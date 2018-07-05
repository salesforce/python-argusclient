#
# Copyright (c) 2016, salesforce.com, inc.
# All rights reserved.
# Licensed under the BSD 3-Clause license. 
# For full license text, see LICENSE.txt file in the repo root  or https://opensource.org/licenses/BSD-3-Clause
#

import requests, sys, json, os, time, calendar, csv, getpass, logging, urlparse
from optparse import OptionParser, Option, OptionValueError

import splunklib.client as splunkclient

from argusclient import ArgusServiceClient, Metric

class MyOptionParser(OptionParser,object):
    def check_values(self, values, args):
        opt, args = super(MyOptionParser, self).check_values(values, args)
        if not opt.password:
            opt.password = getpass.getpass("Password: ")
        return opt, args

parser = MyOptionParser()
parser.add_option("-q", "--quite", dest="quite", action="store_true",
                  help="Quite mode, output only errors", default=False)
parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                  help="Verbose mode", default=False)
parser.add_option("-d", "--debug", dest="debug", action="store_true",
                  help="Debug mode", default=False)
parser.add_option("-u", "--user", dest="user", default=getpass.getuser(),
                  help="Specify username for Argus/Splunk connection")
parser.add_option("-p", "--pass", dest="password", default=None,
                  help="Specify password for Argus/Splunk connection (not specifying this option will result in getting prompted")
parser.add_option("--argusws", dest="argusws",
                  help="Specify Argus webservice endpoint")
parser.add_option("--splunkapi", dest="splunkapi",
                  help="Specify Splunk API endpoint")
parser.add_option("--alert", dest="alert", action="store_true",
                  help="Create/update alert", default=False)
parser.add_option("--dashboard", dest="dashboard", action="store_true",
                  help="Create/update dashboard", default=False)
parser.add_option("-I", "--index", dest="index", default="na44",
                  help="Specify the Splunk index to search against")
parser.add_option("-S", "--earliest", dest="earliest", default="-1d@d",
                  help="Specify splunk time expression for the start of the time range")
parser.add_option("-E", "--latest", dest="latest", default="-0d@d",
                  help="Specify splunk time expression for the end of the time range")
parser.add_option("-P", "--pattern", dest="pattern", default=None,
                  help="Specify a Splunk pattern to search for")
parser.add_option("-T", "--span", dest="span", default="15m",
                  help="Specify an alternative span for bucketing option")
parser.add_option("--scope", dest="scope", default="patternStats",
                  help="The Argus scope name for posting metrics")
parser.add_option("--namespace", dest="namespace", default="testNamespace",
                  help="The Argus namespace name for posting metrics")
(opts, args) = parser.parse_args()

if not opts.pattern:
    parser.error("Please specify a Splunk pattern to search for")
if not opts.argusws:
    parser.error("Need the URL to the Argus endpoint")
if not opts.splunkapi:
    parser.error("Need the URL to the Splunk endpoint")

logging.basicConfig()
if not opts.quite:
    logging.root.setLevel(opts.quite and logging.WARN or (opts.debug and logging.DEBUG or logging.INFO))

def to_gmt_epoch(tsstr):
    # tsstr is expected to be in the default Splunk format: "2015-11-01T00:00:00.000+00:00"
    return calendar.timegm(time.strptime(tsstr[:19], "%Y-%m-%dT%H:%M:%S"))

def get_splunk_metrics(opts):
    splunkendpoint = urlparse.urlsplit(opts.splunkapi)
    splunk_opts = {
        "scheme": splunkendpoint.scheme,
        "host": splunkendpoint.hostname,
        "port": splunkendpoint.port,
        "username": opts.user,
        "password": opts.password,
    }

    try:
        if not opts.quite:
            logging.info("Logging into Splunk service")
        service = splunkclient.connect(**splunk_opts)
        if not opts.quite:
            logging.info("Splunk login successful")
    except:
        logging.exception("Splunk login failed")
        return None


    splunkquery = """
    search index={index} earliest={earliest} latest={latest} "{pattern}"
    | bucket _time span={span}
    | stats count by _time, host
    | appendpipe [stats avg(count) as avgCount, sum(count) as sumCount, min(count) as minCount, max(count) as maxCount, stdev(count) as stdevCount by host]
    """

    if not opts.quite:
        logging.info("Submitting job to Splunk..")
    job = service.jobs.create(splunkquery.format(index=opts.index, pattern=opts.pattern, earliest=opts.earliest, latest=opts.latest, span=opts.span))
    if not opts.quite:
        logging.info("Waiting for job to be ready..")
    while not job.is_ready():
        if opts.verbose:
            logging.info("Still waiting for job to be ready..")
        time.sleep(1)
    else:
        if not opts.quite:
            logging.info("Job is ready, waiting for completion..")
    while not job.is_done():
        if opts.verbose:
            logging.info("Still waiting for job to be completed..")
        time.sleep(2)
    else:
        if not opts.quite:
            logging.info("Job is done, collecting results..")

    results = job.results(output_mode="csv", count=0)
    csvr = csv.reader(results)
    cols = None
    data = []
    for row in csvr:
        logging.debug("Got row: %s", row)
        if not cols:
            cols = row
            continue
        data.append(dict(zip(cols, row)))
    if not opts.quite:
        logging.info("Total result count: %s", len(data))

    runts = int(time.time())
    m_dict = {}
    patternTagVal = opts.pattern.replace(" ", "__") # We can't have spaces in tag values.
    for row in data:
        host = row["host"]
        if not host:
            logging.warn("Skipping row with no host: %s", row)
            continue
        for col in row:
            if col in ("_time", "host") or not row[col]:
                continue
            m_key = (host, col)
            if not m_key in m_dict:
                m_dict[m_key] = Metric(opts.scope, patternTagVal+"."+col, tags=dict(host=host, patternStr=patternTagVal), namespace=opts.namespace)
            m = m_dict[m_key]
            ts = row["_time"] and to_gmt_epoch(row["_time"]) or runts
            val = row[col]
            if "." in val:
                val = float(val)
            else:
                val = int(val)
            if logging.root.isEnabledFor(logging.DEBUG):
                logging.debug("Adding %s at timestamp: %s for metric: %s", val, ts, m.desc())
            m.datapoints[ts] = val

    if not opts.quite:
        logging.info("Total metric count: %s", len(m_dict))
    job.cancel()
    return m_dict.values()

metrics = get_splunk_metrics(opts)
if metrics:
    argus = ArgusServiceClient(opts.user,
                               opts.password,
                               endpoint=opts.argusws)
    if not opts.quite:
        logging.info("Logging into Argus service")
    try:
        argus.login()
        if opts.verbose:
            logging.info("Argus login successful")
        if not opts.quite:
            logging.info("Posting metrics to Argus..")
        argus.metrics.add(metrics);
        if not opts.quite:
            logging.info("Done.")
    except:
        logging.exception("Argus failure")

