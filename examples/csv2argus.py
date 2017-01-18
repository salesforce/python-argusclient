#
# Copyright (c) 2016, salesforce.com, inc.
# All rights reserved.
# Licensed under the BSD 3-Clause license.
# For full license text, see LICENSE.txt file in the repo root  or https://opensource.org/licenses/BSD-3-Clause
#

import requests, time, calendar, csv, getpass, logging
from optparse import OptionParser

# Use the package in this repo (argusclient directory)
from argusclient import ArgusServiceClient, Metric

# Class for parsing command-line options
class MyOptionParser(OptionParser,object):
    def format_epilog(self, formatter):
        return self.epilog
    def check_values(self, values, args):
        opt, args = super(MyOptionParser, self).check_values(values, args)
        if not opt.password:
            opt.password = getpass.getpass("Password: ")
        return opt, args

epilog = r"""
Sample Usage:

python examples/csv2argus.py \
  --argusws <endpoint> \
  --argusnamespace "myMetrics" \
  --argusscope "{index}.appFeature.apex" \
  --arguskeys index \
  --argusmetrics "avgRunTime.ms,p95RunTime.ms,count" \
  --argustags logRecordType,customerId \
  --user <user> \
  --pass <password>
"""

# Object for command-line options
parser = MyOptionParser(epilog=epilog)
# logging options
parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
                  help="Quiet mode, output only errors", default=False)
parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                  help="Verbose mode", default=False)
parser.add_option("-d", "--debug", dest="debug", action="store_true",
                  help="Debug mode", default=False)
# credentials
parser.add_option("-u", "--user", dest="user", default=getpass.getuser(),
                  help="Specify username for Argus connection")
parser.add_option("-p", "--pass", dest="password", default=None,
                  help="Specify password for Argus connection (not specifying this option will result in getting prompted")

# Input file
parser.add_option("-i", "--inputfile", dest="inputfile", default=None, help="Specify an input file for the CSV to be parsed and loaded into Argus.")

# endpoints
parser.add_option("--argusws", dest="argusws",
                  help="Specify Argus webservice endpoint")

# actions
parser.add_option("--alert", dest="alert", action="store_true",
                  help="Create/update alert", default=False)
parser.add_option("--dashboard", dest="dashboard", action="store_true",
                  help="Create/update dashboard", default=False)

# Argus metric components
parser.add_option("--argusnamespace", dest="argusnamespace", default=None,
                  help="The Argus namespace for posting metrics")
parser.add_option("--arguskeys", dest="arguskeys", default=None,
                    help="Specify the result fields to use as the Argus scope for posting metrics")
parser.add_option("--argusscope", dest="argusscope", default=None,
                  help="The Argus scope name for posting metrics")
parser.add_option("--argusmetrics", dest="argusmetrics", default=None,
                  help="The Argus scope name for posting metrics")
parser.add_option("--argustags", dest="argustags", default=None,
                  help="The Argus scope name for posting metrics")
(opts, args) = parser.parse_args()

# Required command-option checks
if not opts.inputfile:
    parser.error("Missing CSV inputfile command-line argument")
if not opts.argusws:
    parser.error("Missing required argusws command-line argument")
if not opts.argustags:
    parser.error("Missing required argustags command-line argument")
if not opts.argusmetrics:
    parser.error("Missing required argusmetrics command-line argument")
if not opts.arguskeys:
    parser.error("Missing required arguskeys command-line argument")

# build lists for multivalue options
if opts.argustags:
    tagNames= opts.argustags.split(",")
if opts.argusmetrics:
    metricNames= opts.argusmetrics.split(",")
if opts.arguskeys:
    keyNames= opts.arguskeys.split(",")

# Create a logging object and set logging level based on command-line option or default
logging.basicConfig()
if not opts.quiet:
    logging.root.setLevel(opts.quiet and logging.WARN or (opts.debug and logging.DEBUG or logging.INFO))

# Conversion function for Splunk format
def to_gmt_epoch(tsstr):
    # tsstr is expected to be in the default Splunk format: "2015-11-01T00:00:00.000+00:00", return epoch time in ms resolution
    return calendar.timegm(time.strptime(tsstr[:19], "%Y-%m-%dT%H:%M:%S"))*1000

def parse_csv_into_metrics(csvfile):


    with open(csvfile,'r') as input:
        # Use a CSV reader to iterate through the results, creating a list named data
        csvr = csv.reader(input)
        # var for column names from first row in result
        cols = None
        data = []
        for row in csvr:
            logging.info("Got row: %s", row)
            # Assign cols from the first row, the header in the CSV
            if not cols:
                cols = row
                continue
            # Append rows to data
            data.append(dict(zip(cols, row)))
        if not opts.quiet:
            logging.info("Total result count: %s", len(data))

        # dictionary var to hold metrics
        m_dict = {}
        # for loop to populate m_dict
        for row in data:

            # abort without timestamp
            try:
                ts = row["_time"] and to_gmt_epoch(row["_time"])
            except KeyError:
                logging.error("Error: Timestamp not found: %s", row)
                return None

            # create final scope, substitute keys into the scope
            rowScope = opts.argusscope

            # abort without arguskeys
            for keyName in keyNames:
                try:
                    rowScope = rowScope.replace("{"+keyName+"}",row[keyName])
                except KeyError:
                    logging.error("Error: Specified arguskeys not found: %s", row)
                    return None

            # create tags
            tag_dict = {}
            for tagName in tagNames:
                # abort without argustags
                try:
                    tag_dict[tagName] = row[tagName]
                except KeyError:
                    logging.error("Error: Specified tags not found: %s", row)
                    return None

            # create metrics and datapoints
            for col in metricNames:

                m_key = (col)

                # abort without argusmetrics
                try:
                    val = row[col]
                except KeyError:
                    # Key is not present
                    logging.error("Error: Specified metrics not found: %s", row)
                    return None

                # abort for non-numeric metrics
                try:
                    float(val)
                except:
                    logging.error("Error: Non-numeric metric found: %s", row)
                    return None

                # cast str to number
                if "." in val:
                    val = float(val)
                else:
                    val = int(val)

                # add a Metric object to m_dict if it doesn't already exist [namespace]:scope:metric{tags}
                if not m_key in m_dict:
                    if opts.argusnamespace:
                        m_dict[m_key] = Metric(scope=rowScope, metric=col, tags=tag_dict, namespace=opts.argusnamespace)
                    else:
                        m_dict[m_key] = Metric(scope=rowScope, metric=col, tags=tag_dict)

                # create a copy of the current Metric object for this metric
                m = m_dict[m_key]

                # add a datapoint for this row/col combination, using the timestamp as the key
                m.datapoints[ts] = val

    if not opts.quiet:
        logging.info("Total metric count: %s", len(m_dict))
    return m_dict.values()


metrics = parse_csv_into_metrics(opts.inputfile)

if metrics:
    argus = ArgusServiceClient(opts.user,
                               opts.password,
                               endpoint=opts.argusws)
    if not opts.quiet:
        logging.info("Logging into Argus service")
    try:
        argus.login()
        if opts.verbose:
            logging.info("Argus login successful")
        if not opts.quiet:
            logging.info("Posting metrics to Argus..")
        argus.metrics.add(metrics);
        if not opts.quiet:
            logging.info("Done.")
    except:
        logging.exception("Argus failure")

