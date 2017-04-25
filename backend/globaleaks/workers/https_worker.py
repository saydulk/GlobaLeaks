# -*- encoding: utf-8 -*-
import os
import sys

if os.path.dirname(__file__) != '/usr/lib/python2.7/dist-packages/globaleaks/workers':
    sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from twisted.internet import reactor, unix
from twisted.spread import pb

from globaleaks.workers.process import Process
from globaleaks.utils.sock import listen_tls_on_sock
from globaleaks.utils.sni import SNIMap
from globaleaks.utils.tls import TLSServerContextFactory, ChainValidator
from globaleaks.utils.httpsproxy import HTTPStreamFactory

class ControlPanel(pb.Root):
    tls_server = None

    def __init__(self, https_process):
        print('Starting up')
        self.tls_server = https_process

    def remote_do_something(self, st):
        print('printing: ', st)
        return 'Success 200 OK!!'

    def remote_shutdown(self, t):
        print('shutting down in %d' % t)
        reactor.callLater(t, reactor.stop)

    def remote_add_context(self, cfg):
        print('adding tls context')
        ctx = TLSServerContextFactory(cfg['ssl_key'],
                                      cfg['ssl_cert'],
                                      cfg['ssl_intermediate'],
                                      cfg['ssl_dh'])
        #common_name = cfg['hostname']
        common_name = 'gl.localhost'
        self.tls_server.snimap.add_new_context(common_name, ctx)
        print('Finished adding conxtext')
        return 'Success 200 OK!!'


print('starting')
class HTTPSProcess(Process):
    name = 'gl-https-proxy'
    ports = []

    def __init__(self, *args, **kwargs):
        super(HTTPSProcess, self).__init__(*args, **kwargs)
        self.log('unix control sock')

        # Startup control panel listener
        #fd = self.cfg['unix_control_sock_fd']
        path = self.cfg['unix_control_sock']
        cpanel_factory = pb.PBServerFactory(ControlPanel(self))

        self.log('about to listen on unix tmp dir')
        reactor.listenUNIX(path, cpanel_factory)

        proxy_url = 'http://' + self.cfg['proxy_ip'] + ':' + str(self.cfg['proxy_port'])

        # TODO(tid_me) management of TLS contexts must move out of __init__
        http_proxy_factory = HTTPStreamFactory(proxy_url)

        cv = ChainValidator()
        ok, err = cv.validate(self.cfg, must_be_disabled=False)
        if not ok or not err is None:
            raise err
        self.log('chain seems okay %s %s' % (ok, err))

        self.snimap = SNIMap({
           'DEFAULT': TLSServerContextFactory(self.cfg['ssl_key'],
                                              self.cfg['ssl_cert'],
                                              self.cfg['ssl_intermediate'],
                                              self.cfg['ssl_dh']),
        })

        socket_fds = self.cfg['tls_socket_fds']

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
            port.loseConnection()


if __name__ == '__main__':
    HTTPSProcess().start()
