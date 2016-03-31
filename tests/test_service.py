import unittest, mock, json, os

from argusclient import *
from argusclient.client import JsonEncoder, JsonDecoder, check_success

from test_data import *


class MockResponse(object):
    def __init__(self, json_text, status_code):
        self.text = json_text
        self.status_code = status_code
        self.cookies = cookies

    def json(self, **kwargs):
        return json.loads(self.text, **kwargs)


class TestCheckSuccess(unittest.TestCase):

    def testSuccess(self):
        check_success(MockResponse(json.dumps(dict(status=200)), 200), decCls=JsonDecoder)

    def testFailure(self):
        self.failUnlessRaises(ArgusException, lambda: check_success(MockResponse(json.dumps(dict(status=400)), 200), decCls=JsonDecoder))

    def testError(self):
        self.failUnlessRaises(ArgusException, lambda: check_success(MockResponse("", 500), decCls=JsonDecoder))

    def testUnexpectedEndpoint(self):
        self.failUnlessRaises(Exception, lambda: check_success(MockResponse("HTTP 404 Not Found", 404), decCls=JsonDecoder))


class TestServiceBase(unittest.TestCase):

    def setUp(self):
        self.argus = ArgusServiceClient(userName, password, endpoint=endpoint)


class TestLogin(TestServiceBase):

    @mock.patch('requests.Session.post', return_value=MockResponse(json.dumps(user_D), 200))
    def testOnSuccess(self, mockPost):
        res = self.argus.login()
        self.assertTrue(isinstance(res, User))
        self.assertEquals(res.to_dict(), user_D)
        # Just checking to make sure the post is happening on the right endpoint.
        self.assertIn((os.path.join(endpoint, "auth/login"),), tuple(mockPost.call_args))

    @mock.patch('requests.Session.post', return_value=MockResponse("""{ "status": 401, "message": "Unauthorized" }""", 401))
    def testUnauthorized(self, mockPost):
        self.failUnlessRaises(ArgusException, lambda: self.argus.login())


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

    @mock.patch('requests.Session.put', return_value=MockResponse(json.dumps(alert_D), 200))
    def testUpdateAlert(self, mockPut):
        self.argus.alerts.update(testId, Alert.from_dict(alert_D))
        self.assertTrue(isinstance(self.argus.alerts.get(testId), Alert))
        self.assertEquals(self.argus.alerts.get(testId).to_dict(), alert_D)
        self.assertIn((os.path.join(endpoint, "alerts", str(testId)),), tuple(mockPut.call_args))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps([alert_D]), 200))
    def testGetAlerts(self, mockGet):
        res = self.argus.alerts.values()
        self.assertTrue(isinstance(res, list))
        self.assertEquals(len(res), 1)
        self.assertTrue(isinstance(res[0], Alert))
        self.assertEquals(res[0].to_dict(), alert_D)
        self.assertIn((os.path.join(endpoint, "alerts"),), tuple(mockGet.call_args))

    @mock.patch('requests.Session.get', return_value=MockResponse(json.dumps(alert_D), 200))
    def testGetAlert(self, mockGet):
        res = self.argus.alerts.get(testId)
        self.assertTrue(isinstance(res, Alert))
        self.assertEquals(res.to_dict(), alert_D)
        self.assertIn((os.path.join(endpoint, "alerts", str(testId)),), tuple(mockGet.call_args))

    @mock.patch('requests.Session.delete', return_value=MockResponse("", 200))
    def testDeleteAlert(self, mockDelete):
        self.argus.alerts.delete(testId)
        self.assertIn((os.path.join(endpoint, "alerts", str(testId)),), tuple(mockDelete.call_args))


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
        self.alert.triggers.delete(testId)
        self.assertIn((os.path.join(endpoint, "alerts", str(testId), "triggers", str(testId)),), tuple(mockDelete.call_args))


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
        self.alert.notifications.delete(testId)
        self.assertIn((os.path.join(endpoint, "alerts", str(testId), "notifications", str(testId)),), tuple(mockDelete.call_args))


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
