#
# Copyright (c) 2016, salesforce.com, inc.
# All rights reserved.
# Licensed under the BSD 3-Clause license.
# For full license text, see LICENSE.txt file in the repo root  or https://opensource.org/licenses/BSD-3-Clause
#

import unittest, json, os

from argusclient import *
from argusclient.client import JsonEncoder, JsonDecoder, check_success

from test_data import *

try:
    import mock      # Python 2
except ImportError:  # Python 3
    from unittest import mock


class MockRequest(object):
    def __init__(self, url):
        self.url = url


class MockResponse(object):
    def __init__(self, json_text, status_code, request=None,url=None):
        self.text = json_text
        self.status_code = status_code
        self.cookies = cookies
        self.request = request
        self.url = url

    def json(self, **kwargs):
        return json.loads(self.text, **kwargs)


def called_endpoints(mockObj):
    return tuple(a[0][0] for a in mockObj.call_args_list)

def expected_endpoints(*args):
    return tuple(os.path.join(endpoint, p) for p in args)

def determineResponse(url, data, params, headers, timeout):
    if 'triggers' in url:
        return MockResponse(json.dumps([trigger_D, trigger_2_D]), 200)
    if 'notifications' in url:
        return MockResponse(json.dumps([notification_D, notification_2_D, notification_3_D]), 200)
    else:
        return MockResponse(json.dumps([alert_D, alert_2_D]), 200)

class TestCheckSuccess(unittest.TestCase):

    def testSuccess(self):
        check_success(MockResponse(json.dumps(dict(status=200)), 200), decCls=JsonDecoder)

    def testFailure(self):
        self.failUnlessRaises(ArgusException, lambda: check_success(MockResponse(json.dumps(dict(status=400)), 200), decCls=JsonDecoder))

    def testError(self):
        self.failUnlessRaises(ArgusException, lambda: check_success(MockResponse("", 500), decCls=JsonDecoder))

    def testUnauthorized(self):
        self.failUnlessRaises(ArgusAuthException, lambda: check_success(MockResponse("", 401), decCls=JsonDecoder))

    def testUnexpectedEndpoint(self):
        self.failUnlessRaises(ArgusObjectNotFoundException, lambda: check_success(MockResponse("HTTP 404 Not Found", 404), decCls=JsonDecoder))


class TestServiceBase(unittest.TestCase):

    def setUp(self):
        self.argus = ArgusServiceClient(userName, password, endpoint=endpoint)
        self.argus.accessToken = "something"


