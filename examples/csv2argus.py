#
# Copyright (c) 2016, salesforce.com, inc.
# All rights reserved.
# Licensed under the BSD 3-Clause license.
# For full license text, see LICENSE.txt file in the repo root  or https://opensource.org/licenses/BSD-3-Clause
#

import requests, time, calendar, csv, getpass, logging, os
from optparse import OptionParser

# Use the package in this repo (argusclient directory)
from argusclient import ArgusServiceClient, Metric


# Class for parsing command-line options
class MyOptionParser(OptionParser, object):
    def format_epilog(self, formatter):
        return self.epilog

    def check_values(self, values, args):
        opt, args = super(MyOptionParser, self).check_values(values, args)
        if os.environ.get('PASS'):
            opt.password = os.environ.get('PASS')
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
parser.add_option("-i", "--inputfile", dest="inputfile", default=None,
                  help="Specify an input file for the CSV to be parsed and loaded into Argus.")

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
                  help="Comma separated Argus metric names for posting metrics")
parser.add_option("--argustags", dest="argustags", default=None,
                  help="Comma separated Argus tag names for posting metrics")

# Optional Timestamp Column
parser.add_option("--timestampcolumn", dest="timestampcolumn", default="_time",
                  help="Optional name for column containing metric timestamp")

# Optional Dateformat Parameter
parser.add_option("--dateformat", dest="dateformat", default="%Y-%m-%dT%H:%M:%S",
                  help="Optional date format for timestamp column, e.g. \"%Y-%m-%dT%H:%M:%S\"")

# Optional test parameter
parser.add_option("--test", dest="testing", action="store_true", default=False,
                  help="Specify --test to, instead of pushing the metrics to argus, print them to STDOUT")

(opts, args) = parser.parse_args()

# Required command-option checks
if not opts.inputfile:
    parser.error("Missing CSV inputfile command-line argument.")
if not opts.argusws:
    parser.error("Missing required argusws command-line argument.")
if not opts.argusscope:
    parser.error("Missing required argus scope accompanied with argusscope command-line argument.")
if not opts.argusmetrics:
    parser.error("Missing required argusmetrics command-line argument.")
if not opts.timestampcolumn or opts.timestampcolumn == "":
    parser.error("Timestamp column unset.")

# build lists for multivalue options
if opts.argusmetrics:
    metricNames = opts.argusmetrics.split(",")

if opts.arguskeys:
    keyNames = opts.arguskeys.split(",")
else:
    keyNames = None

if opts.argustags:
    tagNames = opts.argustags.split(",")
else:
    tagNames = None

# Create a logging object and set logging level based on command-line option or default
logging.basicConfig()
if not opts.quiet:
    logging.root.setLevel(opts.quiet and logging.WARN or (opts.debug and logging.DEBUG or logging.INFO))


# Conversion function for Splunk format
def to_gmt_epoch(tsstr):
    # tsstr is expected to be in the default Splunk format: "2015-11-01T00:00:00.000+00:00", return epoch time in ms resolution
    return calendar.timegm(time.strptime(tsstr[:19], opts.dateformat)) * 1000


def parse_csv_into_metrics(csvfile):

    with open(csvfile, 'r') as input:
        # Use a CSV reader to iterate through the results, creating a list named data
        csvr = csv.reader(input)
        # var for column names from first row in result
        cols = None
        data = []
        for row in csvr:
            logging.debug("Got row: %s", row)
            # Assign cols from the first row, the header in the CSV
            if not cols:
                cols = row

                # Validate parameters against incoming column headers
                if not opts.timestampcolumn in cols:
                    logging.error("Error: Timestamp column \"" + opts.timestampcolumn + "\" not present in header row.")
                    return None

                if tagNames:
                    for tagName in tagNames:
                        if not tagName in cols:
                                logging.error("Error: tagName \"" + tagName + "\" not in column headers.")
                                return None

                if keyNames:
                    for keyName in keyNames:
                        if not keyName in cols:
                                logging.error("Error: keyName \"" + keyName + "\" not in column headers.")
                                return None

                if metricNames:
                    for metricName in metricNames:
                        if not metricName in cols:
                            logging.error("Error: metricName \"" + metricName + "\" not in column headers.")
                            return None

                continue

            # Append rows to data
            data.append(dict(zip(cols, row)))

        if not opts.quiet:
            logging.info("Total result count: %s", len(data))

        # dictionary var to hold metrics
        m_dict = {}

        # for loop to populate m_dict
        rowNum = 2 # rowNum starts after header row, useful for counting, reporting errors, etc. 

        for row in data:
            # abort without timestamp
            try:
                ts = row[opts.timestampcolumn] and to_gmt_epoch(row[opts.timestampcolumn])
            except ValueError: # catch dateformat error parsing timestamp value
                logging.error("Error: Timestamp (" + row[opts.timestampcolumn] + ") format does not match Dateformat (" + opts.dateformat + ").")
                return None
            # Fail if the timestamp value is blank    
            if not ts:
                logging.error("Error: Parse error for Timestamp value on row " + rowNum + ". Value=\"" + row[opts.timestampcolumn] + "\"")
                return None

            # create final scope, substitute keys into the scope
            rowScope = opts.argusscope

            # abort without arguskeys
            if keyNames:
                for keyName in keyNames:
                    logging.debug("Subbing keyName " + keyName + " with value " + str(row[keyName]))
                    rowScope = rowScope.replace("{" + keyName + "}", row[keyName])
                    logging.debug("New rowScope = " + rowScope)

            # create tags
            tag_dict = {}
            if tagNames:
                for tagName in tagNames:
                    logging.debug("Setting tag pair for name: " + tagName + " and value: " + str(row[tagName]))
                    # abort without argustags
                    tag_dict[tagName] = row[tagName]

            # create metrics and datapoints
            for col in metricNames:

                # abort without argusmetrics
                val = row[col]

                # cast str to number
                if val.isdigit():
                    val = int(val)
                else:
                    try:
                        val = float(val)
                    except:
                         logging.error("Error: Non-numeric metric found: %s", row)
                         return None


                # add a Metric object to m_dict if it doesn't already exist [namespace]:scope:metric{tags}
                if opts.argusnamespace:
                    metric = Metric(scope=rowScope, metric=col, tags=tag_dict, namespace=opts.argusnamespace)
                else:
                    metric = Metric(scope=rowScope, metric=col, tags=tag_dict)

                metric_key = str(metric)
                metric = m_dict.setdefault(str(metric), metric)     
                
                logging.debug("Setting new metric with key: " + metric_key + " ts: " + str(ts) + " and val: " + str(val))

                # add a datapoint for this row/col combination, using the timestamp as the key
                metric.datapoints[ts] = val

            rowNum += 1 # increment the row counter

    if not opts.quiet:
        logging.info("Total metric count: %s", len(m_dict))
    return m_dict.values()


metrics = parse_csv_into_metrics(opts.inputfile)

if metrics:

    if opts.testing:
        print("Test mode enabled, printing  metrics:")
        print(metrics)
    else:
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

            response = argus.metrics.add(metrics);

            if opts.verbose:
                logging.info("Argus response:")
                logging.info(response)
            if not opts.quiet:
                logging.info("Done.")
        except:
            logging.exception("Argus failure")

