"""
This modules contains various client classes to interact with the Argus RESTful webservice endpoints.
The implementation is based on API documentation from ``/help`` on various endpoints
and `web service reference <https://github.com/SalesforceEng/Argus/wiki/Web%20Service%20API>`__.
"""

import requests
import json
import os
import logging
import collections
import httplib

from .model import Namespace, Metric, Annotation, Dashboard, Alert, Trigger, Notification, JsonEncoder, JsonDecoder, NS_INTERNAL_PREFIX


class ArgusException(Exception):
    """
    An exception type that is thrown for Argus service errors.
    """
    pass


class BaseQuery(object):
    def __init__(self, baseExpr, *tailParams, **kwargs):
        self.baseExpr = baseExpr
        self.stTimeSpec = kwargs.get("stTimeSpec", None)
        self.enTimeSpec = kwargs.get("enTimeSpec", None)
        self.tailParams = tuple([t for t in tailParams if t])  # Filter None's.
        assert self.stTimeSpec or self.enTimeSpec, "One of start or end time specifications should be non-empty"

    def __str__(self):
        """
        Return string representation of the query that can be used with an Argus query. A metric query has the format:
        ``-1d:-0d:[namespace:]scope:metric[{tagk=tagv,...}]:downsample[:aggregator]``. An annotation query has the format
        ``-1d:-0d:scope:metric[{tagk=tagv,...}]:source``.
        """
        query = ":".join(str(q) for q in (self.stTimeSpec, self.enTimeSpec, self.baseExpr) + self.tailParams if q)
        return query

    def getQueryParams(self):
        return dict(expression=str(self))


class MetricQuery(BaseQuery):
    """
    This class is used to construct the query string for sending metric queries to Argus.

    >>> from argusclient.client import MetricQuery
    >>> mquery = MetricQuery("test.scope", "test.metric", "sum", tags={ "test.tag": "test.value" }, stTimeSpec="-1d", enTimeSpec="-0d", namespace="test.namespace")
    >>> print str(mquery)
    -1d:-0d:-__-test.namespace:test.scope:test.metric{test.tag=test.value}:sum
    """
    def __init__(self, scope, metric, aggregator, tags=None, namespace=None, downsampler=None, stTimeSpec=None, enTimeSpec=None):
        super(MetricQuery, self).__init__(str(Metric(scope, metric, tags=tags, namespace=namespace)), aggregator, downsampler, stTimeSpec=stTimeSpec, enTimeSpec=enTimeSpec)


class AnnotationQuery(BaseQuery):
    """
    This class is used to construct the query string for sending annotations queries to Argus.

    >>> from argusclient.client import AnnotationQuery
    >>> mquery = AnnotationQuery("test.scope", "test.metric", "test.source", tags={ "test.tag": "test.value" }, stTimeSpec="-1d", enTimeSpec="-0d")
    >>> print str(mquery)
    -1d:-0d:test.scope:test.metric{test.tag=test.value}:test.source
    """
    def __init__(self, scope, metric, source, tags=None, stTimeSpec=None, enTimeSpec=None):
        super(AnnotationQuery, self).__init__(str(Annotation(source, scope, metric, None, None, None, tags=tags)), stTimeSpec=stTimeSpec, enTimeSpec=enTimeSpec)


class BaseCollectionServiceClient(object):
    def __init__(self, query_type, obj_type, argus, query_path, coll_path):
        self.query_type = query_type
        self.obj_type = obj_type
        self.argus = argus
        self.query_path = query_path
        self.coll_path = coll_path

    def query(self, query):
        """
        Returns the list of data matching the given query.
        """
        if not query: raise ValueError("need a value for query parameter")
        if not isinstance(query, self.query_type): raise TypeError("query needs to be of type: %s" % self.query_type)
        return self.argus._request("get", self.query_path, params=query.getQueryParams())

    def add(self, data):
        """
        Sends data to the collection service.

        :return: :class:`argusclient.model.AddListResult` object with a summary of the operation.
        """
        if not data: raise ValueError("need a value for data parameter")
        if not isinstance(data, list) or not isinstance(data[0], self.obj_type): raise TypeError("data should be a list of %s objects" % self.obj_type)
        return self.argus._request("post", self.coll_path, dataObj=data)


class MetricCollectionServiceClient(BaseCollectionServiceClient):
    """
    Service class that interfaces with the Argus metrics collection endpoint.

    There is no need to instantiate this directly, as it is available as :attr:`argusclient.client.ArgusServiceClient.metrics` attribute.
    """
    def __init__(self, argus):
        super(MetricCollectionServiceClient, self).__init__(MetricQuery, Metric, argus, "metrics", "collection/metrics")