class TestLogin(TestServiceBase):
    def setUp(self):
        super(TestLogin, self).setUp()
        TestLogin.argus = self.argus # For access by mock
        self.argus.accessToken = None

    def testAuthSuccess(self):
        """A straight-forward login with valid username/password"""
        with mock.patch('requests.Session.get', return_value=MockResponse(json.dumps(user_D), 200)) as mockGet:
            with mock.patch('requests.Session.post', return_value=MockResponse('{"refreshToken": "refresh", "accessToken": "access"}', 200)) as mockPost:
                res = self.argus.login()
                self.assertTrue(isinstance(res, User))
                self.assertEquals(res.to_dict(), user_D)
                # Just checking to make sure the post is happening on the right endpoint.
                self.assertEquals((os.path.join(endpoint, "v2/auth/login"),), called_endpoints(mockPost))
                self.assertEquals((os.path.join(endpoint, "users/username/test.user"),), called_endpoints(mockGet))
                self.assertEquals(self.argus.refreshToken, "refresh")
                self.assertEquals(self.argus.accessToken, "access")
                self.argus.logout()
                self.assertEquals(self.argus.refreshToken, None)
                self.assertEquals(self.argus.accessToken, None)

    def testAuthImplicit(self):
        """A straight-forward implicit login with valid username/password"""
        with mock.patch('requests.Session.get', return_value=MockResponse(json.dumps([namespace_D]), 200)) as mockGet:
            with mock.patch('requests.Session.post', return_value=MockResponse('{"refreshToken": "refresh", "accessToken": "access"}', 200)) as mockPost:
                self.argus.namespaces.values()
                self.assertEquals((os.path.join(endpoint, "v2/auth/login"),), called_endpoints(mockPost))
                self.assertEquals((os.path.join(endpoint, "namespace"),), called_endpoints(mockGet))
                self.assertEquals(self.argus.refreshToken, "refresh")
                self.assertEquals(self.argus.accessToken, "access")

    @mock.patch('requests.Session.post', return_value=MockResponse("""{ "status": 401, "message": "Unauthorized" }""", 401, request=MockRequest("v2/auth/login")))
    def testUnauthorized(self, mockPost):
        """A straight-forward login failure with invalid username/password"""
        self.failUnlessRaises(ArgusAuthException, lambda: self.argus.login())

    def testAuthWithDirectRefreshToken(self):
        """Initialize directly with a valid refresh token but no access token or password"""
        self.argus.refreshToken = "refresh"
        self.argus.password = None
        with mock.patch('test_service.TestLogin.argus.conn') as mockConn:
            mockConn.get = mock.Mock(side_effect=[
                MockResponse(json.dumps([namespace_D]), 200),
            ])
            mockConn.post = mock.Mock(side_effect=[
                MockResponse('{"accessToken": "access"}', 200)
            ])
            self.argus.namespaces.values()
            self.assertEquals((os.path.join(endpoint, "namespace"),), called_endpoints(mockConn.get))
            self.assertEquals(1, mockConn.get.call_count)
            self.assertEquals((os.path.join(endpoint, "v2/auth/token/refresh"),), called_endpoints(mockConn.post))
            self.assertEquals(1, mockConn.post.call_count)

    def testAuthWithDirectAccessToken(self):
        """Initialize directly with a valid access token but no password or refresh token to refresh"""
        self.argus.accessToken = "access"
        self.argus.password = None
        with mock.patch('test_service.TestLogin.argus.conn') as mockConn:
            mockConn.get = mock.Mock(return_value=MockResponse(json.dumps([namespace_D]), 200))
            self.argus.namespaces.values()
            self.assertEquals((os.path.join(endpoint, "namespace"),), called_endpoints(mockConn.get))
            self.assertEquals(1, mockConn.get.call_count)

    def testAuthRefreshAccessToken(self):
        """Test ability to refresh access token from refresh token"""
        self.argus.accessToken = "access"
        self.argus.refreshToken = "refresh"
        with mock.patch('test_service.TestLogin.argus.conn') as mockConn:
            mockConn.get = mock.Mock(side_effect=[
                MockResponse("""{ "status": 401, "message": "Unauthorized" }""", 401, request=MockRequest("namespace")),
                MockResponse(json.dumps([namespace_D]), 200)
            ])
            mockConn.post = mock.Mock(return_value=MockResponse('{"accessToken": "access2"}', 200))
            self.argus.namespaces.values()
            self.assertEquals((os.path.join(endpoint, "v2/auth/token/refresh"),), called_endpoints(mockConn.post))
            self.assertEquals(1, mockConn.post.call_count)
            self.assertEquals((os.path.join(endpoint, "namespace"), os.path.join(endpoint, "namespace"),), called_endpoints(mockConn.get))
            self.assertEquals(2, mockConn.get.call_count)
            self.assertEquals(self.argus.refreshToken, "refresh")
            self.assertEquals(self.argus.accessToken, "access2")

    def testAuthRefreshRefreshToken(self):
        """Test ability to refresh refresh token from username/password"""
        self.argus.accessToken = "access"
        self.argus.refreshToken = "refresh"
        with mock.patch('test_service.TestLogin.argus.conn') as mockConn:
            mockConn.get = mock.Mock(side_effect=[
                MockResponse("""{ "status": 401, "message": "Unauthorized" }""", 401, request=MockRequest("namespace")),
                MockResponse(json.dumps([namespace_D]), 200)
            ])
            mockConn.post = mock.Mock(side_effect=[
                MockResponse("""{ "status": 401, "message": "Unauthorized" }""", 401, request=MockRequest("v2/auth/refresh/token")),
                MockResponse('{"refreshToken": "refresh2", "accessToken": "access2"}', 200)
            ])
            self.argus.namespaces.values()
            self.assertEquals((os.path.join(endpoint, "v2/auth/token/refresh"),os.path.join(endpoint, "v2/auth/login"),), called_endpoints(mockConn.post))
            self.assertEquals(2, mockConn.post.call_count)
            self.assertEquals((os.path.join(endpoint, "namespace"), os.path.join(endpoint, "namespace"),), called_endpoints(mockConn.get))
            self.assertEquals(2, mockConn.get.call_count)
            self.assertEquals(self.argus.refreshToken, "refresh2")
            self.assertEquals(self.argus.accessToken, "access2")

    def testInvalidRefreshTokenWithDirectAccessToken(self):
        """Test inability to refresh access token if refresh token is invalid and there is no password"""
        self.argus.accessToken = "access"
        self.argus.password = None
        with mock.patch('test_service.TestLogin.argus.conn') as mockConn:
            mockConn.get = mock.Mock(side_effect=[
                MockResponse(json.dumps([namespace_D]), 200),
                MockResponse("""{ "status": 401, "message": "Unauthorized" }""", 401, request=MockRequest("namespace")),
                MockResponse("""{ "status": 401, "message": "Unauthorized" }""", 401, request=MockRequest("namespace")),
            ])
            self.argus.namespaces.values()
            self.assertEquals((os.path.join(endpoint, "namespace"),), called_endpoints(mockConn.get))
            self.assertEquals(1, mockConn.get.call_count)
            self.argus.namespaces._retrieved_all = False
            self.failUnlessRaises(ArgusAuthException, lambda: self.argus.namespaces.values())
            self.assertEquals((os.path.join(endpoint, "namespace"), os.path.join(endpoint, "namespace"), os.path.join(endpoint, "namespace"),), called_endpoints(mockConn.get))
            self.assertEquals(3, mockConn.get.call_count)

    def testInvalidPasswordWithDirectRefreshToken(self):
        """Test inability to refresh refresh token as there is no password"""
        self.argus.refreshToken = "refresh"
        self.argus.password = None
        with mock.patch('test_service.TestLogin.argus.conn') as mockConn:
            mockConn.get = mock.Mock(side_effect=[
                MockResponse(json.dumps([namespace_D]), 200),
                MockResponse("""{ "status": 401, "message": "Unauthorized" }""", 401, request=MockRequest("namespace")),
            ])
            mockConn.post = mock.Mock(side_effect=[
                MockResponse('{"accessToken": "access"}', 200),
                MockResponse("""{ "status": 401, "message": "Unauthorized" }""", 401, request=MockRequest("namespace")),
            ])
            self.argus.namespaces.values()
            self.assertEquals((os.path.join(endpoint, "namespace"),), called_endpoints(mockConn.get))
            self.assertEquals(1, mockConn.get.call_count)
            self.assertEquals((os.path.join(endpoint, "v2/auth/token/refresh"),), called_endpoints(mockConn.post))
            self.assertEquals(1, mockConn.post.call_count)
            self.argus.namespaces._retrieved_all = False
            self.failUnlessRaises(ArgusAuthException, lambda: self.argus.namespaces.values())
            self.assertEquals((os.path.join(endpoint, "v2/auth/token/refresh"), os.path.join(endpoint, "v2/auth/token/refresh"),), called_endpoints(mockConn.post))
            self.assertEquals(2, mockConn.post.call_count)

    def testExpiredPassword(self):
        """Test inability to refresh tokens due to expired password"""
        with mock.patch('test_service.TestLogin.argus.conn') as mockConn:
            mockConn.get = mock.Mock(side_effect=[
                MockResponse(json.dumps([namespace_D]), 200),
                MockResponse("""{ "status": 401, "message": "Unauthorized" }""", 401, request=MockRequest("namespace")),
            ])
            mockConn.post = mock.Mock(side_effect=[
                MockResponse('{"refreshToken": "refresh", "accessToken": "access"}', 200),
                MockResponse("""{ "status": 401, "message": "Unauthorized" }""", 401, request=MockRequest("namespace")),
                MockResponse("""{ "status": 401, "message": "Unauthorized" }""", 401, request=MockRequest("namespace")),
            ])
            self.argus.namespaces.values()
            self.assertEquals(1, mockConn.get.call_count)
            self.assertEquals(expected_endpoints("namespace"), called_endpoints(mockConn.get))
            self.assertEquals(1, mockConn.post.call_count)
            self.assertEquals(expected_endpoints("v2/auth/login"), called_endpoints(mockConn.post))
            self.argus.namespaces._retrieved_all = False
            self.failUnlessRaises(ArgusAuthException, lambda: self.argus.namespaces.values())
            self.assertEquals(2, mockConn.get.call_count)
            self.assertEquals(expected_endpoints("namespace", "namespace"), called_endpoints(mockConn.get))
            self.assertEquals(3, mockConn.post.call_count)
            self.assertEquals(expected_endpoints("v2/auth/login", "v2/auth/token/refresh", "v2/auth/login"), called_endpoints(mockConn.post))

