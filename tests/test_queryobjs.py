#
# Copyright (c) 2016, salesforce.com, inc.
# All rights reserved.
# Licensed under the BSD 3-Clause license. 
# For full license text, see LICENSE.txt file in the repo root  or https://opensource.org/licenses/BSD-3-Clause
#

import unittest

from argusclient import *

scope = "test.scope"
metric = "test.metric"
aggregator = "test.aggregator"
tags = {"test.tag": "test.value"}
namespace = "test.namespace"
source = "test.source"
stTime = "-1d"
enTime = "-0d"


class TestMetricQuery(unittest.TestCase):
    def testSimpleStTimeOnly(self):
        self.assertEquals(str(MetricQuery(scope, metric, aggregator, stTimeSpec=stTime)), "-1d:test.scope:test.metric:test.aggregator")
        self.assertEquals(MetricQuery(scope, metric, aggregator, stTimeSpec=stTime).getQueryParams(), dict(expression="-1d:test.scope:test.metric:test.aggregator"))

    def testSimpleTimeRange(self):
        self.assertEquals(str(MetricQuery(scope, metric, aggregator, stTimeSpec=stTime, enTimeSpec=enTime)), "-1d:-0d:test.scope:test.metric:test.aggregator")

    def testNoTimeError(self):
        self.failUnlessRaises(AssertionError, lambda: MetricQuery(scope, metric, aggregator))

    def testWithTags(self):
        self.assertEquals(str(MetricQuery(scope, metric, aggregator, stTimeSpec=stTime, tags=tags)), "-1d:test.scope:test.metric{test.tag=test.value}:test.aggregator")

    def testWithNamespace(self):
        self.assertEquals(str(MetricQuery(scope, metric, aggregator, namespace=namespace, stTimeSpec=stTime)), "-1d:test.scope:test.metric:test.aggregator:test.namespace")

    def testWithNamespace2(self):
        self.assertEquals(str(MetricQuery(scope, metric, aggregator, namespace=namespace, stTimeSpec=stTime, enTimeSpec=enTime)), "-1d:-0d:test.scope:test.metric:test.aggregator:test.namespace")


class TestAnnotationQuery(unittest.TestCase):
    def testSimpleStTimeOnly(self):
        self.assertEquals(str(AnnotationQuery(scope, metric, source, stTimeSpec=stTime)), "-1d:test.scope:test.metric:test.source")

    def testSimpleTimeRange(self):
        self.assertEquals(str(AnnotationQuery(scope, metric, source, stTimeSpec=stTime, enTimeSpec=enTime)), "-1d:-0d:test.scope:test.metric:test.source")

    def testNoTimeError(self):
        self.failUnlessRaises(AssertionError, lambda: AnnotationQuery(scope, metric, source))

    def testWithTags(self):
        self.assertEquals(str(AnnotationQuery(scope, metric, source, stTimeSpec=stTime, tags=tags)), "-1d:test.scope:test.metric{test.tag=test.value}:test.source")
