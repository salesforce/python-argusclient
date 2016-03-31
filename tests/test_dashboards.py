import unittest
import lxml.etree

from argusclient.dashboardtags import *


class TestDashboardTags(unittest.TestCase):
    def testDashboard(self):
        self.assertEquals(lxml.etree.tostring(DASHBOARD()), "<ag-dashboard/>")

    def testDate(self):
        self.assertEquals(lxml.etree.tostring(DATE()), "<ag-date/>")

    def testText(self):
        self.assertEquals(lxml.etree.tostring(TEXT()), "<ag-text/>")

    def testSubmit(self):
        self.assertEquals(lxml.etree.tostring(SUBMIT()), "<ag-submit/>")

    def testChart(self):
        self.assertEquals(lxml.etree.tostring(CHART()), "<ag-chart/>")

    def testAreaChart(self):
        self.assertEquals(lxml.etree.tostring(AREA_CHART()), '<ag-chart type="stackarea"/>')

    def testOption(self):
        self.assertEquals(lxml.etree.tostring(OPTION()), "<ag-option/>")

    def testMetric(self):
        self.assertEquals(lxml.etree.tostring(METRIC()), "<ag-metric/>")

    def testFalgs(self):
        self.assertEquals(lxml.etree.tostring(FLAGS()), "<ag-flags/>")

    def testHtml(self):
        self.assertEquals(lxml.etree.tostring(E.h1()), "<h1/>")
        self.assertEquals(lxml.etree.tostring(E.h1(E.h2())), "<h1><h2/></h1>")


# FIXME: Order of parameters is not going to be always the same.
class TestDashboardGen(unittest.TestCase):
    def testSample1(self):
        self.assertEquals(lxml.etree.tostring(DASHBOARD(CHART(name="Chart")), method="html"), """<ag-dashboard><ag-chart name="Chart"></ag-chart></ag-dashboard>""")

    def testStartDate(self):
        self.assertEquals(lxml.etree.tostring(DASHBOARD(START_DATE()), method="html"), """<ag-dashboard><ag-date default="-1d" type="datetime" name="start" label="Start Date"></ag-date></ag-dashboard>""")

    def testEndDate(self):
        self.assertEquals(lxml.etree.tostring(DASHBOARD(END_DATE()), method="html"), """<ag-dashboard><ag-date default="-0d" type="datetime" name="end" label="End Date"></ag-date></ag-dashboard>""")

    def testTextBox(self):
        self.assertEquals(lxml.etree.tostring(DASHBOARD(TEXT_BOX("test")), method="html"), """<ag-dashboard><ag-text default="" type="text" name="test" label="Test"></ag-text></ag-dashboard>""")

    def testTitle(self):
        self.assertEquals(lxml.etree.tostring(DASHBOARD(CHART(TITLE("Title"), name="Chart")), method="html"), """<ag-dashboard><ag-chart name="Chart"><ag-option name="title.text" value="Title"></ag-option></ag-chart></ag-dashboard>""")

    def testSubTitle(self):
        self.assertEquals(lxml.etree.tostring(DASHBOARD(CHART(SUB_TITLE("Sub Title"), name="Chart")), method="html"), """<ag-dashboard><ag-chart name="Chart"><ag-option name="subtitle.text" value="Sub Title"></ag-option></ag-chart></ag-dashboard>""")
