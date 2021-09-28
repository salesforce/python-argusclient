#
# Copyright (c) 2016, salesforce.com, inc.
# All rights reserved.
# Licensed under the BSD 3-Clause license. 
# For full license text, see LICENSE.txt file in the repo root  or https://opensource.org/licenses/BSD-3-Clause
#

import unittest, json

import argusclient
from argusclient import *
from argusclient.model import *

from test_data import *


class ObjTest(unittest.TestCase):
    """
    Test the basic interaction with various model objects.
    """

    def testCreateMetric(self):
        m = Metric(scope, metric)
        self.assertEqual(m.scope, scope)
        self.assertEqual(m.metric, metric)

        for k, v in list(datapoints.items()):
            m.datapoints[k] = v
        self.assertEqual(m.datapoints, datapoints)

        m.datapoints = {}
        m.datapoints.update(datapoints)
        self.assertEqual(m.datapoints, datapoints)

        m.datapoints = datapoints
        self.assertEqual(m.datapoints, datapoints)

        for k, v in list(tags.items()):
            m.tags[k] = v
        self.assertEqual(m.tags, tags)

        m.tags = {}
        m.tags.update(tags)
        self.assertEqual(m.tags, tags)

        m.tags = tags
        self.assertEqual(m.tags, tags)

        m = Metric(scope, metric, datapoints=datapoints)
        self.assertEqual(m.datapoints, datapoints)
        self.assertEqual(str(m), scope+":"+metric)

        m = Metric(scope, metric, namespace=namespace, displayName=displayName, unitType=unitType, id=testId)
        self.assertEqual(m.namespace, namespace)
        self.assertEqual(m.displayName, displayName)
        self.assertEqual(m.unitType, unitType)
        self.assertEqual(m.id, testId)
        self.assertEqual(str(m), scope + ":" + metric + ":" + namespace)

        m.tags = tags
        self.assertEqual(str(m), scope + ":" + metric + "{test.tag=test.value}" + ":" + namespace)

    def testCreateDashboard(self):
        d = Dashboard(dashboardName, content, shared=False, id=testId)
        self.assertEqual(d.name, dashboardName)
        self.assertEqual(d.content, content)
        self.assertEqual(d.id, testId)

    def testCreateUserPermission(self):
        p = Permission(userPermissionIdentifier, permissionNames, username=userName)
        self.assertEqual(p.type, userPermissionIdentifier)
        self.assertEqual(p.permissionNames, permissionNames)
        self.assertEqual(p.username, userName)

    def testCreateGroupPermission(self):
        p = Permission(groupPermissionIdentifier, permissionNames, groupId=permissionGroupId)
        self.assertEqual(p.type, groupPermissionIdentifier)
        self.assertEqual(p.permissionNames, permissionNames)
        self.assertEqual(p.groupId, permissionGroupId)

    def testCreateUser(self):
        u = User(userName, email=email, id=testId)
        self.assertEqual(u.userName, userName)
        self.assertEqual(u.email, email)
        self.assertEqual(u.id, testId)

    def testCreateNamespace(self):
        n = Namespace(namespace, usernames=usernames)
        self.assertEqual(n.qualifier, namespace)
        self.assertEqual(n.usernames, usernames)

    def testCreateAnnotation(self):
        a = Annotation(source, scope, metric, testId, timestamp, testType)
        self.assertEqual(a.source, source)
        self.assertEqual(a.scope, scope)
        self.assertEqual(a.metric, metric)
        self.assertEqual(a.id, testId)
        self.assertEqual(a.timestamp, timestamp)
        self.assertEqual(a.type, testType)
        self.assertEqual(str(a), scope + ":" + metric + ":"+source)

        for k, v in list(tags.items()):
            a.tags[k] = v
        self.assertEqual(a.tags, tags)
        self.assertEqual(str(a), scope + ":" + metric + "{test.tag=test.value}:" + source)

        a.tags = {}
        a.tags.update(tags)
        self.assertEqual(a.tags, tags)

        a.tags = tags
        self.assertEqual(a.tags, tags)

        for k, v in list(fields.items()):
            a.fields[k] = v
        self.assertEqual(a.fields, fields)

        a.fields = {}
        a.fields.update(fields)
        self.assertEqual(a.fields, fields)

        a.fields = fields
        self.assertEqual(a.fields, fields)

    def testAddListResult(self):
        errors = ["error1", "error2"]
        D = {
            "Error Messages": errors,
            "Error": "1 metrics",
            "Success": "2 metrics"
        }
        r = AddListResult(**D)
        self.assertEqual(r.error_messages(), errors)
        self.assertEqual(r.error_count(), 1)
        self.assertEqual(r.success_count(), 2)

    def testCreateAlert(self):
        a = Alert(alertName, alertQuery, alertCron)
        self.assertEqual(a.name, alertName)
        self.assertEqual(a.expression, alertQuery)
        self.assertEqual(a.cronEntry, alertCron)

    def testCreateTrigger(self):
        t = Trigger(triggerName, Trigger.EQUAL, 100, 200)
        self.assertEqual(t.name, triggerName)
        self.assertEqual(t.type, Trigger.EQUAL)
        self.assertEqual(t.threshold, 100)
        self.assertEqual(t.inertia, 200)

    def testCreateTriggerInvalidType(self):
        self.assertRaises(AssertionError, lambda: Trigger(triggerName, "abc", 100, 200))

    def testCreateNotification(self):
        n = Notification(notificationName, notifierName=Notification.EMAIL, subscriptions=[email])
        self.assertEqual(n.name, notificationName)
        self.assertEqual(n.notifierName, Notification.EMAIL)
        self.assertEqual(n.subscriptions, [email])

    def testCreateNotificationInvalidNotifier(self):
        self.assertRaises(AssertionError, lambda: Notification(notificationName, "abc"))

    def testCreateUserPermission(self):
        permission = Permission(userPermissionIdentifier, id=testId, permissionIds=permission_ids, username=username, entityId=testId)
        self.assertEqual(permission.type, userPermissionIdentifier)
        self.assertEqual(permission.entityId, testId)
        self.assertEqual(permission.permissionIds, permission_ids)
        self.assertEqual(permission.username, username)

    def testCreateGroupPermission(self):
        permission = Permission(groupPermissionIdentifier, id=testId, groupId=group_id, entityId=testId)
        self.assertEqual(permission.type, groupPermissionIdentifier)
        self.assertEqual(permission.entityId, testId)
        self.assertEqual(permission.groupId, group_id)

    def testCreateInvalidPermission(self):
        self.assertRaises(AssertionError, lambda: Permission("abc", id=testId))

    def testCreateAlertDeep(self):
        trigger = Trigger(triggerName, Trigger.EQUAL, 100, 200)
        notification = Notification(notificationName, notifierName=Notification.EMAIL, subscriptions=[email])
        a = Alert(alertName, alertQuery, alertCron, trigger=trigger, notification=notification)
        self.assertEqual(a.trigger, trigger)
        self.assertEqual(a.notification, notification)
        a.trigger = trigger
        a.notification = notification
        self.assertEqual(a.trigger, trigger)
        self.assertEqual(a.notification, notification)


