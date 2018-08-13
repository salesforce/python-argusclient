"""
Module containing the classes that model the Argus base objects.
"""

#
# Copyright (c) 2016, salesforce.com, inc.
# All rights reserved.
# Licensed under the BSD 3-Clause license. 
# For full license text, see LICENSE.txt file in the repo root  or https://opensource.org/licenses/BSD-3-Clause
#

import json

try:
    basestring        # Python 2
except NameError:
    basestring = str  # Python 3


class BaseEncodable(object):

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        D = dict((k, v) for k, v in self.__dict__.items() if not k.startswith("_"))
        return D

    @classmethod
    def from_dict(cls, D):
        for f in cls.id_fields:
            if f not in D:
                return None
        else:
            return cls(**D)

    @property
    def argus_id(self):
        """
        The property that gives access to the Argus ID. This is ``None`` for new objects.
        """
        return hasattr(self, "id") and int(self.id) or None

    @argus_id.setter
    def argus_id(self, value):
        self.id = value

    @property
    def owner_id(self):
        """
        The ID of the object that owns this object or ``None``. Only applicable to a few types that are not first-class objects.
        """
        return hasattr(self, "owner_id_field") and hasattr(self, self.owner_id_field) and int(getattr(self, self.owner_id_field)) or None

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.__dict__)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.__dict__ == other.__dict__


class AddListResult(BaseEncodable):
    """
    Represents the result of metric or annotation collection add request.

    Ex: {"Error Messages":[],"Error":"0 metrics","Success":"1 metrics"}
    """

    id_fields = ("Error", "Success")

    def error_messages(self):
        """ Return any error messsages from the result. """
        return self.__dict__["Error Messages"]

    def error_count(self):
        """ Return error count from the result. """
        numEnd = self.Error.index(" ")
        return int(self.Error[0:numEnd])

    def success_count(self):
        """ Return success count from the result. """
        numEnd = self.Success.index(" ")
        return int(self.Success[0:numEnd])


class User(BaseEncodable):
    """
    Represents a User object in Argus.

    **Required parameters to the constructor:**

    :param userName: The username of the Argus user
    :type userName: str

    **Optional parameters to the constructor:**

    :param email: The email address of the Argus user
    :type email: str
    """

    id_fields = ("userName", "email")

    def __init__(self, userName, **kwargs):
        super(User, self).__init__(userName=userName, **kwargs)


class Metric(BaseEncodable):
    """
    Represents a Metric object in Argus.

    **Required parameters to the constructor:**

    :param scope: The scope for the annotation
    :type scope: str
    :param metric: The metric name of the annotation
    :type metric: str

    **Optional parameters to the constructor:**

    :param namespace: The namespace for the metric
    :type namespace: str
    :param displayName: The display name of the metric
    :type displayName: str
    :param unitType: The unit type of the metric value
    :type unitType: str
    :param datapoints: The actual metric data points as a dictionary of values with epoc timestamp as the keys.
    :type datapoints: dict of int:object
    :param tags: A dictionary of tags. Both keys and values should be valid strings.
    :type tags: dict of str:str
    """

    id_fields = ("datapoints",)

    def __init__(self, scope, metric, **kwargs):
        super(Metric, self).__init__(scope=scope, metric=metric, **kwargs)
        if not hasattr(self, "datapoints") or self.datapoints is None:
            self.datapoints = {}
        if not hasattr(self, "tags") or self.tags is None:
            self.tags = {}

    def __str__(self):
        """
        Return a string representation of the metric that can be directly used as the metric expressoin in a metric query and has the format:
        ``scope:metric[{tagk=tagv,...}][:namespace]``
        """
        tags = hasattr(self, "tags") and self.tags or None
        metricWithTags = tags and "%s{%s}" % (self.metric, ",".join("%s=%s" % (k, v) for k, v in self.tags.items())) or self.metric
        return ":".join(str(q) for q in (self.scope, metricWithTags, hasattr(self, "namespace") and self.namespace or None) if q)


class Annotation(BaseEncodable):
    """
    Represents an Annotation object in Argus.

    **Required parameters to the constructor:**

    :param source: The source of the annotation
    :type source: str
    :param scope: The scope for the annotation
    :type scope: str
    :param metric: The metric name of the annotation
    :type metric: str
    :param timestamp: The timestamp of the annotation
    :type timestamp: int
    :param id: An external id for the annotation
    :type id: int

    **Optional parameters to the constructor:**

    :param tags: A dictionary of tags. Both keys and values should be valid strings.
    :type tags: dict of str:str
    :param fields: A dictionary of fields. Both keys and values should be valid strings.
    :type fields: dict of str:str
    """

    id_fields = ("source", "timestamp",)

    def __init__(self, source, scope, metric, id, timestamp, type, **kwargs):
        super(Annotation, self).__init__(source=source, scope=scope, metric=metric, id=id, timestamp=timestamp, type=type, **kwargs)
        if not hasattr(self, "fields") or self.fields is None:
            self.fields = {}
        if not hasattr(self, "tags") or self.tags is None:
            self.tags = {}

    def __str__(self):
        """
        Return a string representation of the annotation that can be directly used as the annotation expresson in an annotation query and has the format:
        ``scope:metric[{tagk=tagv,...}]:source``
        """
        tags = hasattr(self, "tags") and self.tags or None
        metricWithTags = tags and "%s{%s}" % (self.metric, ",".join("%s=%s" % (k, v) for k, v in self.tags.items())) or self.metric
        return ":".join(str(q) for q in (self.scope, metricWithTags, self.source) if q)


