#
# Copyright (c) 2016, salesforce.com, inc.
# All rights reserved.
# Licensed under the BSD 3-Clause license.
# For full license text, see LICENSE.txt file in the repo root  or https://opensource.org/licenses/BSD-3-Clause
#

import getpass, logging, os
from optparse import OptionParser

# Use the package in this repo (argusclient directory)
from argusclient import ArgusServiceClient, TokenAuthenticator, Metric


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

python examples/argusquery.py \
  --argusws <endpoint> \
  --query "argusquery" \
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


# endpoints
parser.add_option("--argusws", dest="argusws",
                  help="Specify Argus webservice endpoint")

# Argus metric components
parser.add_option("--query", dest="query", default=None,
                  help="The Argus query for the dataset.")

# Optional test parameter
parser.add_option("--test", dest="testing", action="store_true", default=False,
                  help="Specify --test to, instead of pushing the metrics to argus, print them to STDOUT")

(opts, args) = parser.parse_args()

# Required command-option checks
if not opts.query:
    parser.error("Missing query command-line argument.")
if not opts.argusws:
    parser.error("Missing required argusws command-line argument.")

# Create a logging object and set logging level based on command-line option or default
logging.basicConfig()
if not opts.quiet:
    logging.root.setLevel(opts.quiet and logging.WARN or (opts.debug and logging.DEBUG or logging.INFO))

if opts.testing:
    print("Test mode enabled, printing query:")
    print(opts.query)

argus = ArgusServiceClient(opts.user,
                           opts.password,
                           auth_obj=TokenAuthenticator,
                           endpoint=opts.argusws)
if not opts.quiet:
    logging.info("Logging into Argus service")
try:
    argus.login()
    if opts.verbose:
        logging.info("Argus login successful")

    if not opts.quiet:
        logging.info("Querying metrics from Argus..")

    from argusclient.client import MetricQuery
    mquery = MetricQuery("cds.database.io.level.5min", "count", "max", tags={"pod": "cs91", "levelName": "XTREME"}, stTimeSpec="-3d",
                              enTimeSpec="-0d", namespace="spcp_db_io_test")
    if not opts.quiet:
        logging.info("Query: " + str(mquery))

    response = argus.metrics.query(mquery)
    print(response[0].datapoints)
    if opts.verbose:
        logging.info("Argus response:")
        logging.info(response)
    if not opts.quiet:
        logging.info("Done.")
except:
    logging.exception("Argus failure")

