#
# Copyright (c) 2016, salesforce.com, inc.
# All rights reserved.
# Licensed under the BSD 3-Clause license.
# For full license text, see LICENSE.txt file in the repo root  or https://opensource.org/licenses/BSD-3-Clause
#

import requests
import json
import os
import logging

from argusclient.model import JsonEncoder, JsonDecoder

try:
    import http.client as httplib  # Python 3
except ImportError:
    import httplib                 # Python 2
from functools import wraps

def auto_auth(func):
    @wraps(func)
    def with_auth_token(*args, **kwargs):
        client = args[0]

        # Login
        if not client.accessToken:
            res = client._request_no_auth("post", client.login_path)
            # Store access token
            client.accessToken = res["access_token"]

        try:
            # Now ready to call function
            return func(*args, **kwargs)
        except Exception:
            client.accessToken = None
            raise
    return with_auth_token

def check_success(resp, decCls):
    if resp.status_code == httplib.OK:
        # DELETE has no response.
        if not resp.text:
            return None
        res = resp.json(cls=decCls)
        if isinstance(res, dict) and "status" in res and res["status"] != 200:
            raise Exception(resp.text)
        return res
    elif resp.status_code == httplib.UNAUTHORIZED:
        raise Exception("Failed to authenticate at endpoint: %s message: %s" % (resp.url, resp.text))
    else:
        # TODO handle this differently, as this is typically a more severe exception (see W-2830904)
        raise Exception(resp.text)