class TestMetrics(TestServiceBase):
    def testAddInvalidMetrics(self):
        self.failUnlessRaises(TypeError, lambda: self.argus.metrics.add(Metric.from_dict(metric_D)))
        self.failUnlessRaises(TypeError, lambda: self.argus.metrics.add([dict()]))
        self.failUnlessRaises(ValueError, lambda: self.argus.metrics.add([]))

    @mock.patch('requests.Session.post', return_value=MockResponse(json.dumps(addmetricresult_D), 200))
    def testAddMetrics(self, mockPost):
        res = self.argus.metrics.add([Metric.from_dict(metric_D)])
        self.assertTrue(isinstance(res, AddListResult))
        self.assertIn((os.path.join(endpoint, "collection/metrics"),), tuple(mockPost.call_args))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps([metric_D]), 200))
    def testGetMetrics(self, mockGet):
        res = self.argus.metrics.query(MetricQuery(scope, metric, aggregator, stTimeSpec="-1d"))
        self.assertTrue(isinstance(res, list))
        self.assertEquals(len(res), 1)
        self.assertTrue(isinstance(res[0], Metric))
        self.assertEquals(res[0].to_dict(), metric_D)
        self.assertIn((os.path.join(endpoint, "metrics"),), tuple(mockGet.call_args))


class TestAnnotations(TestServiceBase):
    def testAddInvalidAnnotations(self):
        self.failUnlessRaises(TypeError, lambda: self.argus.annotations.add(Annotation.from_dict(annotation_D)))
        self.failUnlessRaises(TypeError, lambda: self.argus.annotations.add([dict()]))
        self.failUnlessRaises(ValueError, lambda: self.argus.annotations.add([]))

    @mock.patch('requests.Session.post', return_value=MockResponse(json.dumps(addannotationresult_D), 200))
    def testAddAnnotations(self, mockPost):
        res = self.argus.annotations.add([Annotation.from_dict(annotation_D)])
        self.assertTrue(isinstance(res, AddListResult))
        self.assertIn((os.path.join(endpoint, "collection/annotations"),), tuple(mockPost.call_args))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps([annotation_D]), 200))
    def testGetAnnotations(self, mockGet):
        res = self.argus.annotations.query(AnnotationQuery(scope, metric, source, stTimeSpec="-1d"))
        self.assertTrue(isinstance(res, list))
        self.assertEquals(len(res), 1)
        self.assertTrue(isinstance(res[0], Annotation))
        self.assertEquals(res[0].to_dict(), annotation_D)
        self.assertIn((os.path.join(endpoint, "annotations"),), tuple(mockGet.call_args))


