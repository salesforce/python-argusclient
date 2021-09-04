#
# Copyright (c) 2016, salesforce.com, inc.
# All rights reserved.
# Licensed under the BSD 3-Clause license.
# For full license text, see LICENSE.txt file in the repo root  or https://opensource.org/licenses/BSD-3-Clause
#

from argusclient import ArgusServiceClient, Alert
from monexclient.monexclient import MonexClient

"""
Login with mtls
"""
monex_client = MonexClient(None,
                            # Endpoint if accessing from Falcon. Public prod endpoint to be released
                           endpoint="put-endpoint-here",
                           login_path="auth/1.0/token")

monex_client.conn.cert = ("path/to/client/cert",
                          "path/to/client/key")
monex_client.login()
print 'token: ', monex_client.accessToken

"""
Set up argus client
"""
argus = ArgusServiceClient(None, None,
                           # Endpoint if accessing from Falcon. Public prod endpoint to be released
                           endpoint="put-endpoint-here",
                           accessToken=monex_client.accessToken)

"""
Add an alert
"""
# alert = argus.alerts.add(Alert('testing-alert-2', expression="-1d:abc:test:sum", cronEntry="*/15 * * * *"))
# print 'alert: ', alert
