import os
import socket

from twisted.protocols import tls


def listen_tcp_on_sock(reactor, fd, factory):
    return reactor.adoptStreamPort(fd, socket.AF_INET, factory)


def listen_tls_on_sock(reactor, fd, contextFactory, factory):
    tlsFactory = tls.TLSMemoryBIOFactory(contextFactory, False, factory)
    port = listen_tcp_on_sock(reactor, fd, tlsFactory)
    port._type = 'TLS'
    return port


def open_socket_listen(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setblocking(False)
    s.bind((ip, port))
    s.listen(1024)
    return s


def open_unix_sock(path):
    if os.path.exists(path):
        os.unlink(path)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.setblocking(False)
    s.bind(path)
    return s


def unix_sock_path():
    rand = ''.join(map(hex, map(ord, os.urandom(4))))
    return '/tmp/glsub-uds-' + rand


def drop_uds_perms(path):
    # TODO preferably the user nobody would own the socket so that even the globaleaks
    # user can touch the sockets after they are created.
    #    tup = pwd.getpwnam('nobody')
    #    pid, gid = tup[2], tup[3]
    #    os.chown(path, pid, gid)
    os.chmod(path, 0000)


def reserve_port_for_ip(ip, port):
    try:
        sock = open_socket_listen(ip, port)
        return [sock, None]
    except Exception as err:
        return [None, err]
