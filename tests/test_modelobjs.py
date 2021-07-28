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
        self.assertEquals(m.scope, scope)
        self.assertEquals(m.metric, metric)

        for k, v in datapoints.items():
            m.datapoints[k] = v
        self.assertEquals(m.datapoints, datapoints)

        m.datapoints = {}
        m.datapoints.update(datapoints)
        self.assertEquals(m.datapoints, datapoints)

        m.datapoints = datapoints
        self.assertEquals(m.datapoints, datapoints)

        for k, v in tags.items():
            m.tags[k] = v
        self.assertEquals(m.tags, tags)

        m.tags = {}
        m.tags.update(tags)
        self.assertEquals(m.tags, tags)

        m.tags = tags
        self.assertEquals(m.tags, tags)

        m = Metric(scope, metric, datapoints=datapoints)
        self.assertEquals(m.datapoints, datapoints)
        self.assertEquals(str(m), scope+":"+metric)

        m = Metric(scope, metric, namespace=namespace, displayName=displayName, unitType=unitType, id=testId)
        self.assertEquals(m.namespace, namespace)
        self.assertEquals(m.displayName, displayName)
        self.assertEquals(m.unitType, unitType)
        self.assertEquals(m.id, testId)
        self.assertEquals(str(m), scope + ":" + metric + ":" + namespace)

        m.tags = tags
        self.assertEquals(str(m), scope + ":" + metric + "{test.tag=test.value}" + ":" + namespace)

    def testCreateDashboard(self):
        d = Dashboard(dashboardName, content, shared=False, id=testId)
        self.assertEquals(d.name, dashboardName)
        self.assertEquals(d.content, content)
        self.assertEquals(d.id, testId)

    def testCreateUserPermission(self):
        p = Permission(userPermissionIdentifier, permissionNames, username=userName)
        self.assertEquals(p.type, userPermissionIdentifier)
        self.assertEquals(p.permissionNames, permissionNames)
        self.assertEquals(p.username, userName)

    def testCreateGroupPermission(self):
        p = Permission(groupPermissionIdentifier, permissionNames, groupId=permissionGroupId)
        self.assertEquals(p.type, groupPermissionIdentifier)
        self.assertEquals(p.permissionNames, permissionNames)
        self.assertEquals(p.groupId, permissionGroupId)

    def testCreateUser(self):
        u = User(userName, email=email, id=testId)
        self.assertEquals(u.userName, userName)
        self.assertEquals(u.email, email)
        self.assertEquals(u.id, testId)

    def testCreateNamespace(self):
        n = Namespace(namespace, usernames=usernames)
        self.assertEquals(n.qualifier, namespace)
        self.assertEquals(n.usernames, usernames)

    def testCreateAnnotation(self):
        a = Annotation(source, scope, metric, testId, timestamp, testType)
        self.assertEquals(a.source, source)
        self.assertEquals(a.scope, scope)
        self.assertEquals(a.metric, metric)
        self.assertEquals(a.id, testId)
        self.assertEquals(a.timestamp, timestamp)
        self.assertEquals(a.type, testType)
        self.assertEquals(str(a), scope + ":" + metric + ":"+source)

        for k, v in tags.items():
            a.tags[k] = v
        self.assertEquals(a.tags, tags)
        self.assertEquals(str(a), scope + ":" + metric + "{test.tag=test.value}:" + source)

        a.tags = {}
        a.tags.update(tags)
        self.assertEquals(a.tags, tags)

        a.tags = tags
        self.assertEquals(a.tags, tags)

        for k, v in fields.items():
            a.fields[k] = v
        self.assertEquals(a.fields, fields)

        a.fields = {}
        a.fields.update(fields)
        self.assertEquals(a.fields, fields)

        a.fields = fields
        self.assertEquals(a.fields, fields)

    def testAddListResult(self):
        errors = ["error1", "error2"]
        D = {
            "Error Messages": errors,
            "Error": "1 metrics",
            "Success": "2 metrics"
        }
        r = AddListResult(**D)
        self.assertEquals(r.error_messages(), errors)
        self.assertEquals(r.error_count(), 1)
        self.assertEquals(r.success_count(), 2)

    def testCreateAlert(self):
        a = Alert(alertName, alertQuery, alertCron)
        self.assertEquals(a.name, alertName)
        self.assertEquals(a.expression, alertQuery)
        self.assertEquals(a.cronEntry, alertCron)

    def testCreateTrigger(self):
        t = Trigger(triggerName, Trigger.EQUAL, 100, 200)
        self.assertEquals(t.name, triggerName)
        self.assertEquals(t.type, Trigger.EQUAL)
        self.assertEquals(t.threshold, 100)
        self.assertEquals(t.inertia, 200)

    def testCreateTriggerInvalidType(self):
        self.failUnlessRaises(AssertionError, lambda: Trigger(triggerName, "abc", 100, 200))

    def testCreateNotification(self):
        n = Notification(notificationName, notifierName=Notification.EMAIL, subscriptions=[email])
        self.assertEquals(n.name, notificationName)
        self.assertEquals(n.notifierName, Notification.EMAIL)
        self.assertEquals(n.subscriptions, [email])

    def testCreateNotificationInvalidNotifier(self):
        self.failUnlessRaises(AssertionError, lambda: Notification(notificationName, "abc"))

    def testCreateUserPermission(self):
        permission = Permission(user_type, id=testId, permissionIds=permission_ids, username=username, entityId=testId)
        self.assertEquals(permission.type, user_type)
        self.assertEquals(permission.entityId, testId)
        self.assertEquals(permission.permissionIds, permission_ids)
        self.assertEquals(permission.username, username)

    def testCreateGroupPermission(self):
        permission = Permission(group_type, id=testId, groupId=group_id, entityId=testId)
        self.assertEquals(permission.type, group_type)
        self.assertEquals(permission.entityId, testId)
        self.assertEquals(permission.groupId, group_id)

    def testCreateInvalidPermission(self):
        self.failUnlessRaises(AssertionError, lambda: Permission("abc", id=testId))

    def testCreateAlertDeep(self):
        trigger = Trigger(triggerName, Trigger.EQUAL, 100, 200)
        notification = Notification(notificationName, notifierName=Notification.EMAIL, subscriptions=[email])
        a = Alert(alertName, alertQuery, alertCron, trigger=trigger, notification=notification)
        self.assertEquals(a.trigger, trigger)
        self.assertEquals(a.notification, notification)
        a.trigger = trigger
        a.notification = notification
        self.assertEquals(a.trigger, trigger)
        self.assertEquals(a.notification, notification)


