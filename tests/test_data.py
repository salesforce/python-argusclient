#
# Copyright (c) 2016, salesforce.com, inc.
# All rights reserved.
# Licensed under the BSD 3-Clause license. 
# For full license text, see LICENSE.txt file in the repo root  or https://opensource.org/licenses/BSD-3-Clause
#

scope = "test.scope"
metric = "test.metric"
datapoints = {"10": 1, "20": 2}
tags = {"test.tag": "test.value"}
namespace = "test.namespace"
usernames = ["testUser1", "testUser2"]
displayName = "test.displayName"
unitType = "test.unitType"
source = "test.source"
testId = 10
testId2 = 11
testId3 = 12
timestamp = 10
testType = "testType"
dashboardName = "test.dashboard"
content = "test content"
userName = "test.user"
password = "test.password"
email = "user@test.com"
fields = {"test.field": "test.value"}
endpoint = "http://test.host:12345/argusws"
cookies = dict(JSESSIONID="abcd")
aggregator = "test.aggregator"
alertName = "test.alert"
alertName_2 = "test.alert.2"
alertQuery = "-1d:test.scope:test.metric:sum"
alertCron = "* */1 * * *"
triggerName = "test.trigger"
notificationName = "test.notification"
groupPermissionIdentifier = "group"
userPermissionIdentifier = "user"
groupID = "5eb1fc18-c985-47eb-94f9-aebce66e119a"
permissionNames = ["VIEW", "EDIT", "DELETE"]
permissionGroupId = '24231-52321-43523-64353-23111'
username = "testuser"
permission_ids = [1,2,3]
user_type = "user"
group_type = "group"
group_id = "c8be7819-bf5e-40aa-8535-88694d34280f"
entity_id = 23590046

compAlertID = 6000
childAlertID_1 = 6003
childAlertID_2 = 6009
triggerID_1 = 6005
compAlert_notificationID = 6007

metric_D = {
    "scope": scope,
    "metric": metric,
    "tags": {
        "host": "testHost"
    },
    "namespace": namespace,
    "displayName": displayName,
    "units": "testUnits",
    "datapoints": {
        "1459250699000": "10",
        "1459250700000": "9",
    }
}

annotation_D = {
    "source": source,
    "scope": scope,
    "metric": metric,
    "id": testId,
    "timestamp": timestamp,
    "type": "generated",
    "tags": {
        "host": "testHost"
    },
    "fields": {
        "user": userName
    }
}

user_D = {
    "id": 101851,
    "createdById": 1,
    "createdDate": 1425386044262,
    "modifiedById": 1,
    "modifiedDate": 1445273664666,
    "userName": userName,
    "email": email,
    "preferences": {},
    "ownedDashboardIds": [
        "101970"
    ],
    "privileged": False
}

dashboard_D = {
    "id": testId,
    "createdById": 101402,
    "createdDate": 1425598578661,
    "modifiedById": 101402,
    "modifiedDate": 1445273708714,
    "name": "Oracle stats",
    "content": content,
    "ownerName": userName,
    "shared": True,
    "description": "Test description"
}

dashboard_2_D = {
    "id": testId2,
    "createdById": 101402,
    "createdDate": 1425598578661,
    "modifiedById": 101402,
    "modifiedDate": 1445273708714,
    "name": "Oracle stats",
    "content": content,
    "ownerName": userName,
    "shared": True,
    "description": "Test description"
}

groupPermission_D = {
    "type": groupPermissionIdentifier,
    "groupId": groupID,
    "permissionIds": [0,1,2]
}

userPermission_D = {
    "type": userPermissionIdentifier,
    "permissionNames": permissionNames,
    "username": userName
}

permission_user_D = {
    "id": testId,
    "createdById": 6906380,
    "createdDate": 1616098911000,
    "modifiedById": 6906380,
    "modifiedDate": 1616098911000,
    "type": user_type,
    "username": userName,
    "permissionIds": permission_ids,
    "entityId": testId,
    "groupId": ""
}

permission_group_D = {
    "id": testId,
    "createdById": 6906380,
    "createdDate": 1616098911000,
    "modifiedById": 6906380,
    "modifiedDate": 1616098911000,
    "type": group_type,
    "groupId": group_id,
    "username": '',
    "permissionIds": [],
    "entityId": testId
}

namespace_D = {
    "id": testId,
    "createdById": 101851,
    "createdDate": 1459433602777,
    "modifiedById": 101851,
    "modifiedDate": 1459433602777,
    "qualifier": namespace,
    "usernames": [
        userName
    ]
}

addmetricresult_D = {
    "Error Messages": [],
    "Error": "0 metrics",
    "Success": "1 metrics"
}

addannotationresult_D = {
    "Error Messages": [],
    "Error": "0 annotations",
    "Success": "1 annotations"
}

alert_D = {
    "id": testId,
    "createdById": 101997,
    "createdDate": 1459857033871,
    "modifiedById": 101997,
    "modifiedDate": 1459857033871,
    "name": alertName,
    "expression": "-1d:hdara:test:sum",
    "cronEntry": "*/15 * * * *",
    "enabled": False,
    "missingDataNotificationEnabled": False,
    "notificationsIds": [],
    "triggersIds": [],
    "ownerName": userName
}

alert_2_D = {
    "id": testId2,
    "createdById": 101997,
    "createdDate": 1459857033871,
    "modifiedById": 101997,
    "modifiedDate": 1459857033871,
    "name": alertName_2,
    "expression": "-1d:hdara:test:sum",
    "cronEntry": "*/15 * * * *",
    "enabled": False,
    "missingDataNotificationEnabled": False,
    "notificationsIds": [],
    "triggersIds": [],
    "ownerName": userName
}

