"""
This modules contains various client classes to interact with the Argus RESTful webservice endpoints.
The implementation is based on API documentation from ``/help`` on various endpoints
and `web service reference <https://github.com/SalesforceEng/Argus/wiki/Web%20Service%20API>`__.
"""

#
# Copyright (c) 2016, salesforce.com, inc.
# All rights reserved.
# Licensed under the BSD 3-Clause license. 
# For full license text, see LICENSE.txt file in the repo root  or https://opensource.org/licenses/BSD-3-Clause
#
import unicodedata
from collections import Mapping

import requests
import json
import os
import logging
import collections
try:
    import http.client as httplib  # Python 3
except ImportError:
    import httplib                 # Python 2
from functools import wraps

from .model import Namespace, Metric, Annotation, Dashboard, Alert, Trigger, Notification, JsonEncoder, JsonDecoder, \
    Permission

REQ_METHOD = "req_method"
REQ_PATH = "req_path"
REQ_PARAMS = "req_params"
REQ_BODY = "req_body"

class ArgusException(Exception):
    """
    An exception type that is thrown for Argus service errors.
    """
    pass

class ArgusAuthException(ArgusException):
    """
    An exception type that is thrown for Argus authentication errors.
    """
    pass

class ArgusObjectNotFoundException(ArgusException):
    """
    An exception type that is thrown for Argus object not found errors.
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
        ``-1d:-0d:scope:metric[{tagk=tagv,...}]:downsample[:aggregator][:namespace]``. An annotation query has the format
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
    -1d:-0d:test.scope:test.metric{test.tag=test.value}:sum:test.namespace
    """
    def __init__(self, scope, metric, aggregator, tags=None, namespace=None, downsampler=None, stTimeSpec=None, enTimeSpec=None):
        # NOTE: Namespace no longer goes into the metric expression, so we pass it down as a tail parameter.
        super(MetricQuery, self).__init__(str(Metric(scope, metric, tags=tags)), aggregator, downsampler, namespace, stTimeSpec=stTimeSpec, enTimeSpec=enTimeSpec)


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
    def __init__(self, argus, get_all_req_opts=None):
        """
        :param get_all_req_opts: Dict holding request details for a 'get-all alerts/dashboards/etc' request.
                                Currently supported fields are REQ_METHOD, REQ_PATH, REQ_PARAMS, and REQ_BODY.
        :type get_all_req_opts: dict
        """
        self.argus = argus
        self._retrieved_all = False
        self._coll = {}
        self.get_all_req_opts = get_all_req_opts or {}

    def _init_all(self, coll=None):
        if not self.get_all_req_opts.get(REQ_PATH):
            raise TypeError("Unsupported operation on: %s" % type(self))
        if not self._retrieved_all:
            self._coll = dict((obj.argus_id, self._fill(obj))
                              for obj in (coll or self.argus._request(self.get_all_req_opts.get(REQ_METHOD, "get"),
                                                                       self.get_all_req_opts.get(REQ_PATH, None),
                                                                       params=self.get_all_req_opts.get(REQ_PARAMS, None),
                                                                       dataObj=self.get_all_req_opts.get(REQ_BODY, None))))
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

    def __getitem__(self, id):
        return self.get(id)

    def __setitem__(self, key, value):
        raise ValueError("You can't modify this list directly, use the add(), delete() and update() methods instead")

    def __delitem__(self, key):
        raise ValueError("You can't modify this list directly, use the add(), delete() and update() methods instead")

    def __contains__(self, key):
        self._init_all()
        return key in self._coll


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
        super(NamespacesServiceClient, self).__init__(argus, get_all_req_opts={REQ_PATH: "namespace"})

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
    def __init__(self, objType, argus, id_path, get_all_req_opts=None):
        super(BaseUpdatableModelServiceClient, self).__init__(argus, get_all_req_opts=get_all_req_opts)
        self.objType = objType
        self.id_path = id_path

    def get(self, id):
        """
        Gets the item with specified id. This method retrieves it from Argus, if the object is not already available in the local collection.
        """
        if id is None: raise ValueError("Need to specify an id to get item")
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
    def __init__(self, argus, get_all_req_opts=None):
        """
        :param get_all_req_opts: See BaseModelServiceClient.__init__() for description.
        """
        if not get_all_req_opts:
            get_all_req_opts = {}
        get_all_req_opts.setdefault(REQ_PATH, "dashboards")
        super(DashboardsServiceClient, self).__init__(Dashboard, argus, id_path="dashboards/%s",
                                                      get_all_req_opts=get_all_req_opts)

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

    def get_user_dashboard(self, ownerName, dashboardName, shared=True):
        """
        Looks up a dashboard with its name and owner. Returns `None` if not found.

        :return: the :class:`argusclient.model.Dashboard` object with all fields populated.
        """
        assert dashboardName, "Expected a dashboard name"
        assert ownerName, "Expected a owner name"
        dashboards = self.argus._request("get", "dashboards", params=dict(dashboardName=dashboardName, owner=ownerName, shared=shared))
        if not dashboards:
            return None
        else:
            assert len(dashboards) == 1, "Expected a single dashboard as a result, but got: %s" % len(dashboards)
            return dashboards[0]

    def get_user_dashboards(self, ownerName=None, shared=True, limit=None, version=None):
        """
        Gets dashboards owned by ownerName.
        If ownerName is not passed in, the username used during login is used.

        :return: a list of :class:`argusclient.model.Dashboard` objects with all fields populated.
        """
        return self.argus._request("get", "dashboards", params=dict(owner=ownerName, shared=shared, limit=limit, version=version))

