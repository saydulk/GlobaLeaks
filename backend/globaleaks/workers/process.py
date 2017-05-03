# -*- encoding: utf-8 -*-
import ctypes
import json
import os
import signal
import sys
import traceback

from twisted.internet import defer, reactor
from twisted.internet.defer import inlineCallbacks
from twisted.internet.protocol import ProcessProtocol
from twisted.spread import pb

from globaleaks.handlers.admin.tenant import get_tenant_list
from globaleaks.utils import tls, sock
from globaleaks.utils.tls import tx_load_tls_dict
from globaleaks.utils.utility import log, randint


def SigQUIT(SIG, FRM):
    try:
        if reactor.running:
            reactor.stop()
        else:
            sys.exit(0)
    except Exception:
        pass


def set_proctitle(title):
    libc = ctypes.cdll.LoadLibrary('libc.so.6')
    buff = ctypes.create_string_buffer(len(title) + 1)
    buff.value = title
    libc.prctl(15, ctypes.byref(buff), 0, 0, 0)


def set_pdeathsig(sig):
    PR_SET_PDEATHSIG = 1
    libc = ctypes.cdll.LoadLibrary('libc.so.6')
    libc.prctl.argtypes = (ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                           ctypes.c_ulong, ctypes.c_ulong)
    libc.prctl(PR_SET_PDEATHSIG, sig, 0, 0, 0)
    # If the parent has already died, kill this process.
    if os.getppid() == 1:
        os.kill(os.getpid(), sig)


class Process(object):
    cfg = {}
    name = ''

    def __init__(self, fd=42):
        self.pid = os.getpid()

        signal.signal(signal.SIGTERM, SigQUIT)
        signal.signal(signal.SIGINT, SigQUIT)
        set_proctitle(self.name)
        set_pdeathsig(signal.SIGINT)

        self._log = os.fdopen(0, 'w', 1).write

        def excepthook(*exc_info):
            self.log("".join(traceback.format_exception(*exc_info)))

        sys.excepthook = excepthook

    def start(self):
        reactor.run()

    def log(self, m):
        if self.cfg.get('debug', True):
            self._log('[%s:%d] %s\n' % (self.name, self.pid, m))


class CfgFDProcProtocol(ProcessProtocol):
    def __init__(self, supervisor, cfg, cfg_fd=42):
        self.supervisor = supervisor
        self.cfg = cfg
        self.cfg_fd = cfg_fd

        self.fd_map = {0:'r', cfg_fd:'r'}

        self.startup_promise = defer.Deferred()

    def childDataReceived(self, childFD, data):
        for line in data.split('\n'):
            if line != '':
                log.debug(line)

    def processEnded(self, reason):
        self.supervisor.handle_worker_death(self, reason)

    def __repr__(self):
        return "<%s: %s:%s>" % (self.__class__.__name__, id(self), self.transport)


class HTTPSProcProtocol(CfgFDProcProtocol):
    def __init__(self, supervisor, cfg, cfg_fd=42):
        self.cc = None

        # Clone the config
        cfg = dict(cfg)

        s_path = sock.unix_sock_path()
        log.debug('Reserved unix sock: %s' % s_path)
        cfg['unix_control_sock'] = s_path

        # NOTE cannot use super here because old style objs
        CfgFDProcProtocol.__init__(self, supervisor, cfg, cfg_fd)

        for tls_socket_fd in cfg['tls_socket_fds']:
            self.fd_map[tls_socket_fd] = tls_socket_fd

        # TODO attach a timing out callback that kills the child after a set period
        # if the startup_promise is not called

    def childConnectionLost(self, childFD):
        CfgFDProcProtocol.childConnectionLost(self, childFD)
        # Ensure that this logic is only ever called once.
        if childFD == self.cfg_fd and not self.startup_promise.called:
            log.debug('Subprocess[%d] signaled the pub broker is active' % self.transport.pid)
            self.cc = ControlClient(self.cfg)
            # TODO With the file descriptor already open, we can drop all perms
            # on it as soon as the the client establishes a connection and
            # change the user to nobody
            self.cc.startup_promise.addCallback(self.startup_promise.callback)


class ControlClient(object):
    def __init__(self, cfg):
        clientfactory = pb.PBClientFactory()
        u_sock = cfg['unix_control_sock']
        log.debug('Attempting connection to %s' % u_sock)
        reactor.connectUNIX(u_sock, clientfactory)
        log.debug('Socket connected')
        self.startup_promise = clientfactory.getRootObject()
        self.startup_promise.addCallback(self.attach_root, u_sock)
        self.startup_promise.addCallback(self.launch_server, cfg)
        self.startup_promise.addErrback(self.failedStartup)

    def failedStartup(self, *args):
        log.err('PB startup failed with %s' % args)

    def attach_root(self, rootObj, u_sock):
        self.rootObj = rootObj
        log.debug('Dropping perms on socket %s' % u_sock)
        sock.drop_uds_perms(u_sock)

    def launch_server(self, _, cfg):
        log.debug('Calling remote subprocess startup')
        d = self.rootObj.callRemote('startup', cfg)
        d.addCallback(self.log_msg)
        return d

    def set_context(self, tls_cfg):
        log.debug('Adding certificate for tenant:<%s>:%s' % \
                  (tls_cfg['tenant_id'], tls_cfg['commonname']))
        d = self.rootObj.callRemote('set_context', tls_cfg)
        d.addCallback(self.log_msg)

    def del_context(self, tenant_id):
        log.debug('Removing tls context for tenant:%d' % tenant_id)
        d = self.rootObj.callRemote('del_context', tenant_id)
        d.addCallback(self.log_msg)

    def log_msg(self, result):
        log.debug('Child responded: %s' % result)