class AnnotationCollectionServiceClient(BaseCollectionServiceClient):
    """
    Service class that interfaces with the Argus annotations collection endpoint.

    There is no need to instantiate this directly, as it is available as :attr:`argusclient.client.ArgusServiceClient.annotations` attribute.
    """
    def __init__(self, argus):
        super(AnnotationCollectionServiceClient, self).__init__(AnnotationQuery, Annotation, argus, "annotations", "collection/annotations")


class BaseModelServiceClient(object):
    def __init__(self, argus, get_all_path=None):
        self.argus = argus
        self._retrieved_all = False
        self._coll = {}
        self.get_all_path = get_all_path

    def _init_all(self, coll=None):
        if not self.get_all_path:
            raise TypeError("Unsupported operation on: %s" % type(self))
        if not self._retrieved_all:
            self._coll = dict((obj.id, self._fill(obj)) for obj in coll or self.argus._request("get", self.get_all_path))
            self._retrieved_all = True

    def _fill(self, obj):
        return obj

    def get(self, id):
        """
        Return the object for the specified id. If the object is not already in the local collection, a one-time attempt would be made to load all objects from Argus.
        """
        # By default, load all, unless the id is already there.
        if id not in self._coll:
            self._init_all()
        return self._coll[id]

    def update(self, key, value):
        raise TypeError("Unsupported operation on: %s" % type(self))

    def delete(self, key):
        raise TypeError("Unsupported operation on: %s" % type(self))

    def items(self):
        """
        Returns the list of (id, object) pairs as tuples, works like the corresponding method on a dict.
        Calling this method may result in sending a request to Argus to fetch all relevant objects.
        """
        self._init_all()
        return self._coll.items()

    def keys(self):
        """
        Returns the list of ids, just like the corresponding method on a dict.
        Calling this method may result in sending a request to Argus to fetch all relevant objects.
        """
        self._init_all()
        return self._coll.items()

    def values(self):
        """
        Returns the list of objects, just like the corresponding method on a dict.
        Calling this method may result in sending a request to Argus to fetch all relevant objects.
        """
        self._init_all()
        return self._coll.values()

    def __iter__(self):
        """
        Returns an iterator of the keys, just like the corresponding method on a dict.
        Calling this method may result in sending a request to Argus to fetch all relevant objects.
        """
        self._init_all()
        return iter(self._coll)

    def __len__(self):
        """
        Returns the number of objects, just like the corresponding method on a dict.
        Calling this method may result in sending a request to Argus to fetch all relevant objects.
        """
        self._init_all()
        return len(self._coll)


class UsersServiceClient(BaseModelServiceClient):
    """
    Service class that interfaces with the Argus users endpoint.

    There is no need to instantiate this directly, as it is available as :attr:`argusclient.client.ArgusServiceClient.users` attribute.
    """
    def __init__(self, argus):
        super(UsersServiceClient, self).__init__(argus)
        self._coll_by_name = {}

    def get(self, key):
        """
        Return the User for the specified id/username. If the object is not already in the local collection, an attempt will be made to retrieve it from Argus.
        """
        if not key: raise ValueError("Need username or id")
        if isinstance(key, int) or key.isdigit():
            id = int(key)
            if id not in self._coll:
                u = self._fill(self.argus._request("get", "users/id/%s" % id))
                self._coll[id] = u
                self._coll_by_name[u.userName] = u
            return self._coll[id]
        else:
            if key not in self._coll_by_name:
                u = self._fill(self.argus._request("get", "users/username/%s" % key))
                self._coll_by_name[key] = u
                self._coll[u.id] = u
            return self._coll_by_name[key]