class Dashboard(BaseEncodable):
    """
    Represents a Dashboard object in Argus.

    Dashboard name has to be unique across the dashboards owned by the current user.

    **Required parameters to the constructor:**

    :param name: The name of the dashboard
    :type name: str
    :param content: The XML content
    :type content: str

    **Optional parameters to the constructor:**

    :param description: A description for the dashboard
    :type description: str
    :param shared: The shared state of the dashboard.
    :type shared: bool
    :param id: The Argus id of the dashboard
    :type id: int
    """

    id_fields = ("content",)

    def __init__(self, name, content, **kwargs):
        super(Dashboard, self).__init__(name=name, content=content, **kwargs)


class Namespace(BaseEncodable):
    """
    Represents a Namespace object in Argus.

    **Required parameters to the constructor:**

    :param qualifier: The namespace qualifier
    :type qualifier: str

    **Optional parameters to the constructor:**

    :param usernames: The list of usernames that are authorized to post metrics to the namespace.
    :type usernames: list of str
    :param id: The Argus id of this namespace
    :type id: int
    """

    id_fields = ("qualifier",)

    def __init__(self, qualifier, **kwargs):
        assert qualifier and isinstance(qualifier, basestring), "A string qualifier is required for namespace"
        super(Namespace, self).__init__(qualifier=qualifier, **kwargs)


class Alert(BaseEncodable):
    """
    Represents an Alert object in Argus.

    Alert name has to be unique across the alerts owned by the current user.

    **Required parameters to the constructor:**

    :param name: The name of the alert
    :type name: str
    :param expression: The metric query expression
    :type expression: str
    :param cronEntry: The cron expression
    :type cronEntry: str

    **Optional parameters to the constructor:**

    :param enabled: The enabled state of the alert
    :type enabled: bool
    :param missingDataNotificationEnabled: The enabled state of missing data notification
    :type missingDataNotificationEnabled: bool
    :param triggerIds: The list of IDs for the triggers owned by this alert.
    :type triggerIds: list of int
    :param notificationIds: The list of IDs for the notifications owned by this alert.
    :type notificationIds: list of int
    :param shared: The shared state of the alert
    :type enabled: bool
    """

    id_fields = ("expression", "cronEntry",)

    def __init__(self, name, expression, cronEntry, **kwargs):
        self._triggers = None
        self._notifications = None
        super(Alert, self).__init__(name=name, expression=expression, cronEntry=cronEntry, **kwargs)

    @property
    def trigger(self):
        """ A convenience property to be used when :attr:`triggers` contains a single :class:`argusclient.model.Trigger`. """
        return self._triggers and len(self._triggers) == 1 and self._triggers[0] or None

    @trigger.setter
    def trigger(self, value):
        if not isinstance(value, Trigger): raise ValueError("argument should be of Trigger type, but is: %s" % type(value))
        if not ((value.owner_id is None and self.argus_id is None) or value.owner_id == self.argus_id): raise ValueError("trigger owned by alert id: %s not by %s" % (value.owner_id, self.argus_id))
        self._triggers = [value]

    @property
    def triggers(self):
        """ Property to get and set triggers on the alert. """
        return self._triggers

    @triggers.setter
    def triggers(self, value):
        if not isinstance(value, list): raise ValueError("value should be of list type, but is: %s" % type(value))
        # This is a special case allowed only while adding new alerts, so ensure that argus_id of self and the objects is None.
        # TODO Check for item type also
        self._triggers = value

    @property
    def notification(self):
        """ A convenience property to be used when :attr:`notifications` contains a single :class:`argusclient.model.Notification`. """
        return self._notifications and len(self._notifications) == 1 and self._notifications[0] or None

    @notification.setter
    def notification(self, value):
        if not isinstance(value, Notification): raise ValueError("value should be of Notification type, but is: %s" % type(value))
        if not ((value.owner_id is None and self.argus_id is None) or value.owner_id == self.argus_id): raise ValueError("notification owned by alert id: %s not by %s" % (value.owner_id, self.argus_id))
        self._notifications = [value]

    @property
    def notifications(self):
        """ Property to get and set notifications on the alert. """
        return self._notifications

    @notifications.setter
    def notifications(self, value):
        if not isinstance(value, list): raise ValueError("value should be of list type, but is: %s" % type(value))
        # This is a special case allowed only while adding new alerts, so ensure that argus_id of self and the objects is None.
        # TODO Check for item type also
        self._notifications = value