trigger_D = {
    "id": testId,
    "createdById": 101997,
    "createdDate": 1459917155968,
    "modifiedById": 101997,
    "modifiedDate": 1459917155968,
    "type": "GREATER_THAN",
    "name": triggerName,
    "threshold": 10000,
    "secondaryThreshold": 0,
    "inertia": 600000,
    "alertId": 304255,
    "notificationIds": []
}

trigger_2_D = {
    "id": testId2,
    "createdById": 101997,
    "createdDate": 1459917155968,
    "modifiedById": 101997,
    "modifiedDate": 1459917155968,
    "type": "GREATER_THAN",
    "name": triggerName,
    "threshold": 10000,
    "secondaryThreshold": 0,
    "inertia": 600000,
    "alertId": 304255,
    "notificationIds": []
}

notification_D = {
    "id": testId,
    "createdById": 101997,
    "createdDate": 1459917506873,
    "modifiedById": 101997,
    "modifiedDate": 1459917506873,
    "name": notificationName,
    "notifierName": "com.salesforce.dva.argus.service.alert.notifier.EmailNotifier",
    "subscriptions": [
        email
    ],
    "metricsToAnnotate": [],
    "cooldownPeriod": 0,
    "cooldownExpiration": 0,
    "triggersIds": [],
    "alertId": 304255
}

notification_2_D = {
    "id": testId2,
    "createdById": 101997,
    "createdDate": 1459917506873,
    "modifiedById": 101997,
    "modifiedDate": 1459917506873,
    "name": notificationName,
    "notifierName": "com.salesforce.dva.argus.service.alert.notifier.EmailNotifier",
    "subscriptions": [
        email
    ],
    "metricsToAnnotate": [],
    "cooldownPeriod": 0,
    "cooldownExpiration": 0,
    "triggersIds": [],
    "alertId": 304255
}

notification_3_D = {
    "id": testId3,
    "createdById": 101997,
    "createdDate": 1459917506873,
    "modifiedById": 101997,
    "modifiedDate": 1459917506873,
    "name": notificationName,
    "notifierName": "com.salesforce.dva.argus.service.alert.notifier.EmailNotifier",
    "subscriptions": [
        email
    ],
    "metricsToAnnotate": [],
    "cooldownPeriod": 0,
    "cooldownExpiration": 0,
    "triggersIds": [],
    "alertId": 304255
}

alert_all_info_D = {
    "id": testId,
    "createdById": 101997,
    "createdDate": 1459857033871,
    "modifiedById": 101997,
    "modifiedDate": 1459857033871,
    "name": alertName,
    "expression": "-1d:hdara:test:sum",
    "cronEntry": "*/15 * * * *",
    "enabled": False,
    "missingDataNotificationEnabled": False,
    "notificationsIds": [testId, testId, testId],
    "triggersIds": [testId, testId],
    "triggers": [trigger_D, trigger_2_D],
    "notifications": [notification_D, notification_2_D, notification_3_D],
    "ownerName": userName
}

alert_all_info_2_D = {
    "id": testId2,
    "createdById": 101997,
    "createdDate": 1459857033871,
    "modifiedById": 101997,
    "modifiedDate": 1459857033871,
    "name": alertName_2,
    "expression": "-1d:hdara:test:sum",
    "cronEntry": "*/15 * * * *",
    "enabled": False,
    "missingDataNotificationEnabled": False,
    "notificationsIds": [testId, testId, testId],
    "triggersIds": [testId, testId],
    "triggers": [trigger_D, trigger_2_D],
    "notifications": [notification_D, notification_2_D, notification_3_D],
    "ownerName": userName
}

compalert_D = {
    'id': compAlertID,
    'alertType': 'COMPOSITE',
    'name': 'CompAlertTest',
    'triggerIds': [],
    'enabled': False,
    'cronEntry': '*/2 * * * *',
    'notificationsIds': [],
    'expression': {'expression': {'operator': 'AND', 'join': [], 'terms': []}, 'termDefinitions': []},
    'childAlertsIds': []
 }

childAlert_1 = {
    'id': childAlertID_1,
    'triggersIds': [],
    'alertType': 'COMPOSITE_CHILD',
    'name': 'CompAlertTest-ChildAlert-1',
    'cronEntry': '* * * * *',
    'notificationsIds': [],
    'enabled': False,
    'expression': '-1h:-0m:tracer.api.XRD.NONE.none:requestsReceivedLastMin:avg:1m-avg'
}

childAlert_2 = {
    'id': childAlertID_2,
    'triggersIds': [],
    'alertType': 'COMPOSITE_CHILD',
    'name': 'CompAlertTest-ChildAlert-2',
    'cronEntry': '* * * * *',
    'notificationsIds': [],
    'enabled': False,
    'expression': '-1h:-0m:tracer.api.XRD.NONE.none:avgQueryTime:avg:1m-avg'
}

childAlert_trigger_1 = {
    'id': triggerID_1,
    'threshold': 1.0,
    'type': 'GREATER_THAN',
    'inertia': 0,
    'name': 'CompAlertTest/trigger1'
}

compAlert_notification = {
    'id': compAlert_notificationID,
    'severityLevel': 5,
    'name': 'Email1',
    'subscriptions': ['jdoe@example.com'],
    'notifierName': 'com.salesforce.dva.argus.service.alert.notifier.EmailNotifier',
    'metricsToAnnotate': [],
    'cooldownPeriod': 0,
    'sractionable': False,
    'customText': 'None'
}