class TestEncoding(unittest.TestCase):
    def setUp(self):
        self.objClasses = []
        for v in list(argusclient.__dict__.values()):
            if v != BaseEncodable and isinstance(v, type) and issubclass(v, BaseEncodable):
                self.objClasses.append(v)
        if not self.objClasses:
            raise Exception("Found no classes of type BaseEncodable")

    def testEncMetric(self):
        self._testFor(metric_D, Metric)

    def testEncAnnotation(self):
        self._testFor(annotation_D, Annotation)

    def testEncUser(self):
        self._testFor(user_D, User)

    def testEncDashboard(self):
        self._testFor(dashboard_D, Dashboard)

    def testEncUserPermission(self):
        self._testFor(userPermission_D, Permission)

    def testEncGroupPermission(self):
        self._testFor(groupPermission_D, Permission)

    def testEncNamespace(self):
        self._testFor(namespace_D, Namespace)

    def testEncAddMetricResult(self):
        self._testFor(addmetricresult_D, AddListResult)

    def testEncAddAnnotationResult(self):
        self._testFor(addannotationresult_D, AddListResult)

    def testEncAlert(self):
        self._testFor(alert_D, Alert)

    def testEncTrigger(self):
        self._testFor(trigger_D, Trigger)

    def testEncNotification(self):
        self._testFor(notification_D, Notification)

    def testDecAlert(self):
        jsonStr = json.dumps(alert_all_info_D)
        o = json.loads(jsonStr, cls=JsonDecoder)
        self._assertType(o, Alert)

        assert o.triggers
        assert len(o.triggers) == 2
        for trigger in o.triggers:
            self._assertType(trigger, Trigger)

        assert o.notifications
        assert len(o.notifications) == 3
        for notif in o.notifications:
            self._assertType(notif, Notification)

    def testNonModel(self):
        D = dict(someRandomField="1", anotherRandomField="2")
        jsonStr = json.dumps(D)
        o = json.loads(jsonStr, cls=JsonDecoder)
        self.assertTrue(isinstance(o, dict))
        self.assertEqual(o, D)

    def _testFor(self, D, objClass):
        o = objClass.from_dict(D)
        self.assertTrue(o is not None)
        self.assertTrue(isinstance(o, objClass))
        self.assertEqual(o.to_dict(), D)
        if "id" in D:
            self.assertEqual(o.argus_id, D["id"])
        if hasattr(objClass, "owner_id_field"):
            self.assertEqual(o.owner_id, D[getattr(objClass, "owner_id_field")])
        for c in self.objClasses:
            if c == objClass:
                pass
            else:
                self.assertEqual(c.from_dict(D), None, "Expected None for class: %s" % c)
        jsonStr = json.dumps(D)
        o = json.loads(jsonStr, cls=JsonDecoder)
        self._assertType(o, objClass)
        self.assertEqual(json.loads(jsonStr), D)

    def _assertType(self, obj, objClass):
        self.assertTrue(isinstance(obj, objClass),
                "Encoded obj of type: %s is not of expected type: %s" % (type(obj), objClass))

class TestW_2816614(unittest.TestCase):
    def test_namespace_qualifier(self):
        ns = Namespace.from_dict(namespace_D)
        self.assertEqual(ns.qualifier, namespace)
        self.assertEqual(ns.__dict__.get("qualifier"), namespace)
        ns.qualifier = "test"
        self.assertEqual(ns.qualifier, "test")
        D = dict(namespace_D)
        D["qualifier"] = "test"
        self.assertEqual(ns.to_dict(), D)

    def test_metric_namespace(self):
        m = Metric.from_dict(metric_D)
        self.assertEqual(m.namespace, namespace)
        self.assertEqual(m.__dict__.get("namespace"), namespace)
        m.namespace = "test"
        self.assertEqual(m.namespace, "test")