class PermissionsServiceClient(BaseUpdatableModelServiceClient):
    """
    Service class that interfaces with the Argus permissions endpoint.

    There is no need to instantiate this directly, as it is available as :attr:`argusclient.client.ArgusServiceClient.permissions` attribute.
    """
    def __init__(self, argus, get_all_req_opts=None):
        """
        :param get_all_req_opts: See BaseModelServiceClient.__init__() for description.
        """
        if not get_all_req_opts:
            get_all_req_opts = {}
        get_all_req_opts.setdefault(REQ_METHOD, "get")
        get_all_req_opts[REQ_PATH] = "permission/" + get_all_req_opts.get(REQ_PATH, "")
        super(PermissionsServiceClient, self).__init__(Permission, argus, id_path="permission/%s",
                                                       get_all_req_opts=get_all_req_opts)

    def _init_all(self, coll=None):
        if not self.get_all_req_opts.get(REQ_PATH):
            raise TypeError("Unsupported operation on: %s" % type(self))
        if not self._retrieved_all:
            resp = convert(self.argus._request(self.get_all_req_opts.get(REQ_METHOD, "get"),
                                                    self.get_all_req_opts.get(REQ_PATH, None),
                                                    params=self.get_all_req_opts.get(REQ_PARAMS, None),
                                                    dataObj=self.get_all_req_opts.get(REQ_BODY, None)))
            for id, perms in resp.items():
                self._coll[id] = perms
            self._retrieved_all = True

    def get_permissions_for_entities(self, entity_ids):
        """
        Gets permissions that are associated with the given entity id's.

        :return: a dict of entity id's mapped to a list of :class:`argusclient.model.Permission` objects
        """
        entityIds = []
        for entity_id in entity_ids:
            if entity_id not in self._coll:
                entityIds.append(entity_id)

        if entityIds:
            response = convert(self.argus._request("post", "permission/entityIds", dataObj=entityIds))
            for id, perms in response.items():
                self._coll[id] = perms
        return self._coll


    def add(self, entity_id, permission):
        """
        Associates a permission with an alert
        :return: the :class:`argusclient.model.Permission` object with the entityId field set.
        """
        if not isinstance(permission, Permission):
            raise TypeError("Need a Permission object, got: %s" % type(permission))
        if permission.argus_id: raise ValueError("A new permission can't have an entity id associated with it")
        updated_permission = self.argus._request("post", "permission/%s" % entity_id, dataObj=permission)

        self._coll[updated_permission.entityId] = updated_permission

        if updated_permission.entityId != entity_id:
            raise ArgusException("This is unexpected... permission: %s not associated with entity after successfully"
                                 " adding it" % permission)
        return updated_permission

    def delete(self, entity_id, permission):
        if not isinstance(permission, Permission):
            raise TypeError("Need a Permission object, got: %s" % type(permission))
        if permission.type == "user" and permission.permissionIds == []:
            raise ValueError("A user permission needs to have the permission that needs to be revoked")
        updated_permission = self.argus._request("delete", "permission/%s" % entity_id, dataObj=permission)
        if updated_permission.entityId in self._coll:
            del self._coll[updated_permission.entity_id]