class TestUser(TestServiceBase):
    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps(user_D), 200))
    def testGetUserById(self, mockGet):
        res = self.argus.users.get(testId)
        self.assertTrue(isinstance(res, User))
        self.assertEquals(res.to_dict(), user_D)
        self.assertIn((os.path.join(endpoint, "users/id", str(testId)),), tuple(mockGet.call_args))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps(user_D), 200))
    def testGetUserByUsername(self, mockGet):
        res = self.argus.users.get(userName)
        self.assertTrue(isinstance(res, User))
        self.assertEquals(res.to_dict(), user_D)
        self.assertIn((os.path.join(endpoint, "users/username", userName),), tuple(mockGet.call_args))


class TestDashboard(TestServiceBase):
    def testAddInvalidDashboard(self):
        self.failUnlessRaises(TypeError, lambda: self.argus.dashboards.add(dict()))
        self.failUnlessRaises(ValueError, lambda: self.argus.dashboards.add(Dashboard.from_dict(dashboard_D)))

    def testGetDashboardNoId(self):
        self.failUnlessRaises(ValueError, lambda: self.argus.dashboards.get(None))

    @mock.patch('requests.Session.post', return_value=MockResponse(json.dumps(dashboard_D), 200))
    def testAddDashboard(self, mockPost):
        dashboard = Dashboard.from_dict(dashboard_D)
        delattr(dashboard, "id")
        res = self.argus.dashboards.add(dashboard)
        self.assertTrue(isinstance(res, Dashboard))
        self.assertTrue(hasattr(res, "id"))
        self.assertIn((os.path.join(endpoint, "dashboards"),), tuple(mockPost.call_args))

    @mock.patch('requests.Session.put', return_value=MockResponse(json.dumps(dashboard_D), 200))
    def testUpdateDashboard(self, mockPut):
        self.argus.dashboards.update(testId, Dashboard.from_dict(dashboard_D))
        self.assertTrue(isinstance(self.argus.dashboards.get(testId), Dashboard))
        self.assertEquals(self.argus.dashboards.get(testId).to_dict(), dashboard_D)
        self.assertIn((os.path.join(endpoint, "dashboards", str(testId)),), tuple(mockPut.call_args))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps(dashboard_D), 200))
    def testGetDashboard(self, mockGet):
        res = self.argus.dashboards.get(testId)
        self.assertTrue(isinstance(res, Dashboard))
        self.assertEquals(res.to_dict(), dashboard_D)
        self.assertIn((os.path.join(endpoint, "dashboards", str(testId)),), tuple(mockGet.call_args))

    @mock.patch('requests.Session.delete', return_value=MockResponse("", 200))
    def testDeleteDashboard(self, mockDelete):
        self.argus.dashboards.delete(testId)
        self.assertIn((os.path.join(endpoint, "dashboards", str(testId)),), tuple(mockDelete.call_args))

    @mock.patch('requests.Session.get', return_value=MockResponse("[]", 200))
    def testGetUserDashboardNonExisting(self, mockGet):
        res = self.argus.dashboards.get_user_dashboard(userName, dashboardName)
        self.assertTrue(res is None)

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps([dashboard_D]), 200))
    def testGetUserDashboard(self, mockGet):
        res = self.argus.dashboards.get_user_dashboard(userName, dashboardName)
        self.assertTrue(res is not None)
        self.assertEquals(res.to_dict(), dashboard_D)
        self.assertIn((os.path.join(endpoint, "dashboards"),), tuple(mockGet.call_args))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps([dashboard_D, dashboard_D]), 200))
    def testGetUserDashboardMultipleUnexpected(self, mockGet):
        self.failUnlessRaises(AssertionError, lambda: self.argus.dashboards.get_user_dashboard(userName, dashboardName))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps([dashboard_D, dashboard_D]), 200))
    def testGetUserDashboards(self, mockGet):
        res = self.argus.dashboards.get_user_dashboards(userName)
        self.assertTrue(res is not None)
        for obj in res:
            self.assertTrue(isinstance(obj, Dashboard))
            self.assertEquals(obj.to_dict(), dashboard_D)
        self.assertIn((os.path.join(endpoint, "dashboards"),), tuple(mockGet.call_args))