class TestEncoding(unittest.TestCase):
    def setUp(self):
        self.objClasses = []
        for v in argusclient.__dict__.values():
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
        self._testFor(groupPermission_D, GroupPermission)

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
        self.assertEquals(o, D)

    def _testFor(self, D, objClass):
        o = objClass.from_dict(D)
        self.assertTrue(o is not None)
        self.assertTrue(isinstance(o, objClass))
        self.assertEquals(o.to_dict(), D)
        if "id" in D:
            self.assertEquals(o.argus_id, D["id"])
        if hasattr(objClass, "owner_id_field"):
            self.assertEquals(o.owner_id, D[getattr(objClass, "owner_id_field")])
        for c in self.objClasses:
            if c == objClass:
                pass
            else:
                self.assertEquals(c.from_dict(D), None, "Expected None for class: %s" % c)
        jsonStr = json.dumps(D)
        o = json.loads(jsonStr, cls=JsonDecoder)
        self._assertType(o, objClass)
        self.assertEquals(json.loads(jsonStr), D)

    def _assertType(self, obj, objClass):
        self.assertTrue(isinstance(obj, objClass),
                "Encoded obj of type: %s is not of expected type: %s" % (type(obj), objClass))

class TestW_2816614(unittest.TestCase):
    def test_namespace_qualifier(self):
        ns = Namespace.from_dict(namespace_D)
        self.assertEquals(ns.qualifier, namespace)
        self.assertEquals(ns.__dict__.get("qualifier"), namespace)
        ns.qualifier = "test"
        self.assertEquals(ns.qualifier, "test")
        D = dict(namespace_D)
        D["qualifier"] = "test"
        self.assertEquals(ns.to_dict(), D)

    def test_metric_namespace(self):
        m = Metric.from_dict(metric_D)
        self.assertEquals(m.namespace, namespace)
        self.assertEquals(m.__dict__.get("namespace"), namespace)
        m.namespace = "test"
        self.assertEquals(m.namespace, "test")
