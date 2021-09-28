#
# Copyright (c) 2016, salesforce.com, inc.
# All rights reserved.
# Licensed under the BSD 3-Clause license. 
# For full license text, see LICENSE.txt file in the repo root  or https://opensource.org/licenses/BSD-3-Clause
#

import unittest
import lxml.etree

from argusclient.dashboardtags import *


class TestDashboardTags(unittest.TestCase):
    def testDashboard(self):
        self.assertEqual(lxml.etree.tounicode(DASHBOARD()), "<ag-dashboard/>")

    def testDate(self):
        self.assertEqual(lxml.etree.tounicode(DATE()), "<ag-date/>")

    def testText(self):
        self.assertEqual(lxml.etree.tounicode(TEXT()), "<ag-text/>")

    def testSubmit(self):
        self.assertEqual(lxml.etree.tounicode(SUBMIT()), "<ag-submit/>")

    def testChart(self):
        self.assertEqual(lxml.etree.tounicode(CHART()), "<ag-chart/>")

    def testAreaChart(self):
        self.assertEqual(lxml.etree.tounicode(AREA_CHART()), '<ag-chart type="stackarea"/>')

    def testOption(self):
        self.assertEqual(lxml.etree.tounicode(OPTION()), "<ag-option/>")

    def testMetric(self):
        self.assertEqual(lxml.etree.tounicode(METRIC()), "<ag-metric/>")

    def testFalgs(self):
        self.assertEqual(lxml.etree.tounicode(FLAGS()), "<ag-flags/>")

    def testHtml(self):
        self.assertEqual(lxml.etree.tounicode(E.h1()), "<h1/>")
        self.assertEqual(lxml.etree.tounicode(E.h1(E.h2())), "<h1><h2/></h1>")


# FIXME: Order of parameters is not going to be always the same.
class TestDashboardGen(unittest.TestCase):
    def testSample1(self):
        self.assertEqual(lxml.etree.tounicode(DASHBOARD(CHART(name="Chart")), method="html"), """<ag-dashboard><ag-chart name="Chart"></ag-chart></ag-dashboard>""")

    def testStartDate(self):
        self.assertEqual(lxml.etree.tounicode(DASHBOARD(START_DATE()), method="html"), """<ag-dashboard><ag-date type="datetime" name="start" label="Start Date" default="-1d"></ag-date></ag-dashboard>""")

    def testEndDate(self):
        self.assertEqual(lxml.etree.tounicode(DASHBOARD(END_DATE()), method="html"), """<ag-dashboard><ag-date type="datetime" name="end" label="End Date" default="-0d"></ag-date></ag-dashboard>""")

    def testTextBox(self):
        self.assertEqual(lxml.etree.tounicode(DASHBOARD(TEXT_BOX("test")), method="html"), """<ag-dashboard><ag-text type="text" name="test" label="Test" default=""></ag-text></ag-dashboard>""")

    def testTitle(self):
        self.assertEqual(lxml.etree.tounicode(DASHBOARD(CHART(TITLE("Title"), name="Chart")), method="html"), """<ag-dashboard><ag-chart name="Chart"><ag-option name="title.text" value="Title"></ag-option></ag-chart></ag-dashboard>""")

    def testSubTitle(self):
        self.assertEqual(lxml.etree.tounicode(DASHBOARD(CHART(SUB_TITLE("Sub Title"), name="Chart")), method="html"), """<ag-dashboard><ag-chart name="Chart"><ag-option name="subtitle.text" value="Sub Title"></ag-option></ag-chart></ag-dashboard>""")
