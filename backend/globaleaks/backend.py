# -*- coding: UTF-8
#   backend
#   *******
# Here is the logic for creating a twisted service. In this part of the code we
# do all the necessary high level wiring to make everything work together.
# Specifically we create the cyclone web.Application from the API specification,
# we create a TCPServer for it and setup logging.
# We also set to kill the threadpool (the one used by Storm) when the
# application shuts down.

import os, sys, traceback

from twisted.application import internet, service
from twisted.internet import reactor, defer
from twisted.python import log as txlog, logfile as txlogfile

from globaleaks.db import init_db, sync_clean_untracked_files
from globaleaks.jobs import jobs_list
from globaleaks.jobs.base import GLJobsMonitor
from globaleaks.rest import api
from globaleaks.settings import GLSettings
from globaleaks.onion_services import configure_tor_hs
from globaleaks.utils.utility import log, GLLogObserver
from globaleaks.utils.sock import listen_tcp_on_sock, reserve_port_for_ip
from globaleaks.workers.supervisor import ProcessSupervisor
from globaleaks import orm

from globaleaks.state import app_state

# this import seems unused but it is required in order to load the mocks
import globaleaks.mocks.cyclone_mocks
import globaleaks.mocks.twisted_mocks


def fail_startup(excep):
    log.err("ERROR: Cannot start GlobaLeaks. Please manually examine the exception.")
    if GLSettings.nodaemon and GLSettings.devel_mode:
        print("EXCEPTION: %s" %  traceback.format_exc(excep))
    else:
        log.err("EXCEPTION: %s" %  excep)
    if reactor.running:
        reactor.stop()


def pre_listen_startup():
    mask = 0
    if GLSettings.devel_mode:
        mask = 9000

    GLSettings.http_socks = []
    for port in GLSettings.bind_ports:
        port = port+mask if port < 1024 else port
        http_sock, fail = reserve_port_for_ip(GLSettings.bind_address, port)
        if fail is not None:
            log.err("Could not reserve socket for %s (error: %s)" % (fail[0], fail[1]))
        else:
            GLSettings.http_socks += [http_sock]

    https_sock, fail = reserve_port_for_ip(GLSettings.bind_address, 443+mask)
    if fail is not None:
        log.err("Could not reserve socket for %s (error: %s)" % (fail[0], fail[1]))
    else:
        GLSettings.https_socks = [https_sock]

    GLSettings.fix_file_permissions()
    GLSettings.drop_privileges()
    GLSettings.check_directories()

    if GLSettings.initialize_db:
        init_db()

    sync_clean_untracked_files()

    orm.thread_pool.start()
    # TODO(tid_me) startup create tenant_id
    app_state.sync_refresh()


class GLService(service.Service):
    jobs = []
    jobs_monitor = None

    @defer.inlineCallbacks
    def startService(self):
        try:
            yield self._start()
        except Exception as excep:
            fail_startup(excep)

    @defer.inlineCallbacks
    def _start(self):
        api_factory = api.get_api_factory(app_state)

        yield configure_tor_hs(app_state.root_id, GLSettings.bind_port)

        for sock in GLSettings.http_socks:
            listen_tcp_on_sock(reactor, sock.fileno(), api_factory)

        app_state.process_supervisor = ProcessSupervisor(GLSettings.https_socks,
                                                         '127.0.0.1',
                                                         GLSettings.bind_port)

        yield app_state.process_supervisor.launch_and_configure_workers(app_state) # @_@ design me better

        self.start_jobs()

        print("GlobaLeaks is listening and will respond to the following urls:")
        for ten_state in app_state.tenant_states.values():
            print("- http://%s%s" % (ten_state.memc.https_hostname, GLSettings.api_prefix))


    def start_jobs(self):
        # A temporary shim
        for job in jobs_list:
            j = job()
            app_state.jobs.append(j)
            j.schedule()

        app_state.jobs_monitor = GLJobsMonitor(app_state.jobs)
        app_state.jobs_monitor.schedule()



application = service.Application('GLBackend')

if not GLSettings.nodaemon and GLSettings.logfile:
    name = os.path.basename(GLSettings.logfile)
    directory = os.path.dirname(GLSettings.logfile)

    gl_logfile = txlogfile.LogFile(name, directory,
                                   rotateLength=GLSettings.log_file_size,
                                   maxRotatedFiles=GLSettings.num_log_files)

    application.setComponent(txlog.ILogObserver, GLLogObserver(gl_logfile).emit)

try:
    pre_listen_startup()

    service = GLService()
    service.setServiceParent(application)

except Exception as excep:
    fail_startup(excep)
    # Exit with non-zero exit code to signal systemd/systemV
    sys.exit(55)