class Trigger(BaseEncodable):
    """
    Represents a Trigger object in Argus.

    **Required parameters to the constructor:**

    :param name: Name of the trigger
    :type name: str
    :param type: Type of the trigger. Must be one of these: :attr:`GREATER_THAN`, :attr:`GREATER_THAN_OR_EQ`, :attr:`LESS_THAN`, :attr:`LESS_THAN_OR_EQ`, :attr:`EQUAL`, :attr:`NOT_EQUAL`, :attr:`BETWEEN`, :attr:`NOT_BETWEEN`, :attr:`NO_DATA`.
    :type type: str
    :param threshold: Threshold for the trigger
    :type threshold: float
    :param inertia: Inertia for the trigger
    :type inertia: int

    **Optional parameters to the constructor:**

    :param secondaryThreshold: Secondary threshold.
    :type secondaryThreshold: float
    :param notificationIds: List of IDs of notifications that this trigger is associated with.
    :type notificationIds: list of int
    :param alertId: ID of the alert that this trigger belongs to.
    :type alertId: int
    """

    id_fields = ("threshold",)
    owner_id_field = "alertId"

    GREATER_THAN = "GREATER_THAN"
    GREATER_THAN_OR_EQ = "GREATER_THAN_OR_EQ"
    LESS_THAN = "LESS_THAN"
    LESS_THAN_OR_EQ = "LESS_THAN_OR_EQ"
    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    BETWEEN = "BETWEEN"
    NOT_BETWEEN = "NOT_BETWEEN"
    NO_DATA = "NO_DATA"

    #: Set of all valid trigger types.
    VALID_TYPES = frozenset((GREATER_THAN, GREATER_THAN_OR_EQ, LESS_THAN, LESS_THAN_OR_EQ, EQUAL, NOT_EQUAL, BETWEEN, NOT_BETWEEN, NO_DATA))

    def __init__(self, name, type, threshold, inertia, **kwargs):
        assert type in Trigger.VALID_TYPES, "type is not valid: %s" % type
        super(Trigger, self).__init__(name=name, type=type, threshold=threshold, inertia=inertia, **kwargs)


class Notification(BaseEncodable):
    """
    Represents a Notification object in Argus.

    **Required parameters to the constructor:**

    :param name: The name of the notification
    :type name: str
    :param notifierName: The name of the notifier implementation. Must be one of :attr:`EMAIL`, :attr:`AUDIT`, :attr:`GOC`, :attr:`GUS`
    :type notifierName: str

    **Optional parameters to the constructor:**

    :param subscriptions: The subscriptions for the notifier implementation, such as email ids in case of :attr:`EMAIL`.
    :type subscriptions: list of str
    :param cooldownPeriod: The cooldown period
    :type cooldownPeriod: float
    :param cooldownExpiration: The cooldown expiration
    :type cooldownExpiration: float
    :param triggerIds: List of IDs of triggers that this notification is associated with.
    :type triggerIds: list of int
    :param alertId: ID of the alert that this trigger belongs to.
    :type alertId: int
    """

    id_fields = ("notifierName",)
    owner_id_field = "alertId"

    EMAIL = "com.salesforce.dva.argus.service.alert.notifier.EmailNotifier"
    AUDIT = "com.salesforce.dva.argus.service.alert.notifier.AuditNotifier"
    GOC = "com.salesforce.dva.argus.service.alert.notifier.GOCNotifier"
    GUS = "com.salesforce.dva.argus.service.alert.notifier.GusNotifier"

    #: Set of all valid notifier implementation names.
    VALID_NOTIFIERS = frozenset((EMAIL, AUDIT, GOC, GUS))

    def __init__(self, name, notifierName, metricsToAnnotate=None, **kwargs):
        assert notifierName in Notification.VALID_NOTIFIERS, "notifierName is not valid: %s" % notifierName
        super(Notification, self).__init__(name=name, notifierName=notifierName, metricsToAnnotate=metricsToAnnotate or [], **kwargs)


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        return self.to_json(obj)

    def to_json(self, obj):
        if isinstance(obj, BaseEncodable):
            return obj.to_dict()

        return json.JSONEncoder.default(self, obj)


class JsonDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        kwargs['object_hook'] = self.from_json
        super(JsonDecoder, self).__init__(*args, **kwargs)

    def from_json(self, jsonObj):
        if not jsonObj or not isinstance(jsonObj, dict):
            return jsonObj
        for cls in (Metric, Dashboard, AddListResult, User, Namespace, Annotation, Alert, Trigger, Notification):
            obj = cls.from_dict(jsonObj)
            if obj:
                return obj
        else:
            return jsonObj
