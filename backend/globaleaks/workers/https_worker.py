# -*- encoding: utf-8 -*-
import os
import sys
import socket

if os.path.dirname(__file__) != '/usr/lib/python2.7/dist-packages/globaleaks/workers':
    sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from twisted.internet import reactor, unix
from twisted.spread import pb

from globaleaks.workers.process import Process
from globaleaks.utils.sock import listen_tls_on_sock
from globaleaks.utils.sni import SNIMap
from globaleaks.utils.tls import TLSServerContextFactory, ChainValidator
from globaleaks.utils.httpsproxy import HTTPStreamFactory
from globaleaks.utils.utility import log

class ControlPanel(pb.Root):
    tls_server = None

    def __init__(self, https_process):
        self.tls_server = https_process

    def remote_startup(self, cfg):
        if self.tls_server.started:
            raise Excpetion('Already started')
        self.tls_server.launch_server(cfg)
        return 0

    def remote_shutdown(self, t):
        reactor.callLater(t, reactor.stop)

    def remote_set_context(self, cfg):
        self.tls_server.log('Setting up SSL config')
        common_name = cfg['commonname']
        self.tls_server.log('Adding TLS context: %s' % common_name)
        ctx = TLSServerContextFactory(cfg['ssl_key'],
                                      cfg['ssl_cert'],
                                      cfg['ssl_intermediate'],
                                      cfg['ssl_dh'])
        self.tls_server.snimap.add_new_context(common_name, ctx)
        self.tls_server.log('Finished adding conxtext, listening with ssl on:')
        self.tls_server.log('https://%s' % common_name)
        return 0

    def remote_del_context(self, t):
        pass


class HTTPSProcess(Process):
    name = 'gl-https-proxy'

    def __init__(self, *args, **kwargs):
        super(HTTPSProcess, self).__init__(*args, **kwargs)

        self.ports = []
        self.started = False

        path = sys.argv[1]
        self.log('Starting up...')

        # Start the control panel listener first
        cpanel_factory = pb.PBServerFactory(ControlPanel(self))
        reactor.listenUNIX(path, cpanel_factory)

        self.log('Listening for pubbroker commands')
        # Use a file descriptor here as a poor man's semaphore
        f = os.fdopen(42, 'w')
        f.close()


    def launch_server(self, default_cfg):
        self.started = True
        self.log('Launching tls server')

        proxy_url = 'http://' + default_cfg['proxy_ip'] + ':' + str(default_cfg['proxy_port'])

        # TODO(tid_me) management of TLS contexts must move out of __init__
        http_proxy_factory = HTTPStreamFactory(proxy_url)

        cv = ChainValidator()
        ok, err = cv.validate(default_cfg, must_be_disabled=False)
        if not ok or not err is None:
            raise err

        self.snimap = SNIMap({
           'DEFAULT': TLSServerContextFactory(default_cfg['ssl_key'],
                                              default_cfg['ssl_cert'],
                                              default_cfg['ssl_intermediate'],
                                              default_cfg['ssl_dh']),
        })

        socket_fds = default_cfg['tls_socket_fds']

        for socket_fd in socket_fds:
            self.log("Opening socket: %d : %s" % (socket_fd, os.fstat(socket_fd)))

            port = listen_tls_on_sock(reactor,
                                      fd=socket_fd,
                                      contextFactory=self.snimap,
                                      factory=http_proxy_factory)

            self.ports.append(port)
            self.log("HTTPS proxy listening on %s" % port)

    def shutdown(self):
        for port in self.ports:
            self.log('Shutting down. . .')
            port.loseConnection()


if __name__ == '__main__':
    HTTPSProcess().start()
