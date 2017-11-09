#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Produce reports based on a YaML config file
"""
from __future__ import unicode_literals
from collections import OrderedDict
from json import dump as json_dump
from logging import (
    basicConfig as configure_log_basic,
    getLogger as get_logger,
    DEBUG as LOGLEVEL_DEBUG)
from os import getenv
from os.path import join
import sys

import yaml

from simplecasper import CasperAPI, get_casper_credentials
from simplecasper import SWVersions, to_file

reload(sys)
sys.setdefaultencoding('utf8')

configure_log_basic()
LOG = get_logger(__name__)
LOG.setLevel(LOGLEVEL_DEBUG)
INFO = LOG.info
CRIT = LOG.critical
WARN = LOG.warn
DEBUG = LOG.debug
ERROR = LOG.error
FATAL = LOG.fatal

CAPI_DEBUG = False

def load_yml_conf(stream, loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


def main():
    username, password, hostname = get_casper_credentials()
    capi = CasperAPI(username, password, hostname)
    capi.read_cache(True)
    capi.update_cache(False)
    if CAPI_DEBUG is True:
        capi.enable_debug()
    capi.http_get_computers()
    # computers = capi.get_all_computer_data()
    xattr_stats = capi.get_extension_attributes(count=True)
    to_file(join('output', 'xattr_stats.json'), xattr_stats)


if __name__ == '__main__':
    main()