class TestNamespace(TestServiceBase):
    def testAddInvalidNamespace(self):
        self.failUnlessRaises(TypeError, lambda: self.argus.namespaces.add(dict()))
        self.failUnlessRaises(ValueError, lambda: self.argus.namespaces.add(Namespace.from_dict(namespace_D)))

    @mock.patch('requests.Session.post', return_value=MockResponse(json.dumps(namespace_D), 200))
    def testAddNamespace(self, mockPost):
        namespace = Namespace.from_dict(namespace_D)
        delattr(namespace, "id")
        res = self.argus.namespaces.add(namespace)
        self.assertTrue(isinstance(res, Namespace))
        self.assertTrue(hasattr(res, "id"))
        self.assertIn((os.path.join(endpoint, "namespace"),), tuple(mockPost.call_args))

    @mock.patch('requests.Session.put', return_value=MockResponse(json.dumps(namespace_D), 200))
    def testUpdateNamespace(self, mockPut):
        self.argus.namespaces.update(testId, Namespace.from_dict(namespace_D))
        self.assertTrue(isinstance(self.argus.namespaces.get(testId), Namespace))
        self.assertEquals(self.argus.namespaces.get(testId).to_dict(), namespace_D)
        self.assertIn((os.path.join(endpoint, "namespace", str(testId)),), tuple(mockPut.call_args))

    @mock.patch('requests.Session.put', return_value=MockResponse(json.dumps(namespace_D), 200))
    def testUpdateNamespaceUsers(self, mockPut):
        res = self.argus.namespaces.update_users(testId, userName)
        self.assertTrue(isinstance(res, Namespace))
        self.assertEquals(res.to_dict(), namespace_D)
        self.assertIn((os.path.join(endpoint, "namespace", str(testId), "users"),), tuple(mockPut.call_args))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps([namespace_D]), 200))
    def testGetNamespaces(self, mockGet):
        res = self.argus.namespaces.values()
        self.assertTrue(isinstance(res, list))
        self.assertEquals(len(res), 1)
        self.assertTrue(isinstance(res[0], Namespace))
        self.assertEquals(res[0].to_dict(), namespace_D)
        self.assertIn((os.path.join(endpoint, "namespace"),), tuple(mockGet.call_args))


