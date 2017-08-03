argusclient -- A minimal client library for Argus webservice
------------------------------------------------------------

This is a minimal and thin layer of Python client code on top of the
Argus webservices REST API. Most of the library API is 1:1 with that of
REST API so it serves to be more of a convenience than an abstraction.
This means you still need to be familiar with the underlying REST API to
be effective. For more information on the REST API and data model, refer
to the `Argus - User
Guide <https://github.com/SalesforceEng/Argus/wiki>`__.
Special thanks to `Demian Brecht <https://github.com/demianbrecht>`__
for giving a lot of feedback early and helping to shape the API and the
project.

You can also browse the Python API documentation online at: `<https://salesforce.github.io/python-argusclient/>`__

A quick primer to using argusclient
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Below you will find functional and self-explanatory code that shows how
to do the following:

-  Import the relevant pieces from argusclient
-  Create the main entry point and establish login session
-  Query for existing namespaces
-  Create a new namespace
-  Collect metrics and annotations
-  Post metrics and annotations
-  Query for existing dashboards
-  Update or Create dashboard
-  Query for existing alerts
-  Delete alert
-  Create an alert along with a trigger and a notification

In addition, also look at the bundled example named
``splunk_to_argus.py`` that shows how to extract metrics from Splunk and
push them to Argus.

Some package imports and initializations that we use later
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    import sys, os, time, calendar, getpass, logging, random
    import lxml.etree

    from argusclient import *
    from argusclient.dashboardtags import DASHBOARD, CHART, TITLE, METRIC, FLAGS

    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARN)

    endpoint = "http://localhost:8080/argusws"
    user = "hdara"
    password = None

    tags = { "host": "hdara-wsl" }
    fields = { "user": user }
    curtm = long(calendar.timegm(time.gmtime()))*1000
    ns_name = "hdara-ns"
    ns_access_addl_users = ("hdara",)
    dashboard_name = "hdara.test.dashboard"
    alert_name = "hdara.test.alert"
    scope_name = "hdara"
    metric_name = "test"
    ans = []

Login to the service and establish session
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    argus = ArgusServiceClient(user,
                               password or getpass.getpass("Password: "),
                               endpoint=endpoint)
    logging.info("Logging in")
    argus.login()

Check if a namespace exists and create one if missing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    logging.info("Looking up existing namespace with name: %s", ns_name)
    nss = dict((ns.qualifier, ns) for ns in argus.namespaces.values())
    ns = nss.get(ns_name)
    if not ns:
        logging.info("Creating new namespace with name: %s", ns_name)
        ns = argus.namespaces.add(Namespace(ns_name))

Generate some random metrics against hdara-ns:hdara:test and mark the start and end with annotations.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    logging.info("Generating some metric and annotation data for the dashboard")
    m = Metric("hdara", "test", tags=tags, namespace=ns_name)
    for t in xrange(10, 0, -1):
        # Warden requires 1 minute gap between successive data points.
        ts = curtm-t*60*1000
        m.datapoints[ts] = random.randint(50, 100)
        if not ans or t == 1:
            ans.append(Annotation("script", "hdara", "test", ts, ts, "generated", tags=tags, fields=dict(event=ans and "start" or "end", **fields)))

Send metrics and annotations to Argus
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    logging.info("Adding metrics data to Argus")
    am_resp = argus.metrics.add([m]);
    if am_resp.error_count():
        logging.info("Errors reported in metric data: errorCount: %s errorMessages: %s", am_resp.error_count(), am_resp.error_messages())
    logging.info("Adding annotation data to Argus")
    an_resp = argus.annotations.add(ans)
    if an_resp.error_count():
        logging.info("Errors reported in annotation data: errorCount: %s errorMessages: %s", an_resp.error_count(), an_resp.error_messages())

Generate dashboard content
^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    mquery = str(MetricQuery(scope_name, metric_name, "sum", tags=tags, stTimeSpec="-1d", enTimeSpec="-0d", namespace=ns_name))
    aquery = str(AnnotationQuery(scope_name, metric_name, "generated", tags=tags, stTimeSpec="-1d", enTimeSpec="-0d"))
    content = lxml.etree.tostring(DASHBOARD(
        CHART(
            TITLE("hdara.test"),
            METRIC(mquery, name="hdara.test.metric"),
            FLAGS(aquery, name="hdara.test.annotation"),
            name="Chart"
            )
    ), method="html")
    dashbobj.content = content

Update or Create dashboard
^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    logging.info("Looking up existing dashboard with name: %s", dashboard_name)
    dashbobj = argus.dashboards.get_user_dashboard(user, dashboard_name)
    if not dashbobj:
        logging.info("Creating new dashboard with name: %s", dashboard_name)
        dashbobj = Dashboard(dashboard_name, content, shared=True, description="A new dashboard")
        dashbobj = argus.dashboards.add(dashbobj)
    else:
        logging.info("Updating dashboard with name: %s id %s", dashboard_name, dashbobj.argus_id)
        dashbobj.content = content
        argus.dashboards.update(dashbobj.argus_id, dashbobj)
    logging.info("Dashboard url: %s", os.path.join(os.path.dirname(endpoint), "argus/#/dashboards", str(dashbobj.argus_id)).replace("-ws", "-ui"))

Look for an existing alert and delete it so that we can recreate it
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    logging.info("Looking up existing alerts with name: %s", alert_name)
    alerts = dict(((alert.ownerName, alert.name), alert) for alert in argus.alerts.values())
    alertobj = alerts.get((user, alert_name))
    if alertobj:
        logging.info("Deleting existing alert with name: %s id: %s", alert_name, alertobj.argus_id)
        argus.alerts.delete(alertobj.argus_id)

Finally, create alert with a trigger and a notification
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    logging.info("Creating new alert with alert name: %s", alert_name)
    alertobj = argus.alerts.add(Alert(alert_name, mquery, "* */1 * * *",
                                      trigger=Trigger("hdara.test.trigger", Trigger.GREATER_THAN, 100000, 600000),
                                      notification=Notification("hdara.test.notification", Notification.EMAIL, subscriptions=["hdara@salesforce.com"]),
                                      shared=True))
