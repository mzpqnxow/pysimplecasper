#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This is a sample program that utilizes the CasperAPI class

It will produce a small set of files in CSV and JSON formats
See the README.md for a summary of the content of these files

Copyright 2017, <copyright@mzpqnxow.com>
See COPYRIGHT for details
"""
from __future__ import unicode_literals
import json
from os import getenv
from os.path import join

from simplecasper import CasperAPI
from simplecasper import SWVersions, to_file

OUTPATH = 'output'
TESTING = False

def main():
    """Exercise the simplecasper API"""

    def _outpath(filename):
        """Helper function, for aesthetics"""
        return join(OUTPATH, filename)

    sw_version = SWVersions()
    print('The latest version of Google Chrome is %s' % (
        sw_version.get_version(
            applications=('Google Chrome', ),
            version_only=True)))

    # authenticate to Casper API
    # use export CASPER_USER=yourname, etc..
    # put in a ~/.caspercredsrc and source it in your shellrc
    for var in ('CASPER_USER', 'CASPER_PASS', 'CASPER_HOST'):
        if not getenv(var):
            print("FATAL: %s is missing from user environment" % (
                var))
            raise RuntimeError(
                'Missing Casper API information, set CASPER_USER, CASPER_PASS, CASPER_HOST')
    capi = CasperAPI(
        getenv('CASPER_USER'),
        getenv('CASPER_PASS'),
        getenv('CASPER_HOST'))
    # capi.enable_debug()
    capi.http_get_computers()
    to_file(_outpath('user_chrome_extensions.json'), capi.get_chrome_extensions())
    to_file(_outpath('user_patches.json'), capi.http_get_patches())
    to_file(_outpath('user_applications.json'), capi.get_applications())
    to_file(_outpath('all_applications.json'), capi.get_applications(per_user=False))
    to_file(_outpath('user_plugins.json'), capi.get_plugins())
    to_file(_outpath(
        'user_available_software_updates.json'), capi.get_available_software_updates())
    to_file(_outpath('user_available_updates.json'), capi.get_available_updates())
    to_file(_outpath('ip_to_user_object.json'), capi.get_ip_user_map(simple=False))
    to_file(_outpath('ip_to_username.json'), capi.get_ip_user_map(simple=True))
    to_file(_outpath('user_services.json'), capi.get_services())
    to_file(_outpath('services_counter.json'), capi.get_services(per_user=False, counter=True))
    to_file(_outpath(
        'chrome_extensions_counter.json'), capi.get_chrome_extensions(per_user=False, counter=True))
    to_file(_outpath('user_assets.json'), capi.get_assets())
    to_file(_outpath('user_virtual_machines.json'), capi.get_virtual_machines())
    to_file(_outpath(
        'virtual_machines_counter.json'), capi.get_virtual_machines(counter=True, per_user=False))
    to_file(_outpath('user_missing_patches.csv'), capi.get_missing_patches(csv=True))
    to_file(_outpath('all_computers_ip_map.json'), capi.get_all_computer_data(ip_key=True))
    to_file(_outpath('all_computers_ip_map_not_stale.json'), capi.get_all_computer_data(ip_key=True, exclude_stale=True))
    to_file(_outpath('hardware.json'), capi.get_hardware())

    if TESTING:
        encryption_records = []
        for asset in capi.get_hardware():
            asset_record = {}
            encryption = asset['disk_encryption_configuration']
            hostname = asset['hostname']
            person = asset['person']
            asset_record['encryption_enabled'] = True if encryption else False
            asset_record['owner_name'] = person
            asset_record['hostname'] = hostname
            encryption_records.append(asset_record)
        to_file(_outpath('encryption.json'), encryption_records)

if __name__ == '__main__':
    main()