class TestAlert(TestServiceBase):
    def testAddInvalidAlert(self):
        self.failUnlessRaises(TypeError, lambda: self.argus.alerts.add(dict()))
        self.failUnlessRaises(ValueError, lambda: self.argus.alerts.add(Alert.from_dict(alert_D)))

    @mock.patch('requests.Session.post', return_value=MockResponse(json.dumps(alert_D), 200))
    def testAddAlert(self, mockPost):
        alert = Alert.from_dict(alert_D)
        delattr(alert, "id")
        res = self.argus.alerts.add(alert)
        self.assertTrue(isinstance(res, Alert))
        self.assertTrue(hasattr(res, "id"))
        for method in ['get', 'add', 'update', 'delete']:
            self.assertTrue(hasattr(res.triggers, method), msg='no alert.triggers.{}()'.format(method))
            self.assertTrue(hasattr(res.notifications, method), msg='no alert.notifications.{}()'.format(method))

    @mock.patch('requests.Session.put', return_value=MockResponse(json.dumps(alert_D), 200))
    def testUpdateAlert(self, mockPut):
        res = self.argus.alerts.update(testId, Alert.from_dict(alert_D))
        self.assertTrue(isinstance(self.argus.alerts.get(testId), Alert))
        self.assertEquals(self.argus.alerts.get(testId).to_dict(), alert_D)
        self.assertIn((os.path.join(endpoint, "alerts", str(testId)),), tuple(mockPut.call_args))
        for method in ['get', 'add', 'update', 'delete']:
            self.assertTrue(hasattr(res.triggers, method), msg='no alert.triggers.{}()'.format(method))
            self.assertTrue(hasattr(res.notifications, method), msg='no alert.notifications.{}()'.format(method))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps([alert_D]), 200))
    def testGetAlerts(self, mockGet):
        res = self.argus.alerts.values()
        self.assertTrue(isinstance(res, list))
        self.assertEquals(len(res), 1)
        self.assertTrue(isinstance(res[0], Alert))
        self.assertEquals(res[0].to_dict(), alert_D)
        self.assertIn((os.path.join(endpoint, "alerts"),), tuple(mockGet.call_args))
        for method in ['get', 'add', 'update', 'delete']:
            self.assertTrue(hasattr(res[0].triggers, method), msg='no alert.triggers.{}()'.format(method))
            self.assertTrue(hasattr(res[0].notifications, method), msg='no alert.notifications.{}()'.format(method))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps(alert_D), 200))
    def testGetAlert(self, mockGet):
        res = self.argus.alerts.get(testId)
        self.assertTrue(isinstance(res, Alert))
        self.assertEquals(res.to_dict(), alert_D)
        self.assertIn((os.path.join(endpoint, "alerts", str(testId)),), tuple(mockGet.call_args))
        for method in ['get', 'add', 'update', 'delete']:
            self.assertTrue(hasattr(res.triggers, method), msg='no alert.triggers.{}()'.format(method))
            self.assertTrue(hasattr(res.notifications, method), msg='no alert.notifications.{}()'.format(method))

    @mock.patch('requests.Session.delete', return_value=MockResponse("", 200))
    def testDeleteAlert(self, mockDelete):
        self.argus.alerts.delete(testId)
        self.assertIn((os.path.join(endpoint, "alerts", str(testId)),), tuple(mockDelete.call_args))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps([alert_D]), 200))
    def testGetUserAlert(self, mockGet):
        res = self.argus.alerts.get_user_alert(testId, testId)
        self.assertTrue(isinstance(res, Alert))
        self.assertEquals(res.to_dict(), alert_D)
        self.assertIn((os.path.join(endpoint, "alerts/meta"),), tuple(mockGet.call_args))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps([]), 200))
    def testGetUserAlertNoMatch(self, mockGet):
        res = self.argus.alerts.get_user_alert(testId, testId)
        self.assertEquals(res, None)
        self.assertIn((os.path.join(endpoint, "alerts/meta"),), tuple(mockGet.call_args))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps([alert_D, alert_D]), 200))
    def testGetUserAlertUnexpectedMultiple(self, mockGet):
        self.failUnlessRaises(AssertionError, lambda: self.argus.alerts.get_user_alert(testId, testId))
        self.assertIn((os.path.join(endpoint, "alerts/meta"),), tuple(mockGet.call_args))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps([alert_D, alert_D]), 200))
    def testGetAlertsAllInfo(self, mockGet):
        res = self.argus.alerts.get_alerts_allinfo(userName)
        if res:
            for obj in res:
                self.assertTrue(isinstance(obj, Alert))
        self.assertIn((os.path.join(endpoint, "alerts/allinfo"),), tuple(mockGet.call_args))

    # Test items() where get_all_path is the allinfo one
    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps([alert_all_info_D, alert_all_info_2_D]), 200))
    def testGetItemsAllInfo(self, mockGet):
        self.assertEquals(len(mockGet.call_args_list), 0)
        alertClient = self.argus.alerts
        alertClient.set_get_all_path("alerts/allinfo")
        alertClient.set_get_all_path_params(dict(shared=False))

        # Act
        res = alertClient.items()
        # Assert
        self.assertEquals(len(mockGet.call_args_list), 1)
        self.assertIn((os.path.join(endpoint, "alerts/allinfo"),), tuple(mockGet.call_args))
        self.assertEquals(len(res), 2)

        for element in res:
            # Assert
            self.assertTrue(isinstance(element[1], Alert))
            alert = element[1]

            # Act
            items = alert.triggers.items()
            # Assert
            self.assertEquals(len(items), 2)
            for item in items:
                self.assertTrue(isinstance(item[1], Trigger))

            # Act
            items = alert.notifications.items()
            # Assert
            self.assertEquals(len(items), 3)
            for item in items:
                self.assertTrue(isinstance(item[1], Notification))

        self.assertEquals(len(mockGet.call_args_list), 1)

    # Test items() where get_all_path is default
    @mock.patch('requests.Session.get', side_effect=determineResponse)
    def testGetItems(self, mockGet):
        self.assertEquals(len(mockGet.call_args_list), 0)
        alertClient = self.argus.alerts

        # Act
        res = alertClient.items()
        # Assert
        self.assertEquals(len(res), 2)
        self.assertIn((os.path.join(endpoint, "alerts"),), tuple(mockGet.call_args))
        self.assertEquals(len(mockGet.call_args_list), 1)

        for element in res:
            # Assert
            self.assertTrue(isinstance(element[1], Alert))
            alert = element[1]

            # Act
            items = alert.triggers.items()
            # Assert
            self.assertEquals(len(items), 2)
            self.assertIn("triggers", mockGet.call_args[0][0])
            for item in items:
                self.assertTrue(isinstance(item[1], Trigger))

            # Act
            items = alert.notifications.items()
            # Assert
            self.assertEquals(len(items), 3)
            self.assertIn("notifications", mockGet.call_args[0][0])
            for item in items:
                self.assertTrue(isinstance(item[1], Notification))

        self.assertEquals(len(mockGet.call_args_list), 5)