class NamespacesServiceClient(BaseModelServiceClient):
    """
    Service class that interfaces with the Argus namespaces endpoint.

    There is no need to instantiate this directly, as it is available as :attr:`argusclient.client.ArgusServiceClient.namespaces` attribute.
    """
    def __init__(self, argus):
        super(NamespacesServiceClient, self).__init__(argus, "namespace")

    def update(self, id, namespace):
        """
        Updates the specified namespace.

        :return: the updated :class:`argusclient.model.Namespace` with all fields populated.
        """
        if not id: raise ValueError("Need to specify an id to update namespace")
        id = int(id)
        if not namespace.argus_id: raise ValueError("Namespace needs an id to update")
        if id != namespace.argus_id: raise ValueError("Namespace id: %s doesn't match the id: %s that you are updating" % (namespace.id, id))
        self._coll[id] = self.argus._request("put", "namespace/%s" % id, dataObj=namespace)
        return self._coll[id]

    def add(self, namespace):
        """
        Adds the namespace.

        :return: the new :class:`argusclient.model.Namespace` with all fields populated.
        """
        if not isinstance(namespace, Namespace): raise TypeError("Need a Namespace object, got: %s" % type(namespace))
        if namespace.argus_id: raise ValueError("A new namespace can't have an id")
        ns = self._fill(self.argus._request("post", "namespace", dataObj=namespace))
        self._coll[ns.id] = ns
        return ns

    def update_users(self, namespaceid, *users):
        """
        Updates the namespace with the specified users.

        :return: the updated :class:`argusclient.model.Namespace` with all fields populated.
        """
        if not namespaceid: raise ValueError("Need to specify a namespaceid")
        self._coll[namespaceid] = self.argus._request("put", "namespace/%s/users" % namespaceid, dataObj=users)
        return self._coll[namespaceid]


class BaseUpdatableModelServiceClient(BaseModelServiceClient):
    def __init__(self, objType, argus, get_all_path, id_path):
        super(BaseUpdatableModelServiceClient, self).__init__(argus, get_all_path)
        self.objType = objType
        self.id_path = id_path

    def get(self, id):
        """
        Gets the item with specified id. This method retrieves it from Argus, if the object is not already available in the local collection.
        """
        if not id: raise ValueError("Need to specify an id to get item")
        id = int(id)
        if id not in self._coll:
            self._coll[id] = self._fill(self.argus._request("get", self.id_path % id))
        return self._coll[id]

    def update(self, id, obj):
        """
        Updates the specified item on Argus as well as in the local collection.

        :return: the updated object with all fields populated.
        """
        if not id: raise ValueError("Need to specify an id to update item")
        id = int(id)
        if not isinstance(obj, self.objType): raise TypeError("Need an object of type: %s" % self.objType)
        if not obj.argus_id: raise ValueError("Object needs an id to update")
        # Ensure that user doesn't accidentally copy another item.
        if id != obj.argus_id: raise ValueError("Object id: %s doesn't match the id: %s that you are updating" % (obj.id, id))
        self._coll[id] = self.argus._request("put", self.id_path % id, dataObj=obj)
        return self._coll[id]

    def delete(self, id):
        """
        Deletes the object from Argus service and also from this collection (if exists).
        """
        if not id: raise ValueError("Need to specify an id to delete item")
        id = int(id)
        self.argus._request("delete", self.id_path % id)
        if id in self._coll:
            del self._coll[id]


class DashboardsServiceClient(BaseUpdatableModelServiceClient):
    """
    Service class that interfaces with the Argus dashboards endpoint.

    There is no need to instantiate this directly, as it is available as :attr:`argusclient.client.ArgusServiceClient.dashboards` attribute.
    """
    def __init__(self, argus):
        super(DashboardsServiceClient, self).__init__(Dashboard, argus, "dashboards", "dashboards/%s")

    def add(self, dashboard):
        """
        Adds the dashboard.

        :return: the :class:`argusclient.model.Dashboard` object with all fields populated.
        """
        if not isinstance(dashboard, Dashboard): raise TypeError("Need a Dashboard object, got: %s" % type(dashboard))
        if dashboard.argus_id: raise ValueError("A new dashboard can't have an id")
        db = self._fill(self.argus._request("post", "dashboards", dataObj=dashboard))
        self._coll[db.id] = db
        return db


