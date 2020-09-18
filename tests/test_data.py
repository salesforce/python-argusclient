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
alertQuery = "-1d:test.scope:test.metric:sum"
alertCron = "* */1 * * *"
triggerName = "test.trigger"
notificationName = "test.notification"

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