class TestAlertTrigger(TestServiceBase):
    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps(alert_D), 200))
    def setUp(self, mockGet):
        super(TestAlertTrigger, self).setUp()
        self.alert = self.argus.alerts.get(testId)

    def testAddInvalidTrigger(self):
        self.failUnlessRaises(TypeError, lambda: self.alert.triggers.add(dict()))
        self.failUnlessRaises(ValueError, lambda: self.alert.triggers.add(Trigger.from_dict(trigger_D)))

    @mock.patch('requests.Session.post', return_value=MockResponse(json.dumps([trigger_D]), 200))
    def testAddTrigger(self, mockPost):
        trigger = Trigger.from_dict(trigger_D)
        delattr(trigger, "id")
        res = self.alert.triggers.add(trigger)
        self.assertTrue(isinstance(res, Trigger))
        self.assertTrue(hasattr(res, "id"))
        self.assertIn((os.path.join(endpoint, "alerts", str(testId), "triggers"),), tuple(mockPost.call_args))
        self.assertEquals(self.alert.triggers[testId].argus_id, testId)

    @mock.patch('requests.Session.put', return_value=MockResponse(json.dumps(trigger_D), 200))
    def testUpdateTrigger(self, mockPut):
        self.alert.triggers.update(testId, Trigger.from_dict(trigger_D))
        self.assertTrue(isinstance(self.alert.triggers.get(testId), Trigger))
        self.assertEquals(self.alert.triggers.get(testId).to_dict(), trigger_D)
        self.assertIn((os.path.join(endpoint, "alerts", str(testId), "triggers", str(testId)),), tuple(mockPut.call_args))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps([trigger_D]), 200))
    def testGetTriggers(self, mockGet):
        res = self.alert.triggers.values()
        self.assertTrue(isinstance(res, list))
        self.assertEquals(len(res), 1)
        self.assertTrue(isinstance(res[0], Trigger))
        self.assertEquals(res[0].to_dict(), trigger_D)
        self.assertIn((os.path.join(endpoint, "alerts", str(testId), "triggers"),), tuple(mockGet.call_args))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps(trigger_D), 200))
    def testGetTrigger(self, mockGet):
        res = self.alert.triggers.get(testId)
        self.assertTrue(isinstance(res, Trigger))
        self.assertEquals(res.to_dict(), trigger_D)
        self.assertIn((os.path.join(endpoint, "alerts", str(testId), "triggers", str(testId)),), tuple(mockGet.call_args))

    @mock.patch('requests.Session.delete', return_value=MockResponse("", 200))
    def testDeleteTrigger(self, mockDelete):
        with mock.patch('requests.Session.post', return_value=MockResponse(json.dumps([trigger_D]), 200)):
            trigger = Trigger.from_dict(trigger_D)
            delattr(trigger, "id")
            self.alert.triggers.add(trigger)
        self.alert.triggers.delete(testId)
        self.assertIn((os.path.join(endpoint, "alerts", str(testId), "triggers", str(testId)),), tuple(mockDelete.call_args))
        # With delete removing the entry from alert.triggers, the following lookup would result in
        # a fresh get call.
        with mock.patch('requests.Session.get', return_value=MockResponse("", 404)) as mockGet:
            self.failUnlessRaises(ArgusObjectNotFoundException, lambda: self.alert.triggers[testId])
            self.assertIn((os.path.join(endpoint, "alerts", str(testId), "triggers", str(testId)),), tuple(mockGet.call_args))


class TestAlertNotification(TestServiceBase):
    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps(alert_D), 200))
    def setUp(self, mockGet):
        super(TestAlertNotification, self).setUp()
        self.alert = self.argus.alerts.get(testId)

    def testAddInvalidNotification(self):
        self.failUnlessRaises(TypeError, lambda: self.alert.notifications.add(dict()))
        self.failUnlessRaises(ValueError, lambda: self.alert.notifications.add(Notification.from_dict(notification_D)))

    @mock.patch('requests.Session.post', return_value=MockResponse(json.dumps([notification_D]), 200))
    def testAddNotification(self, mockPost):
        notification = Notification.from_dict(notification_D)
        delattr(notification, "id")
        res = self.alert.notifications.add(notification)
        self.assertTrue(isinstance(res, Notification))
        self.assertTrue(hasattr(res, "id"))
        self.assertIn((os.path.join(endpoint, "alerts", str(testId), "notifications"),), tuple(mockPost.call_args))
        self.assertEquals(self.alert.notifications[testId].argus_id, testId)

    @mock.patch('requests.Session.put', return_value=MockResponse(json.dumps(notification_D), 200))
    def testUpdateNotification(self, mockPut):
        self.alert.notifications.update(testId, Notification.from_dict(notification_D))
        self.assertTrue(isinstance(self.alert.notifications.get(testId), Notification))
        self.assertEquals(self.alert.notifications.get(testId).to_dict(), notification_D)
        self.assertIn((os.path.join(endpoint, "alerts", str(testId), "notifications", str(testId)),), tuple(mockPut.call_args))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps([notification_D]), 200))
    def testGetNotifications(self, mockGet):
        res = self.alert.notifications.values()
        self.assertTrue(isinstance(res, list))
        self.assertEquals(len(res), 1)
        self.assertTrue(isinstance(res[0], Notification))
        self.assertEquals(res[0].to_dict(), notification_D)
        self.assertIn((os.path.join(endpoint, "alerts", str(testId), "notifications"),), tuple(mockGet.call_args))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps(notification_D), 200))
    def testGetNotification(self, mockGet):
        res = self.alert.notifications.get(testId)
        self.assertTrue(isinstance(res, Notification))
        self.assertEquals(res.to_dict(), notification_D)
        self.assertIn((os.path.join(endpoint, "alerts", str(testId), "notifications", str(testId)),), tuple(mockGet.call_args))

    @mock.patch('requests.Session.delete', return_value=MockResponse("", 200))
    def testDeleteNotification(self, mockDelete):
        with mock.patch('requests.Session.post', return_value=MockResponse(json.dumps([notification_D]), 200)):
            notification = Notification.from_dict(notification_D)
            delattr(notification, "id")
            self.alert.notifications.add(notification)
        self.alert.notifications.delete(testId)
        self.assertIn((os.path.join(endpoint, "alerts", str(testId), "notifications", str(testId)),), tuple(mockDelete.call_args))
        # With delete removing the entry from alert.notifications, the following lookup would result in
        # a fresh get call.
        with mock.patch('requests.Session.get', return_value=MockResponse("", 404)) as mockGet:
            self.failUnlessRaises(ArgusObjectNotFoundException, lambda: self.alert.notifications[testId])
            self.assertIn((os.path.join(endpoint, "alerts", str(testId), "notifications", str(testId)),), tuple(mockGet.call_args))