class AlertsServiceClient(BaseUpdatableModelServiceClient):
    """
    Service class that interfaces with the Argus alerts endpoint.

    There is no need to instantiate this directly, as it is available as :attr:`argusclient.client.ArgusServiceClient.alerts` attribute.

    .. attribute:: triggers

         :class:`argusclient.client.AlertTriggersServiceClient`

         Interfaces with the Argus alert triggers endpoint.

    .. attribute:: notifications

         :class:`argusclient.client.AlertNotificationsServiceClient`

         Interfaces with the Argus alert notifications endpoint.

    """
    def __init__(self, argus):
        super(AlertsServiceClient, self).__init__(Alert, argus, "alerts", "alerts/%s")

    def _fill(self, alert):
        alert._triggers = AlertTriggersServiceClient(self.argus, alert)
        alert._notifications = AlertNotificationsServiceClient(self.argus, alert)
        return alert

    def add(self, alert):
        """
        Adds the alert.

        :return: the :class:`argusclient.model.Alert` object with all fields populated.
        """
        if not isinstance(alert, Alert): raise TypeError("Need a Alert object, got: %s" % type(alert))
        if alert.argus_id: raise ValueError("A new alert can't have an id")
        alertobj = self._fill(self.argus._request("post", "alerts", dataObj=alert))
        self._coll[alertobj.id] = alertobj
        if alert.trigger:
            alertobj.trigger = alertobj.triggers.add(alert.trigger)
        if alert.notification:
            alertobj.notification = alertobj.notifications.add(alert.notification)
        if alert.trigger and alert.notification:
            self.argus.alerts.add_notification_trigger(alertobj.id, alertobj.notification.id, alertobj.trigger.id)
            alertobj.notification.triggersIds = [alertobj.trigger.id]
            alertobj.trigger.notificationsIds = [alertobj.notification.id]
        return alertobj

    def get_notification_triggers(self, alertid, notificationid):
        """
        Return all triggers that are associated with the specified notification as a list.

        :return: the :class:`list` of :class:`argusclient.model.Trigger` object with all fields populated.
        """
        if not alertid: raise ValueError("Need to specify an alertid")
        if not notificationid: raise ValueError("Need to specify a notificationid")
        # TODO: Update self._coll
        return self.argus._request("get", "alerts/%s/notifications/%s/triggers" % (alertid, notificationid))

    def get_notification_trigger(self, alertid, notificationid, triggerid):
        """
        Returns the trigger only if it is associated with the specified notification.

        :return: the :class:`argusclient.model.Trigger` object with all fields populated.
        """
        if not alertid: raise ValueError("Need to specify an alertid")
        if not notificationid: raise ValueError("Need to specify a notificationid")
        if not triggerid: raise ValueError("Need to specify a triggerid")
        # TODO: Update self._coll
        return self.argus._request("get", "alerts/%s/notifications/%s/triggers/%s" % (alertid, notificationid, triggerid))

    def add_notification_trigger(self, alertid, notificationid, triggerid):
        """
        Associates the trigger with the specified notification.

        :return: the :class:`argusclient.model.Trigger` with all fields populated.
        """
        if not alertid: raise ValueError("Need to specify an alertid")
        if not notificationid: raise ValueError("Need to specify a notificationid")
        if not triggerid: raise ValueError("Need to specify a triggerid")
        # TODO: Update self._coll
        return self.argus._request("post", "alerts/%s/notifications/%s/triggers/%s" % (alertid, notificationid, triggerid))

    def delete_notification_trigger(self, alertid, notificationid, triggerid):
        """
        Disassociates the trigger with the specified notification. This method has no return value.
        """
        if not alertid: raise ValueError("Need to specify an alertid")
        if not notificationid: raise ValueError("Need to specify a notificationid")
        if not triggerid: raise ValueError("Need to specify a triggerid")
        # TODO: Update self._coll
        self.argus._request("delete", "alerts/%s/notifications/%s/triggers/%s" % (alertid, notificationid, triggerid))


class AlertTriggersServiceClient(BaseUpdatableModelServiceClient):
    """
    Service class that interfaces with the Argus alert triggers endpoint.

    There is no need to instantiate this directly, as it is available as :attr:`argusclient.client.AlertsServiceClient.triggers` attribute.
    """

    def __init__(self, argus, alert):
        assert alert, "Expected an alert at this point"
        assert alert.id, "Alert expected to have an id at this point"
        super(AlertTriggersServiceClient, self).__init__(Trigger, argus, "alerts/%s/triggers" % alert.id, "alerts/%s/triggers/%%s" % alert.id)
        self.alert = alert

    def add(self, trigger):
        """
        Adds the trigger to this alert.

        :return: the added :class:`argusclient.model.Trigger` with all fields populated.
        """
        if not isinstance(trigger, Trigger): raise TypeError("Need a Trigger object, got: %s" % type(trigger))
        if trigger.argus_id: raise ValueError("A new Trigger can't have an id")
        triggers = self.argus._request("post", "alerts/%s/triggers" % self.alert.id, dataObj=trigger)
        self._init_all(triggers)
        self.alert.triggerIds = triggers
        try:
            return next(t for t in triggers if t.name == trigger.name)
        except StopIteration:
            raise ArgusException("This is unexpected... trigger: %s not found after successfully adding it" % trigger.name)


