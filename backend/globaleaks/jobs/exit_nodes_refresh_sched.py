# -*- coding: UTF-8
# Implement refresh of the list of exit nodes IPs.

from twisted.internet.defer import inlineCallbacks

from globaleaks.jobs.base import GLJob
from globaleaks.utils.agent import get_tor_agent, get_web_agent
from globaleaks.settings import GLSettings

from globaleaks.state import app_state

__all__ = ['ExitNodesRefreshSchedule']


class ExitNodesRefreshSchedule(GLJob):
    name = "Exit Nodes Refresh"
    interval = 3600

    def operation(self):
        # NOTE operation is intended to a be synchronous func. Here it is async
        self._operation()

    def get_agent(self):
        if app_state.memc.anonymize_outgoing_connections:
            return get_tor_agent(GLSettings.socks_host, GLSettings.socks_port)
        else:
            return get_web_agent()

    @inlineCallbacks
    def _operation(self):
        net_agent = self.get_agent()
        yield app_state.tor_exit_set.update(net_agent)
