"""
This module provides functions for generating dashboard tags. These functions are simple wrappers on top of the lxml `ElementMaker` API.
These functions can be combined with additional HTML tags to produce the required XML to define dashboards.

    >>> import lxml.etree
    >>> from argusclient.dashboardtags import E, DASHBOARD, CHART, TITLE, METRIC
    >>> h1 = E.h1
    >>> hr = E.hr
    >>> dashboard = DASHBOARD(h1("Test Dashboard"), hr(), CHART(TITLE("hdara.test"), METRIC("-1d:-0d:test.scope:test.metric:sum", name="hdara.test.metric"), name="Chart"))
    >>> print lxml.etree.tostring(dashboard, pretty_print=True)
    <ag-dashboard>
      <h1>Test Dashboard</h1>
      <hr/>
      <ag-chart name="Chart">
        <ag-option name="title.text" value="hdara.test"/>
        <ag-metric name="hdara.test.metric">-1d:-0d:test.scope:test.metric:sum</ag-metric>
      </ag-chart>
    </ag-dashboard>
    >>> print lxml.etree.tostring(dashboard, method="html")
    <ag-dashboard><h1>Test Dashboard</h1><hr/><ag-chart name="Chart"><ag-option name="title.text" value="hdara.test"/><ag-metric name="hdara.test.metric">-1d:-0d:test.scope:test.metric:sum</ag-metric></ag-chart></ag-dashboard>

Argus cant't handle auto-closed XML tags, so using "html" `method` is recommended.
"""

#
# Copyright (c) 2016, salesforce.com, inc.
# All rights reserved.
# Licensed under the BSD 3-Clause license. 
# For full license text, see LICENSE.txt file in the repo root  or https://opensource.org/licenses/BSD-3-Clause
#

import lxml.builder

#: Use this to create additional XML/HTML tags, e.g., `E.h1` will create the `<h1>` tag 
E = lxml.builder.ElementMaker()

_DASHBOARD = getattr(E, "ag-dashboard")
_DATE = getattr(E, "ag-date")
_TEXT = getattr(E, "ag-text")
_SUBMIT = getattr(E, "ag-submit")
_CHART = getattr(E, "ag-chart")
_OPTION = getattr(E, "ag-option")
_METRIC = getattr(E, "ag-metric")
_FLAGS = getattr(E, "ag-flags")
_TABULAR = getattr(E, "ag-table")


def DASHBOARD(*args, **kwargs):
    """ Generates an `ag-dashboard` tag. """
    return _DASHBOARD(*args, **kwargs)


def DATE(*args, **kwargs):
    """ Generates an `ag-date` tag. """
    return _DATE(*args, **kwargs)


def TEXT(*args, **kwargs):
    """ Generates an `ag-text` tag. """
    return _TEXT(*args, **kwargs)


def SUBMIT(*args, **kwargs):
    """ Generates an `ag-submit` tag. """
    return _SUBMIT(*args, **kwargs)


def CHART(*args, **kwargs):
    """ Generates an `ag-chart` tag. """
    return _CHART(*args, **kwargs)


def OPTION(*args, **kwargs):
    """ Generates an `ag-option` tag. """
    return _OPTION(*args, **kwargs)


def METRIC(*args, **kwargs):
    """ Generates an `ag-metric` tag. """
    return _METRIC(*args, **kwargs)


def FLAGS(*args, **kwargs):
    """ Generates an `ag-flags` tag. """
    return _FLAGS(*args, **kwargs)


def TABULAR(*args, **kwargs):
    """ Generates an `ag-table` tag. """
    return _TABULAR(*args, **kwargs)


def START_DATE(name="start", label="Start Date", default="-1d"):
    """ Generates a `ag-date` tag with sensible defaults for `name`, `label` and `default` for specifying a start date. """
    return DATE(type="datetime", name=name, label=label, default=default)


def END_DATE(name="end", label="End Date", default="-0d"):
    """ Generates a `ag-date` tag with sensible defaults for `name`, `label` and `default` for specifying end date. """
    return DATE(type="datetime", name=name, label=label, default=default)


def TEXT_BOX(name, label=None, default=None):
    """ Generates a `ag-text` tag with sensible defaults for `type`, `name`, `label` and `default` for specifying text field. """
    return TEXT(type="text", name=name, label=label or name.capitalize(), default=default or "")


def TITLE(title):
    """ Generates a `ag-option` tag with the specified `title`. """
    return OPTION(name="title.text", value=title)


def SUB_TITLE(subTitle):
    """ Generates a `ag-option` tag with the specified `subtitle`. """
    return OPTION(name="subtitle.text", value=subTitle)


def AREA_CHART(*args, **kwargs):
    """ Generates an `ag-chart` tag with `type='stackarea'`. """
    return _CHART(type='stackarea', *args, **kwargs)