class MonexClient(object):
    """
    This is the main class to interact with the Monex webservice.
    """

    def __init__(self, out, endpoint, login_path, timeout=(10, 120), accessToken=None, dry=False):
        """
        Creates a new client object to interface with the Monex RESTful API.

        :param timeout: The timeout(s) to be applied for connection and read. This is passed as is to the calls to ``requests``. For more information, see `Requests Timeout <http://docs.python-requests.org/en/latest/user/advanced/#timeouts>`__
        :type timeout: int or float or tuple
        """
        if not endpoint:
            raise ValueError("Need a valid endpoint URL")
        self.out = out
        self.endpoint = endpoint
        self.login_path = login_path
        self.timeout = timeout
        self.dry = dry
        self.accessToken = accessToken
        self.conn = requests.Session()

    def login(self):
        """
        Logs into the monex service and retrieves token.
        The call to ``login()`` is optional, as a session will be established the first time it is required.
        :return:  access token
        """
        path = self.login_path or "auth/1.0/token"
        resp = self._request_no_auth("post", path)
        self.accessToken = resp['access_token']

    def _request_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.accessToken:
            headers["Authorization"] = "Bearer " + self.accessToken
        return headers

    def get_group(self, group_id):
        url = "{}ext/groups/{}/usersInfo".format(self.endpoint, group_id)
        resp = requests.get(url, verify=False, headers=self._request_headers())
        self.out(v='Found userinfo for group {} : {}'.format(group_id, resp.json()))
        return resp.json()

    def delete_group(self, group_id):
        if self.dry:
            self.out(v='Deleted group {}'.format(group_id))
            return None

        url = "{}ext/groups/{}".format(self.endpoint, group_id)
        resp = requests.delete(url, verify=False, headers=self._request_headers())
        self.out(v='Deleted group {}'.format(group_id))
        return resp.json()

    def create_group(self, group_name, group_description):
        if self.dry:
            self.out(v='Created group name: {}'.format(group_name))
            return {'guid': '00000000-0000-0000-0000-000000000123'}

        url = "{}ext/groups/create".format(self.endpoint)
        data = {'name': group_name,
                'description': group_description,
                'state': 'ACTIVE'}

        resp = requests.post(url, verify=False, headers=self._request_headers(), data=json.dumps(data))
        group = resp.json()
        self.out(v='Created group name: {}, guid: {}'.format(group_name, group['guid']))
        return group

    def remove_user_from_group(self, group_id, user_id):
        if self.dry:
            self.out(v='Removed user {} from group {} .'.format(user_id, group_id))
            return None

        url = "{}ext/groups/{}/users/{}".format(self.endpoint, group_id, user_id)
        resp = requests.delete(url, verify=False, headers=self._request_headers())
        self.out(v='Removed user {} from group {} .'.format(user_id, group_id))
        return resp.json()

    def add_user_to_group(self, group_id, user_id):
        if self.dry:
            self.out(v='Added user {} to group {} .'.format(user_id, group_id))
            return None

        url = "{}ext/groups/{}/users/{}".format(self.endpoint, group_id, user_id)
        data = {'state': 'ACTIVE'}
        resp = requests.post(url, verify=False, headers=self._request_headers(), data=json.dumps(data))
        self.out(v='Added user {} to group {} .'.format(user_id, group_id))
        return resp.json()

    def modify_user_permission_in_group(self, old_permission, new_permission, group_id, user_id):
        if self.dry:
            self.out(v='Modified user {} in group {}. Original permission {}, new permission {} .'.format(user_id, group_id, old_permission, new_permission))
            return None

        url = "{}ext/resourcePermissions/{}".format(self.endpoint, new_permission)
        data = {'resourceType': 'GROUP',
                'resourceId': group_id,
                'userGuid': user_id,
                'permissionId': old_permission}
        resp = requests.patch(url, verify=False, headers=self._request_headers(), data=json.dumps(data))

        self.out(v='Modified user {} in group {}. Old permission {}, new permission {} .'.format(user_id, group_id, old_permission, new_permission))
        return resp.json()

    def find_user_by_username(self, username):
        url = "{}users/search/findByUsername?username={}".format(self.endpoint, username)
        resp = requests.get(url, verify=False, headers=self._request_headers())
        user = resp.json()
        self.out(v='Found user {}, guid: {} .'.format(username, user['guid']))
        return user

    def find_group_by_groupname(self, group_name):
        url = "{}ext/group?term={}&limit=1".format(self.endpoint, group_name)
        resp = requests.get(url, verify=False, headers=self._request_headers())
        group_list = resp.json()
        if len(group_list) == 0 or group_list[0]['name'] != group_name:
            self.out(v='Cant find group: {}'.format(group_name))
            return None

        group = group_list[0]
        self.out(v='Found group {}, guid: {} .'.format(group['name'], group['guid']))
        return group

    def add_permissions_for_group(self, settings, group_id):
        if self.dry:
            self.out(v='Added group permissions in group {}.'.format(group_id))
            return None

        url = "{}grouppermission".format(settings.get_endpoint_for_monex_service())
        data = {'groupId': group_id, 'permissionIds': [0, 1]}

        requests.post(url, verify=False, headers=self._request_headers(), data=json.dumps(data))
        self.out(v='Added group permissions in group {}.'.format(group_id))

    def delete_permissions_from_group(self, settings, group_id):
        if self.dry:
            self.out(v='Removed group permissions from group {}.'.format(group_id))
            return None

        url = "{}grouppermission".format(settings.get_endpoint_for_monex_service())
        data = {'groupId': group_id, 'permissionIds': [0, 1]}

        requests.delete(url, verify=False, headers=self._request_headers(), data=json.dumps(data))
        self.out(v='Removed group permissions from group {}.'.format(group_id))

    """
    Make request. Logs in if needed.
    """
    @auto_auth
    def _request(self, method, path, params=None, dataObj=None, encCls=JsonEncoder, decCls=JsonDecoder):
        """
        Make a request to Monex. This auto logs in.

        :param method: The HTTP method name as a string. Some valid names are: `get`, `post`, `put` and `delete`.
        :type method: str
        :param path: The Monex path on which the request needs to be made, e.g. `/auth/login`
        :type path: str
        """
        return self._request_no_auth(method, path, params, dataObj, encCls, decCls)

    """
    Makes request. No auto-login.
    """
    def _request_no_auth(self, method, path, params=None, dataObj=None, encCls=JsonEncoder, decCls=JsonDecoder):
        """
        This is the low level method used to make the underlying Monex requests. It is preferable to use :meth:`_request` method instead.

        :param method: The HTTP method name as a string. Some valid names are: `get`, `post`, `put` and `delete`.
        :type method: str
        :param path: The Monex path on which the request needs to be made, e.g. `/auth/login`
        :type path: str
        """

        # Create full request path
        url = os.path.join(self.endpoint, path)

        # Get request type
        req_method = getattr(self.conn, method)

        # Convert data to json
        data = dataObj and json.dumps(dataObj, cls=encCls) or None

        # Log
        logging.debug("%s request with params: %s data length %s on: %s", method.upper(), params, data and len(data) or 0, url) # Mainly for the sake of data length

        # Set headers
        headers = {"Content-Type": "application/json"}
        if self.accessToken:
            headers["Authorization"] = "Bearer " + self.accessToken

        # Send request
        resp = req_method(url, data=data, params=params,
                          headers=headers,
                          timeout=self.timeout)
        res = check_success(resp, decCls)
        return res

