import re

from twisted.internet.address import IPv4Address
from twisted.internet.defer import inlineCallbacks
from twisted.web.test.requesthelper import DummyRequest

from globaleaks.settings import GLSettings
from globaleaks.tests.helpers import TestGL


def forgeRequest(headers):
    ret = DummyRequest([''])
    ret.client = IPv4Address('TCP', '1.2.3.4', 12345)

    for k, v in headers.iteritems():
        ret.requestHeaders.setRawHeaders(bytes(k), [bytes(v)])

    ret.headers = ret.getAllHeaders()

    return ret


def getAPI():
    from globaleaks.rest import api
    ret = api.APIResourceWrapper()

    return ret


class TestAPI(TestGL):
    def test_api_spec(self):
        from globaleaks.rest import api
        for spec in api.api_spec:
            check_roles = getattr(spec[1], 'check_roles')
            self.assertIsNotNone(check_roles)

            if type(check_roles) == str:
                check_roles = {check_roles}

            self.assertTrue(len(check_roles) >= 1)
            self.assertTrue('*' not in check_roles or len(check_roles) == 1)
            self.assertTrue('unauthenticated' not in check_roles or len(check_roles) == 1)
            self.assertTrue('*' not in check_roles or len(check_roles) == 1)

            rest = filter(lambda a: a not in ['*',
                                              'unauthenticated',
                                              'whistleblower',
                                              'admin',
                                              'receiver',
                                              'custodian'], check_roles)
            self.assertTrue(len(rest) == 0)

    def test_get_with_no_language_header(self):
        api = getAPI()
        request = forgeRequest({})
        self.assertEqual(api.detect_language(request), 'en')

    def test_get_with_gl_language_header(self):
        api = getAPI()
        request = forgeRequest({'GL-Language': 'it'})
        self.assertEqual(api.detect_language(request), 'it')

    def test_get_with_accept_language_header(self):
        api = getAPI()
        request = forgeRequest({'Accept-Language': 'ar;q=0.8,it;q=0.6'})
        self.assertEqual(api.detect_language(request), 'ar')

    def test_get_with_gl_language_header_and_accept_language_header_1(self):
        api = getAPI()
        request = forgeRequest({'GL-Language': 'en',
                                'Accept-Language': 'en-US,en;q=0.8,it;q=0.6'})
        self.assertEqual(api.detect_language(request), 'en')

    def test_get_with_gl_language_header_and_accept_language_header_2(self):
        api = getAPI()
        request = forgeRequest({'GL-Language': 'antani',
                                'Accept-Language': 'en-US,en;it;q=0.6'})
        self.assertEqual(api.detect_language(request), 'en')

    def test_get_with_gl_language_header_and_accept_language_header_3(self):
        api = getAPI()
        request = forgeRequest({'GL-Language': 'antani',
                                'Accept-Language': 'antani1,antani2;q=0.8,antani3;q=0.6'})
        self.assertEqual(api.detect_language(request), 'en')

    def test_client_using_tor(self):
        api = getAPI()
        request = forgeRequest({})
        api.preprocess(request)
        self.assertFalse(request.client_using_tor)

        GLSettings.state.tor_exit_set.add('1.2.3.4')

        request = forgeRequest({})
        api.preprocess(request)
        self.assertTrue(request.client_using_tor)

        request = forgeRequest({'X-Tor2Web': '1'})
        api.preprocess(request)
        self.assertFalse(request.client_using_tor)

        GLSettings.state.tor_exit_set.clear()