class GroupPermissionServiceClient(BaseUpdatableModelServiceClient):
    """
    Service class that interfaces with the Argus alert Group Permissions endpoint.
    """
    def __init__(self, argus):
        super(GroupPermissionServiceClient, self).__init__([], argus, "grouppermission", "grouppermission/getvalidgroupkeys")

    def get_groups_with_valid_permissions(self, group_ids):
        """
        Checks if the group ids specified have valid permissions
        :return: the a list of strings representing group id's that have valid permissions.
        """

        groups_with_valid_permissions = self.argus._request("get", "grouppermission/getvalidgroupkeys",
                                                            params=dict(groupIds=group_ids))
        return groups_with_valid_permissions

def convert(input):
    if isinstance(input, Mapping):
        return {convert(key): convert(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [convert(element) for element in input]
    elif isinstance(input, basestring):
        ret = str(input)
        if ret.isdigit():
            ret = int(ret)
        return ret
    else:
        return input


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
    def __init__(self, argus, get_all_req_opts=None):
        """
        :param get_all_req_opts: See BaseModelServiceClient.__init__() for description.
        """
        if not get_all_req_opts:
            get_all_req_opts = {}
        get_all_req_opts[REQ_PATH] = "alerts/" + get_all_req_opts.get(REQ_PATH, "")
        super(AlertsServiceClient, self).__init__(Alert, argus, id_path="alerts/%s", get_all_req_opts=get_all_req_opts)

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

    def update(self, id, alert):
        """
        Updates the specified alert.

        :return: the updated :class:`argusclient.model.Alert` object with all fields populated.
        """
        return self._fill(super(AlertsServiceClient, self).update(id, alert))

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

    def get_user_alert(self, ownerName, alertName, shared=True):
        """
        Looks up an alert with its name and owner. Returns `None` if not found.

        :return: the :class:`argusclient.model.Alert` object with all fields populated.
        """
        assert alertName, "Expected an alert name"
        assert ownerName, "Expected a owner name"
        alerts = self.argus._request("get", "alerts/meta", params=dict(alertname=alertName, ownername=ownerName, shared=shared))
        if not alerts:
            return None
        else:
            assert len(alerts) == 1, "Expected a single alert as a result, but got: %s" % [a.name for a in alerts]
            return alerts[0]

    def get_alerts_allinfo(self, ownerName=None, alertNameContains=None, shared=False, limit=None):
        """
        If ownerName is not passed in, the username used during login is used.
        Calls the GET /alerts/allinfo endpoint.
        Returns the list of alerts (including associated notifications and triggers) created by the user.

        :return: the list of :class:`argusclient.model.Alert` objects, with all fields populated, including triggers and notifications
        """
        return self.argus._request("get", "alerts/allinfo", params=dict(ownername=ownerName, alertNameContains=alertNameContains, shared=shared, limit=limit))

    '''
    Functions to enable support for composite alerts
    '''

    def get_composite_alert_children(self, comp_alert_id):
        """
        Get list of child alerts for a composite alert 
        :param comp_alert_id: ID of an argus composite alert
        :type comp_alert_id: integer
        :return:  list of :class:`argusclient.model.Alert` object with all fields populated.
        """

        if not comp_alert_id: raise ValueError("Need to specify comp_alert_id")
        if not isinstance(comp_alert_id, int): raise TypeError("Need an Alert ID, got: %s" % type(comp_alert_id))

        uri_path = "alerts/{}/children".format(comp_alert_id)
        child_alerts = self.argus._request("get", uri_path)
        child_alerts = [self._fill(child_alert) for child_alert in child_alerts]
        return child_alerts 

    def get_composite_alert_children_info(self, comp_alert_id):
        """
        Get information for all children (child alerts + triggers associated with them) of a composite alert

        :param comp_alert_id: ID of an argus composite alert
        :type comp_alert_id: integer
        :return:  list of child alerts information (alertid, alertname, triggerids, triggernames etc)
        """

        if not comp_alert_id: raise ValueError("Need to specify comp_alert_id")
        if not isinstance(comp_alert_id, int): raise TypeError("Need an Alert ID, got: %s" % type(comp_alert_id))

        uri_path = "alerts/{}/children/info".format(comp_alert_id)
        return self.argus._request("get", uri_path)


    def add_child_alert_to_composite_alert(self, comp_alert_id, alert):
        """
        Add child alert to a composite alert

        :param comp_alert_id: ID of a composite alert
        :type comp_alert_id: Integer

        :param alert: alert definition
        :type alert: class:`argusclient.model.Alert` object

        :return: newly created child  alert object  of type class:`argusclient.model.Alert`
        """
        if not comp_alert_id: raise ValueError("Need to specify a composite alert id")
        if not alert: raise ValueError("Need to specify an Alert object")
        if not isinstance(comp_alert_id, int): raise TypeError("Need an Alert ID, got: %s" % type(comp_alert_id))
        if not isinstance(alert, Alert): raise TypeError("Need an Alert object, got: %s" % type(alert))

        uri_path = "alerts/{}/children".format(comp_alert_id)
        alert_obj = self._fill(self.argus._request("post", uri_path, dataObj=alert))
        self._coll[alert_obj.id] = alert_obj
        return alert_obj


    def delete_child_alert_from_composite_alert(self, comp_alert_id, child_alert_id):
        """
         Delete a child alert from a composite alert

        :param comp_alert_id: ID of a composite alert
        :type comp_alert_id: Integer

        :param child_alert_id: ID of a child alert
        :type child_alert_id: Integer
        """
        if not comp_alert_id: raise ValueError("Need to specify a composite alert id")
        if not child_alert_id: raise ValueError("Need to specify a child alert id")
        if not isinstance(comp_alert_id, int): raise TypeError("Need a composite Alert ID, got: %s" % type(comp_alert_id))
        if not isinstance(child_alert_id, int): raise TypeError("Need an Alert ID, got: %s" % type(child_alert_id))

        uri_path = "alerts/{}/children/{}".format(comp_alert_id, child_alert_id)
        if child_alert_id in self._coll:
            del self._coll[child_alert_id]
        return self.argus._request("delete", uri_path)


class AlertTriggersServiceClient(BaseUpdatableModelServiceClient):
    """
    Service class that interfaces with the Argus alert triggers endpoint.

    There is no need to instantiate this directly, as it is available as :attr:`argusclient.client.AlertsServiceClient.triggers` attribute.
    """

    def __init__(self, argus, alert):
        assert alert, "Expected an alert at this point"
        assert alert.id, "Alert expected to have an id at this point"
        super(AlertTriggersServiceClient, self).__init__(Trigger, argus, id_path="alerts/%s/triggers/%%s" % alert.id,
                                                         get_all_req_opts={REQ_PATH: "alerts/%s/triggers" % alert.id})
        self.alert = alert
        if alert.triggers:
            self._init_all(alert.triggers)

    def add(self, trigger):
        """
        Adds the trigger to this alert.

        :return: the added :class:`argusclient.model.Trigger` with all fields populated.
        """
        if not isinstance(trigger, Trigger): raise TypeError("Need a Trigger object, got: %s" % type(trigger))
        if trigger.argus_id: raise ValueError("A new Trigger can't have an id")
        triggers = self.argus._request("post", "alerts/%s/triggers" % self.alert.id, dataObj=trigger)
        self._init_all(triggers)
        self.alert.triggerIds = [t.argus_id for t in triggers]
        try:
            return next(t for t in triggers if t.name == trigger.name)
        except StopIteration:
            raise ArgusException("This is unexpected... trigger: %s not found after successfully adding it" % trigger.name)

    def delete(self, id):
        super(AlertTriggersServiceClient, self).delete(id)
        self.alert.triggerIds = list(self._coll.keys())


class AlertNotificationsServiceClient(BaseUpdatableModelServiceClient):
    """
    Service class that interfaces with the Argus alert notifications endpoint.

    There is no need to instantiate this directly, as it is available as :attr:`argusclient.client.AlertsServiceClient.notifications` attribute.
    """
    def __init__(self, argus, alert):
        assert alert, "Expected an alert at this point"
        assert alert.id, "Alert expected to have an id at this point"
        super(AlertNotificationsServiceClient, self).__init__(Notification, argus, id_path="alerts/%s/notifications/%%s" % alert.id,
                                                              get_all_req_opts={REQ_PATH: "alerts/%s/notifications" % alert.id})
        self.alert = alert
        if alert.notifications:
            self._init_all(alert.notifications)

    def add(self, notification):
        """
        Adds the notification to this alert.

        :return: the added :class:`argusclient.model.Notification` with all fields populated.
        """
        if not isinstance(notification, Notification): raise TypeError("Need a Notification object, got: %s" % type(notification))
        if notification.argus_id: raise ValueError("A new Notification can't have an id")
        notifications = self.argus._request("post", "alerts/%s/notifications" % self.alert.id, dataObj=notification)
        self._init_all(notifications)
        self.alert.notificationIds = [n.argus_id for n in notifications]
        try:
            return next(n for n in notifications if n.name == notification.name)
        except StopIteration:
            raise ArgusException("This is unexpected... notification: %s not found after successfully adding it" % notification.name)

    def delete(self, id):
        super(AlertNotificationsServiceClient, self).delete(id)
        self.alert.notificationIds = list(self._coll.keys())


def retry_auth(f):
    @wraps(f)
    def with_retry(*args, **kwargs):
        try_cnt = 0
        while True:
            try_cnt += 1
            try:
                return f(*args, **kwargs)
            except ArgusAuthException as ex:
                if try_cnt >= 2:
                    raise
                else:
                    logging.debug("Got auth exception, but will retry", exc_info=True)

    return with_retry


def auto_auth(f):
    @wraps(f)
    def with_auth_token(*args, **kwargs):
        argus = args[0]
        if not argus.accessToken and argus.refreshToken:
            try:
                res = argus._request_no_auth("post",
                                     "v2/auth/token/refresh",
                                     dataObj=dict(refreshToken=argus.refreshToken))
                argus.accessToken = res["accessToken"]
            except ArgusAuthException:
                if argus.password:
                    logging.debug("Token refresh failed, will attempt a fresh login", exc_info=True)
                else:
                    raise
        if not argus.accessToken and argus.password:
            argus.refreshToken = None
            res = argus._request_no_auth("post",
                                 "v2/auth/login",
                                 dataObj=dict(username=argus.user, password=argus.password))
            argus.refreshToken, argus.accessToken = res["refreshToken"], res["accessToken"]

        try:
            return f(*args, **kwargs)
        except ArgusAuthException:
            argus.accessToken = None
            raise

    return with_auth_token


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

    .. attribute:: permissions

         :class:`argusclient.client.PermissionsServiceClient`

         Interfaces with the Argus permissions endpoint.

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

    def __init__(self, user, password, endpoint, timeout=(10, 120), refreshToken=None, accessToken=None):
        """
        Creates a new client object to interface with the Argus RESTful API.

        :param user: The username for Argus account.
        :type user: str
        :param password: The password for Argus account. This is optional, unless a valid ``refreshToken`` or ``accessToken`` is specified. The password will be used to generate a ``refreshToken`` and ``accessToken``.
        :type password: str
        :param endpoint: The Argus endpoint to be used
        :type endpoint: str
        :param timeout: The timeout(s) to be applied for connection and read. This is passed as is to the calls to ``requests``. For more information, see `Requests Timeout <http://docs.python-requests.org/en/latest/user/advanced/#timeouts>`__
        :type timeout: int or float or tuple
        :param refreshToken: A token that can be used to generate an ``accessToken`` as and when needed. When the ``refreshToken`` expires, the ``password`` (if specified) will be used to generate a new token.
        :type refreshToken: str
        :param accessToken: A token that can be used to authenticate with Argus. If a ``refreshToken`` or ``password`` is specified, the ``accessToken`` will be refreshed as and when it is needed.
        :type refreshToken: str
        """
        if not user:
            raise ValueError("A valid user must be specified")
        if not any((password, refreshToken, accessToken)):
            raise ValueError("One of these parameters must be specified: (password, refreshToken, accessToken)")
        if not endpoint:
            raise ValueError("Need a valid Argus endpoint URL")

        self.user = user
        self.password = password
        self.endpoint = endpoint
        self.timeout = timeout
        self.refreshToken = refreshToken
        self.accessToken = accessToken

        self.metrics = MetricCollectionServiceClient(self)
        self.annotations = AnnotationCollectionServiceClient(self)
        self.dashboards = DashboardsServiceClient(self)
        self.permissions = PermissionsServiceClient(self)
        self.users = UsersServiceClient(self)
        self.namespaces = NamespacesServiceClient(self)
        self.alerts = AlertsServiceClient(self)
        self.group_permissions = GroupPermissionServiceClient(self)
        self.conn = requests.Session()

    def login(self):
        """
        Logs into the Argus service and establishes required tokens.
        The call to ``login()`` is optional, as a session will be established the first time it is required.

        :return: the :class:`argusclient.model.User` object.
        """
        # Simply make a request and let it handle the authentication implicitly.
        return self._request("get", "users/username/{user}".format(user=self.user))

    def logout(self):
        """
        Logs out of the Argus service and destroys the session.
        """
        # The new V2 auth doesn't support a logout, so just clear the tokens.
        #self._request("get", "auth/logout")
        self.refreshToken = self.accessToken = None

    @retry_auth
    @auto_auth
    def _request(self, method, path, params=None, dataObj=None, encCls=JsonEncoder, decCls=JsonDecoder):
        """
        This is the low level method used to make the underlying Argus requests. This ensures that all requests are fully authenticated.

        :param method: The HTTP method name as a string. Some valid names are: `get`, `post`, `put` and `delete`.
        :type method: str
        :param path: The Argus path on which the request needs to be made, e.g. `/auth/login`
        :type path: str
        """
        return self._request_no_auth(method, path, params, dataObj, encCls, decCls)

    def _request_no_auth(self, method, path, params=None, dataObj=None, encCls=JsonEncoder, decCls=JsonDecoder):
        """
        This is the low level method used to make the underlying Argus requests. It is preferable to use :meth:`_request` method instead.

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
        headers = {"Content-Type": "application/json"}
        if self.accessToken:
            headers["Authorization"] = "Bearer "+self.accessToken

        # print "url "+ str(url) + " data "+ str(data) + "params "+ str(params) + "headers "+ str(headers)
        resp = req_method(url, data=data, params=params,
                          headers=headers,
                          timeout=self.timeout,
                          verify=False)
        # print resp
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
        raise ArgusObjectNotFoundException("Object not found at endpoint: {} message: {}".format(resp.url, resp.text))
    elif resp.status_code == httplib.UNAUTHORIZED:
        raise ArgusAuthException("Failed to authenticate at endpoint: %s message: %s" % (resp.url, resp.text))
    else:
        # TODO handle this differently, as this is typically a more severe exception (see W-2830904)
        raise ArgusException(resp.text)