class TestNotificationTrigger(TestServiceBase):
    def testAddInvalidNotificationTrigger(self):
        self.failUnlessRaises(ValueError, lambda: self.argus.alerts.add_notification_trigger(None, testId, testId))
        self.failUnlessRaises(ValueError, lambda: self.argus.alerts.add_notification_trigger(testId, None, testId))
        self.failUnlessRaises(ValueError, lambda: self.argus.alerts.add_notification_trigger(testId, testId, None))

    @mock.patch('requests.Session.post', return_value=MockResponse(json.dumps(trigger_D), 200))
    def testAddNotificationTrigger(self, mockPost):
        res = self.argus.alerts.add_notification_trigger(testId, testId, testId)
        self.assertTrue(isinstance(res, Trigger))
        self.assertIn((os.path.join(endpoint, "alerts", str(testId), "notifications", str(testId), "triggers", str(testId)),), tuple(mockPost.call_args))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps([trigger_D]), 200))
    def testGetNotificationTriggers(self, mockGet):
        res = self.argus.alerts.get_notification_triggers(testId, testId)
        self.assertTrue(isinstance(res, list))
        self.assertEquals(len(res), 1)
        self.assertTrue(isinstance(res[0], Trigger))
        self.assertEquals(res[0].to_dict(), trigger_D)
        self.assertIn((os.path.join(endpoint, "alerts", str(testId), "notifications", str(testId), "triggers"),), tuple(mockGet.call_args))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps(trigger_D), 200))
    def testGetNotificationTrigger(self, mockGet):
        res = self.argus.alerts.get_notification_trigger(testId, testId, testId)
        self.assertTrue(isinstance(res, Trigger))
        self.assertEquals(res.to_dict(), trigger_D)
        self.assertIn((os.path.join(endpoint, "alerts", str(testId), "notifications", str(testId), "triggers", str(testId)),), tuple(mockGet.call_args))

    @mock.patch('requests.Session.delete', return_value=MockResponse("", 200))
    def testDeleteNotificationTrigger(self, mockDelete):
        self.argus.alerts.delete_notification_trigger(testId, testId, testId)
        self.assertIn((os.path.join(endpoint, "alerts", str(testId), "notifications", str(testId), "triggers", str(testId)),), tuple(mockDelete.call_args))


class TestAlertMultipleNotifications(TestServiceBase):

    def setUp(self):
        super(TestAlertMultipleNotifications, self).setUp()
        self.alert_dict = dict(alert_D)
        self.notif1_dict = dict(notification_D)
        self.notif2_dict = dict(notification_D)
        self.notif1_dict["id"] = 100
        self.notif2_dict["id"] = 101
        self.alert_dict["notificationIds"] = [100, 101]

    def testGetAlertWithMultipleNotifications(self):
        with mock.patch('requests.Session.get', return_value=MockResponse(json.dumps(self.alert_dict), 200)):
            return self.argus.alerts.get(testId)
        alert = get_alert()
        self.assertEquals(alert.notificationIds, [100, 101])

        with mock.patch('requests.Session.get', return_value=MockResponse(json.dumps([self.notif1_dict, self.notif2_dict]), 200)):
            self.assertEquals(len(alert.notifications), 2)
        self.assertEquals(alert.notifications[100].argus_id, 100)
        self.assertEquals(alert.notifications[101].argus_id, 101)


class TestAlertMultipleTriggers(TestServiceBase):

    def setUp(self):
        super(TestAlertMultipleTriggers, self).setUp()
        self.alert_dict = dict(alert_D)
        self.trigr1_dict = dict(trigger_D)
        self.trigr2_dict = dict(trigger_D)
        self.trigr1_dict["id"] = 100
        self.trigr2_dict["id"] = 101
        self.alert_dict["triggerIds"] = [100, 101]

    def testGetAlertWithMultipleTriggers(self):
        with mock.patch('requests.Session.get', return_value=MockResponse(json.dumps(self.alert_dict), 200)):
            return self.argus.alerts.get(testId)
        alert = get_alert()
        self.assertEquals(alert.triggerIds, [100, 101])

        with mock.patch('requests.Session.get', return_value=MockResponse(json.dumps([self.trigr1_dict, self.trigr2_dict]), 200)):
            self.assertEquals(len(alert.triggers), 2)
        self.assertEquals(alert.triggers[100].argus_id, 100)
        self.assertEquals(alert.triggers[101].argus_id, 101)
