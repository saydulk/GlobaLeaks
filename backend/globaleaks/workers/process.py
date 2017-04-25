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
from globaleaks.models.config import tx_load_tls_dict
from globaleaks.utils import tls
from globaleaks.utils.utility import log, randint
from globaleaks.utils.sock import unix_sock_path


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

        f = os.fdopen(fd, 'r')

        try:
            s = f.read()
        except:
            raise
        finally:
            f.close()

        self.cfg = json.loads(s)

    def start(self):
        reactor.run()

    def log(self, m):
        if self.cfg.get('debug', True):
            self._log('[%s:%d] %s\n' % (self.name, self.pid, m))


class CfgFDProcProtocol(ProcessProtocol):
    def __init__(self, supervisor, cfg, cfg_fd=42):
        self.supervisor = supervisor
        self.cfg = json.dumps(cfg)
        self.cfg_fd = cfg_fd

        self.fd_map = {0:'r', cfg_fd:'w'}

        self.startup_promise = defer.Deferred()

    def connectionMade(self):
        self.transport.writeToChild(self.cfg_fd, self.cfg)

        self.transport.closeChildFD(self.cfg_fd)

        self.startup_promise.callback(None)

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
        # Clone the config
        cfg = dict(cfg)

        # Pass the unix control sock fd
        cpanel_unix_sock = unix_sock_path()
        cfg['unix_control_sock'] = cpanel_unix_sock
        #cfg['unix_control_sock_fd'] = s.fileno()

        #super(self.__class__, self).__init__(self, supervisor, cfg, cfg_fd)
        # NOTE cannot use super here because old style objs
        CfgFDProcProtocol.__init__(self, supervisor, cfg, cfg_fd)

        for tls_socket_fd in cfg['tls_socket_fds']:
            self.fd_map[tls_socket_fd] = tls_socket_fd

        # TODO use socket.fromfd from twisted.internet.tcp._fromListeningDescriptor
        # to adopt the fd in the subprocess like twisted.internet.posixbase adoptStreamPort
        # With the file descriptor already open, we can drop all perms on it as soon as the
        # the client establishes a connection and change the user to nobody

        self.cc = ControlClient(cpanel_unix_sock)
        self.cc.cfg = cfg

    @inlineCallbacks
    def connectionMade(self):
        CfgFDProcProtocol.connectionMade(self)
        yield self.cc.connect_and_control()

        tenants = yield get_tenant_list()

        for tenant in tenants:
            tls_cfg = yield tx_load_tls_dict(tenant['id'])

            chnv = tls.ChainValidator()
            ok, err = chnv.validate(tls_cfg, must_be_disabled=False)
            if not ok or err is not None:
                log.debug('Skipping https setup for %s because: %s' % (tenant['label'], err))
                continue

            yield self.cc.add_tls_ctx(tls_cfg)

        # TODO drop privileges here


class ControlClient(object):
    def __init__(self, sock_addr):
        self.sock_addr = sock_addr

    def connect_and_control(self):
        clientfactory = pb.PBClientFactory()

        reactor.connectUNIX(self.sock_addr, clientfactory)
        d = clientfactory.getRootObject()
        d.addCallback(self.attach_root)
        #d.addCallback(self.send_shutdown_signal, 60)
        return d

    def attach_root(self, rootObj):
        self.rootObj = rootObj

    def send_msg(self, _):
        d = self.rootObj.callRemote('do_noop', obj)
        d.addCallback(self.get_msg)

    def add_tls_ctx(self, tls_cfg):
        d = self.rootObj.callRemote('add_context', tls_cfg)
        log.debug('Adding certificate for %s' % tls_cfg['commonname'])
        d.addCallback(self.log_msg)

    def log_msg(self, result):
        log.debug('Child responded: %s' % result)

    def send_shutdown_signal(self, _, t):
        log.msg('Asking https server to shutdown')
        self.rootObj.callRemote('shutdown', t)