class AlertNotificationsServiceClient(BaseUpdatableModelServiceClient):
    """
    Service class that interfaces with the Argus alert notifications endpoint.

    There is no need to instantiate this directly, as it is available as :attr:`argusclient.client.AlertsServiceClient.notifications` attribute.
    """
    def __init__(self, argus, alert):
        assert alert, "Expected an alert at this point"
        assert alert.id, "Alert expected to have an id at this point"
        super(AlertNotificationsServiceClient, self).__init__(Notification, argus, "alerts/%s/notifications" % alert.id, "alerts/%s/notifications/%%s" % alert.id)
        self.alert = alert

    def add(self, notification):
        """
        Adds the notification to this alert.

        :return: the added :class:`argusclient.model.Notification` with all fields populated.
        """
        if not isinstance(notification, Notification): raise TypeError("Need a Notification object, got: %s" % type(notification))
        if notification.argus_id: raise ValueError("A new Notification can't have an id")
        notifications = self.argus._request("post", "alerts/%s/notifications" % self.alert.id, dataObj=notification)
        self._init_all(notifications)
        self.alert.notificationIds = notifications
        try:
            return next(n for n in notifications if n.name == notification.name)
        except StopIteration:
            raise ArgusException("This is unexpected... notification: %s not found after successfully adding it" % notification.name)


class ArgusServiceClient(object):
    """
    This is the main class to interact with the Argus webservice.

    An instance of this class comes with the below attributes to interact with the different Argus endpoints:

    .. attribute:: metrics

         :class:`argusclient.client.MetricCollectionServiceClient`

         Interfaces with the Argus metrics collection endpoint.

    .. attribute:: annotations

         :class:`argusclient.client.AnnotationCollectionServiceClient`

         Interfaces with the Argus annotations collection endpoint.

    .. attribute:: dashboards

         :class:`argusclient.client.DashboardsServiceClient`

         Interfaces with the Argus dashboards endpoint.

    .. attribute:: users

         :class:`argusclient.client.UsersServiceClient`

         Interfaces with the Argus users endpoint.

    .. attribute:: namespaces

         :class:`argusclient.client.NamespacesServiceClient`

         Interfaces with the Argus namespaces endpoint.

    .. attribute:: alerts

         :class:`argusclient.client.AlertsServiceClient`

         Interfaces with the Argus alerts endpoint.

    """

    def __init__(self, user, password, endpoint, timeout=(10, 60)):
        """
        Creates a new client object to interface with the Argus RESTful API.

        :param user: The username for Argus account.
        :type user: str
        :param password: The password for Argus account.
        :type password: str
        """
        self.user = user
        self.password = password
        self.endpoint = endpoint
        self.timeout = timeout

        if not self.endpoint:
            raise ValueError("Need a valid Argus endpoint URL")

        self.metrics = MetricCollectionServiceClient(self)
        self.annotations = AnnotationCollectionServiceClient(self)
        self.dashboards = DashboardsServiceClient(self)
        self.users = UsersServiceClient(self)
        self.namespaces = NamespacesServiceClient(self)
        self.alerts = AlertsServiceClient(self)
        self.conn = requests.Session()

    def login(self):
        """
        Logs into the Argus service and establishes a session.

        :return: the :class:`argusclient.model.User` object.
        """
        return self._request("post", "auth/login", dataObj=dict(username=self.user, password=self.password))

    def logout(self):
        """
        Logs out of the Argus service and destroys the session.
        """
        self._request("get", "auth/logout")

    def _request(self, method, path, params=None, dataObj=None, encCls=JsonEncoder, decCls=JsonDecoder):
        """
        This is the low level method that all

        :param method: The HTTP method name as a string. Some valid names are: `get`, `post`, `put` and `delete`.
        :type method: str
        :param path: The Argus path on which the request needs to be made, e.g. `/auth/login`
        :type path: str
        """
        url = os.path.join(self.endpoint, path)
        req_method = getattr(self.conn, method)
        data = dataObj and json.dumps(dataObj, cls=encCls) or None
        logging.debug("%s request with params: %s data length %s on: %s", method.upper(), params, data and len(data) or 0, url) # Mainly for the sake of data length
        # Argus seems to recognized "Accept" header for "application/json" and "application/ms-excel", but the former is the default.
        resp = req_method(url, data=data, params=params,
                          headers={"Content-Type": "application/json"},
                          timeout=self.timeout)
        res = check_success(resp, decCls)
        return res


def check_success(resp, decCls):
    if resp.status_code == httplib.OK:
        # DELETE has no response.
        if not resp.text:
            return None
        res = resp.json(cls=decCls)
        if isinstance(res, dict) and "status" in res and res["status"] != 200:
            raise ArgusException(resp.text)
        return res
    elif resp.status_code == httplib.NOT_FOUND:
        raise ArgusException("Object not found at endpoint: %s message: %s" % (resp.request.url, resp.text))
    else:
        # TODO handle this differently, as this is typically a more severe exception (see W-2830904)
        raise ArgusException(resp.text)
