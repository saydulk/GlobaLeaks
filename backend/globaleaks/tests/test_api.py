from globaleaks.tests.helpers import TestGL

class TestAPI(TestGL):
    def test_api_factory(self):
        from globaleaks.rest import api
        from globaleaks.state import AppState
        app_state = AppState()
        api.get_api_factory(app_state)
        # TODO: write some tests againg the API factory
