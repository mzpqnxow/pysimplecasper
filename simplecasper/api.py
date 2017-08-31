#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CasperAPI class - call the Casper API and parse the data it returns, creating various
objects that are useful for reporting. Some reports supported:

- List all Chrome extensions or per-user.
- List all Chrome extensions with the number of instances of each
- List all services or per-user.
- List all services with the number of instances of each
- List all plug-ins or per-user.
- List all plug-ins with the number of instances of each
- List all applications or per-user.
- List all applications with the number of instances of each
- List all updates or per-user
- List all updates with the number of instances of each
- ...

See driver.py in the root of the repository for examples

Copyright 2017, <copyright@mzpqnxow.com>
See COPYRIGHT for details
"""
from __future__ import unicode_literals, print_function

from collections import (
    defaultdict,
    Counter)
from copy import copy
import datetime
from errno import EEXIST
import httplib
from json import (
    dump as json_dump,
    load as json_load)
from os import mkdir
from os.path import join, realpath, dirname, basename
from re import sub as substitute
from sys import stdout

from simplecasper.util import SimpleHTTPJSON

# Use if doing development, to speed things up by foregoing
# HTTP requests
READ_CACHE = True
UPDATE_CACHE = False


class CasperAPI(SimpleHTTPJSON):
    """CasperAPI: a class for pulling data out of the Casper HTTP JSON API

    This class retrieves raw data and also performs a good deal of processing
    to produce useful reports. To accomplish this, it creates a large set of
    data structures based on the raw data

    The majority of the work takes place in get_computer_data()

    All non-public methods are named with a leading `_` and should not be
    used directly
    """
    HEADERS = {'Accept': 'application/json, text/javascript, */*; q=0.01'}
    COMPUTERS_ENDPOINT = '/computers'
    COMPUTERS_ID_ENDPOINT = '/computers/id/'
    PATCHES_ENDPOINT = '/patches'
    PATCHES_ID_ENDPOINT = '/patches/id/'
    CASPER_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, user, password, fqdn, https=True):
        """Generate reports based on data pulled from the Casper API

        Requires a username, password and fqdn of a Casper server
        Used https by default

        JSON is used via the `Accept` header. This avoids having to
        deal with XML
        """
        super(CasperAPI, self).__init__()
        self._user = user
        self._password = password
        self._url = 'http'
        if https is True:
            self._url += 's'
        self._url += '://%s/JSSResource/' % (fqdn)
        self._cache_path = join(dirname(realpath(__file__)), '..', 'cache')
        # Begin data filled in by get_computer_data()
        self._applications = None
        self._assets = None
        self._available_software_updates = None
        self._available_updates = None
        self._casper_software = None
        self._chrome_extensions = None
        self._computer_data = None
        self._computer_data_list = None
        self._computer_id_list = None
        self._id_to_user_map = None
        self._id_to_patch_report = None
        self._installer_swu_software = None
        self._ip_simple_name_map = None
        self._ip_user_map = None
        self._patches = None
        self._plugins = None
        self._services = None
        self._user_chrome_extensions = None
        self._user_to_machine = None
        self._user_tagged_applications = None
        self._user_tagged_assets = None
        self._user_tagged_available_updates = None
        self._user_tagged_available_software_updates = None
        self._user_tagged_chrome_extensions = None
        self._user_tagged_patch_list = None
        self._user_tagged_plugins = None
        self._user_tagged_services = None
        self._user_tagged_virtual_machines = None
        self._user_virtual_machines = None
        self._virtual_machines = None

    def get_applications(self, per_user=True):
        """Return the applications report

        If per_user is True, return a version containing user context in
        each entry
        """
        self._run_if_none(self._applications)
        if per_user is True:
            return self._user_tagged_applications
        return [dict(t) for t in set([tuple(d.items()) for d in self._applications])]

    def get_plugins(self, per_user=True):
        """Get the plugins report

        If per_user is True, return a version containing user context in
        each entry
        """
        self._run_if_none(self._plugins)
        if per_user is True:
            return self._user_tagged_plugins
        return [dict(t) for t in set([tuple(d.items()) for d in self._plugins])]

    def get_all_computer_data(self):
        """Return all data from the /computers endpoint"""
        self._run_if_none(self._computer_data_list)
        return self._computer_data_list

    def get_missing_patches(self, csv=True):
        """
        Return the missing patches report

        If csv is True, return a list version of the report so that
        it can be easily represented as a CSV
        """
        if csv is True:
            return self._user_tagged_patch_list
        return self._id_to_patch_report

    def get_ip_user_map(self, simple=True):
        """
        Return a dictionary with IP address as the key and user info as value

        If simple is True, the value is only the full name of the user
        If simple is False, the value contains username, full name, and time info
        """
        self._run_if_none(self._ip_simple_name_map)
        if simple is True:
            return self._ip_simple_name_map
        return self._ip_user_map

    def get_chrome_extensions(self, counter=False, per_user=True):
        """
        Return the chrome extension report

        If per_user is True, return the "per user" version
        If counter is True, return a dict of service: unique_count
        key value pairs
        """
        self._run_if_none(self._user_tagged_chrome_extensions)
        if per_user is not True:
            return self._counter_if(self._chrome_extensions, counter)
        # return self._counter_if(self._user_tagged_chrome_extensions, counter)
        return self._user_tagged_chrome_extensions

    def enable_debug(self):
        """Switch on httplib debugging, causing requests to print to stderr"""
        httplib.HTTPConnection.debuglevel = 9

    def disable_debug(self):
        """Switch off httplib debugging, inhibiting requests from printing to stderr"""
        httplib.HTTPConnection.debuglevel = 0

    def get_available_updates(self, counter=False, per_user=True):
        """
        Return the available updates report
        If per_user is True, return the "per user" version
        If counter is True, return a dict of service: unique_count
        key value pairs

        counter and per_user are mutually exclusive
        """
        self._run_if_none(self._available_updates)
        if per_user is True:
            return self._user_tagged_available_updates
        return self._counter_if(self._available_updates, counter)

    def get_available_software_updates(self, per_user=True):
        """
        Return the available software updates report
        If per_user is True, return the "per user" version
        """
        self._run_if_none(self._available_software_updates)
        if per_user is True:
            return self._user_tagged_available_software_updates
        return self._available_software_updates

    def get_virtual_machines(self, counter=False, per_user=True):
        """
        Return the virtual machines report
        If per_user is True, return the "per user" version
        If counter is True, return a dict of service: unique_count
        key value pairs

        counter and per_user are mutually exclusive
        """
        self._run_if_none(self._virtual_machines)
        if per_user is True:
            return self._user_tagged_virtual_machines
        if counter is True:
            return Counter(self._virtual_machines)
        return self._virtual_machines

    def get_assets(self, per_user=True):
        """
        Return the assets report
        If per_user is True, return the "per user" version
        """
        self._run_if_none(self._assets)
        if per_user is True:
            return self._user_tagged_assets
        return self._assets

    def get_services(self, counter=False, per_user=True):
        """
        Return the services report
        If per_user is True, return the "per user" version
        If counter is True, return a dict of service: unique_count
        key value pairs

        counter and per_user are mutually exclusive
        """
        self._run_if_none(self._available_updates)
        if per_user is True:
            return self._user_tagged_services
        return self._counter_if(self._services, counter)

    def http_get_computers(self):
        """
        Fetch a list of computer identifiers from the Casper API
        using the /computers endpoint. Returns a list of integers

        Also, populate self._computer_id_list so that other class
        methods can use the list
        """
        obj = self.http_get_json(
            '%s%s' % (self._url, self.COMPUTERS_ENDPOINT),
            verify=False,
            auth=(self._user, self._password),
            headers=self.HTTP_HEADER_ACCEPT_JSON)
        self._computer_id_list = [record['id'] for record in obj['computers']]
        if READ_CACHE is True:
            return self._cache_load('computers.json')
        elif UPDATE_CACHE is True:
            self._cache_dump(self._computer_id_list, 'computers.json')
        return self._computer_id_list

    def http_get_patch_id_list(self):
        """
        Fetch a list of patch identifiers from the Casper API using
        the /patches endpoint. Returns a list of integers
        """
        obj = self.http_get_json(
            '%s%s' % (self._url, self.PATCHES_ENDPOINT),
            verify=False,
            auth=(self._user, self._password),
            headers=self.HTTP_HEADER_ACCEPT_JSON)
        titles = obj['patch_reporting_software_titles']
        return [record['id'] for record in titles]

    def http_get_patches(self):
        """
        Fetch data from the HTTP /patches endpoint and prepare various
        data structures to make the data easier to understand and work
        with
        """
        self._patches = []
        for patch_id in self.http_get_patch_id_list():
            obj = self.http_get_json('%s%s%s' % (
                self._url, self.PATCHES_ID_ENDPOINT, str(patch_id)),
                verify=False,
                auth=(self._user, self._password),
                headers=self.HTTP_HEADER_ACCEPT_JSON)
            patch_data = obj
            self._patches.append(patch_data)
            self._cache_dump(patch_data, '%s-patches.json' % str(patch_id))
            patch_data = patch_data['software_title']
            name = patch_data['name']
            # total_computers_unpatched = patch_data['total_computers']
            # total_unpatched_versions = patch_data['total_versions']
            unpatched_versions = patch_data['versions']
            # This data structure is bizarre - it is a list of records that
            # really ought to be tuples. It goes like this:
            # [
            # "1.2.3",
            # {"computers": [
            #   ... ], ... }
            # "2.3.4",
            # {"computers": [...]
            # ... }
            # ...
            # So some basic state must be kept if you use a simple for loop
            # over the list. This is done using current_version, which is set
            # to None when it expects a `version` string item and non-None when
            # it expects a `computers` string)
            current_version = None
            for row in unpatched_versions:
                if current_version is None:
                    current_version = row
                    continue
                for computer in row['computers']:
                    # alt_mac_address = computer['alt_mac_address']
                    # serial_number = computer['serial_number']
                    # mac_address = computer['mac_address']
                    identifier = computer['id']  # int
                    # name = computer['name']
                    computer_full = self._computer_data[identifier]
                    computer_full = computer_full['computer']
                    general = computer_full['general']
                    location = computer_full['location']
                    person_name = location['canonical_name']
                    email = location['email_address']
                    serial_number = general['serial_number']
                    # ip = general['last_reported_ip']
                    patch_record = {}
                    patch_record['application'] = name
                    patch_record['version'] = current_version
                    # if self._id_to_patch_report[identifier]:
                    #   pass
                    try:
                        self._id_to_patch_report[identifier]['missing_patches'].append(patch_record)
                    except KeyError:
                        self._id_to_patch_report[identifier] = {}
                        self._id_to_patch_report[identifier]['person'] = person_name
                        self._id_to_patch_report[identifier]['email'] = email
                        self._id_to_patch_report[identifier]['missing_patches'] = []
                        self._id_to_patch_report[identifier]['missing_patches'].append(patch_record)
                        # Some users have two computers, so distinguish between them using SN
                        self._id_to_patch_report[identifier]['serial_number'] = serial_number
                current_version = None

        # Build out a one row per missing patch list
        # This is CSV friendly since CSV can't represent lists in a row
        for identifier, patch_entry in self._id_to_patch_report.iteritems():
            missing = copy(patch_entry['missing_patches'])
            del patch_entry['missing_patches']
            for patch in missing:
                patch_entry.update(patch)
                self._user_tagged_patch_list.append(patch_entry)

        return self._patches

    # ---- End user interface ----

    def _run_if_none(self, obj):
        """For convenience"""
        if obj is None:
            self._get_computer_data()

    def _counter_if(self, obj, counter):
        """Convenience function"""
        if counter is True:
            return Counter(obj)
        return obj

    def _cache_load(self, cache_file):
        """Cleaner looking caching"""
        with open(join(self._cache_path, cache_file), 'rb') as stream:
            return json_load(stream)

    def _cache_dump(self, obj, cache_file):
        """Cleaner looking caching"""
        try:
            mkdir(self._cache_path)
        except OSError as err:
            if err.errno != EEXIST:
                raise
        with open(join(self._cache_path, cache_file), 'wb') as stream:
            return json_dump(obj, stream)

    def _process_extension_attributes(self, computer, silent=True):
        """Do all of the work required for parsing extension attributes"""
        virtual_machines = []
        general = computer['general']
        location = computer['location']
        realname = location['realname']
        attributes = defaultdict(dict)
        ext_attr = computer['extension_attributes']
        general['simplecasper_parsed_attributes'] = {}

        for attr in ext_attr:
            attr_id = int(attr['id'])
            attr_name = u'{0}'.format(attr['name'])
            attr_type = u'{0}'.format(attr['type'])
            attr_value = u'{0}'.format(attr['value'])
            if attr_type not in ('String', 'Number'):
                raise RuntimeError('unknown attribute type %s' % (
                    attr_type))
            if attr_type == 'Number':
                try:
                    attr_value = int(attr_value)
                except ValueError as err:
                    if silent is False:
                        print('WARN: %s' % (err))
            attributes[attr_name]['value'] = u'{0}'.format(attr_value)
            attributes[attr_name]['type'] = attr_type
            attributes[attr_name]['id'] = attr_id
            general['simplecasper_parsed_attributes'][attr_name] = u'{0}'.format(
                attr_value)
        del computer['extension_attributes']

        vm_settings = [attr for attr in attributes['Virtual Machines']['value'].split(
            '\n') if attr != '']
        vm_count = len(vm_settings)
        if vm_count > 0:
            vm_app = vm_settings[0]
            virtual_machines = vm_settings[1:]
            general['virtual_machines'] = virtual_machines
            self._virtual_machines.extend(virtual_machines)
            self._user_virtual_machines = virtual_machines
            general['vm_app'] = vm_app
        chr_ext = attributes['Chrome Extensions']['value']
        # user_chrome_extensions = [u'{0}'.format(
        #    ext.strip()) for ext in chr_ext.split(',')]
        # general['simplecasper_chrome_extensions'] = chrome_extensions
        self._user_chrome_extensions = [u'{0}'.format(
            ext.strip()) for ext in chr_ext.split(',')]

        self._chrome_extensions.extend(self._user_chrome_extensions)

        crashers = attributes['crashers']['value']
        if crashers not in ('No recent heavy crashers', ''):
            # coreaudiod_2016-11-16-123214_Persons-Name.crash
            # Remove the directory path from the front
            crashers = basename(crashers)
            # Strip out everything except the application name
            crashers = substitute(r'(^.*)_\d{4}-\d{2}-\d{2}-\d{6}_.*$', r'\1',
                                  crashers)
            general['simplecasper_crash_data'] = {'user': realname,
                                                  'app': crashers}
        return

    def _get_computer_data(self, computer_id_list=None, silent=True):
        """Iterative over all computer identifiers and pull the computer object

        This is the main function that parses the computer record that
        is returned by Casper. It is a very large piece of data to describe
        a computer- it includes information about the user, the software, the
        physical hardware, patches, and tons of other junk

        This function creates a few "report" style data structures, such as lists
        of plug-ins, plug-ins per-user, count of plug-in instances, and so on

        An IP address -> user mapping is also created
        """
        def _is_stale(last_contact_time):
            try:
                date = datetime.datetime.strptime(
                    last_contact_time, self.CASPER_DATE_FORMAT)
                days30 = datetime.timedelta(days=30)
                now = datetime.datetime.now()
                month_ago = now - days30
                if date < month_ago:
                    return True
            except ValueError:
                if silent is False:
                    print('WARN: invalid date "%s"' % (last_contact_time))
                return False
            return False

        def _value(obj):
            """Shorthand"""
            return obj['value']

        def _initialize_objects():
            self._applications = []
            self._assets = []
            self._available_updates = []
            self._available_software_updates = []
            self._casper_software = []
            self._chrome_extensions = []
            self._computer_data_list = []
            self._computer_data = {}
            self._installer_swu_software = []
            self._id_to_patch_report = defaultdict()
            self._ip_user_map = defaultdict(dict)
            self._ip_simple_name_map = {}
            self._plugins = []
            self._services = []
            self._user_chrome_extensions = []
            self._user_tagged_applications = []
            self._user_tagged_assets = []
            self._user_tagged_plugins = []
            self._user_tagged_available_updates = []
            self._user_tagged_available_software_updates = []
            self._user_tagged_chrome_extensions = []
            self._user_tagged_patch_list = []
            self._user_tagged_services = []
            self._user_tagged_virtual_machines = []
            self._id_to_user_map = {}
            self._user_to_machine = defaultdict(list)
            self._user_virtual_machines = []
            self._virtual_machines = []

        def _get_user_tag(poll_date, name, email):
            """create a dict used to stamp user information into a dict"""
            tag = {}
            tag['report_date'] = str(datetime.datetime.now())
            tag['poll_date'] = str(poll_date)
            tag['name'] = name
            tag['email'] = email
            return tag

        def _append_tagged(user_obj, global_obj, name, tag):
            """add an object to an empty dict, tag dict with username info"""
            record = {}
            record[name] = user_obj
            record.update(tag)
            global_obj.append(record)

        _initialize_objects()

        if computer_id_list is None:
            if self._computer_id_list is None:
                computer_id_list = self.http_get_computers()
            else:
                computer_id_list = self._computer_id_list

        total_records = len(computer_id_list)
        for progress, comp_id in enumerate(computer_id_list):
            casper_software = []
            cid = str(comp_id)
            user_applications = []
            user_asset = {}
            user_available_updates = []
            user_available_software_updates = []
            user_plugins = []
            user_services = []

            # For development use
            if READ_CACHE is True:
                obj = self._cache_load('%s.json' % (cid))
            else:
                obj = self.http_get_json('%s%s' % (
                    self._url, '%s/%s' % (self.COMPUTERS_ID_ENDPOINT, cid)),
                    auth=(self._user, self._password))
                if UPDATE_CACHE is True:
                    self._cache_dump(obj, '%s.json' % cid)

            self._computer_data[comp_id] = obj
            computer = obj['computer']
            general = computer['general']
            remote_mgmt = general['remote_management']
            # Zero out the sensitive hash info
            remote_mgmt['management_password_sha256'] = '*'
            self._computer_data_list.append(copy(obj))
            location = computer['location']
            username = location['username']
            serial_number = general['serial_number']
            email = location['email_address']
            if email == '':
                email = 'N/A'
            # dept = location['department']
            # building = location['building']
            # position = location['position']
            # Pick a non-empty name
            name = location['real_name']
            if name == '':
                name = general['name']
                if name == '':
                    name = general['realname']
                    if name == '':
                        name = username
                        if name == '':
                            name = email
                            if name == '':
                                name = 'N/A'
            location['canonical_name'] = name
            name = u'{0}'.format(name)
            ip_address = u'{0}'.format(general['last_reported_ip'])
            self._user_to_machine[username].append((ip_address, serial_number))
            last_contact_time = general['last_contact_time']
            _is_stale(last_contact_time)
            self._ip_user_map[ip_address]['realname'] = name
            self._ip_user_map[ip_address]['username'] = username
            self._ip_user_map[ip_address]['last checkin'] = str(last_contact_time)
            self._ip_user_map[ip_address]['freshness'] = str(datetime.datetime.now())
            remote_mgmt['management_password_sha256'] = ''
            # mgmt_user = remote_mgmt['management_username']
            hardware = computer['hardware']
            user_asset['make'] = hardware['make']
            user_asset['model'] = hardware['model']
            user_asset['model_id'] = hardware['model_identifier']
            user_asset['os_name'] = hardware['os_name']
            user_asset['os_version'] = hardware['os_version']
            user_asset['os_build'] = hardware['os_build']
            user_asset['disk_encryption'] = hardware['disk_encryption_configuration']
            user_asset['managed'] = remote_mgmt['managed']
            general['asset'] = user_asset

            software = computer['software']
            casper_software = [pkg for pkg in software['installed_by_casper']]
            installer_swu_software = [pkg for pkg in software['installed_by_installer_swu']]
            user_available_software_updates = ['{0}'.format(
                upd) for upd in software['available_software_updates']]

            try:
                stdout.write('\r' + ' ' * 80)
                stdout.write(u'\r{0}/{1} computers processed ({2}) ...'.format(
                    progress, total_records, name))
                stdout.flush()
            except UnicodeDecodeError as err:
                err = err
            for dmg_name in casper_software:
                self._casper_software.append(dmg_name)

            for swu_name in installer_swu_software:
                swu_name = swu_name.strip()
                self._installer_swu_software.append(swu_name)

            for key, upd in software['available_updates'].iteritems():
                assert key == 'update'
                update = {}
                update_name = upd['name']
                package_name = upd['package_name']
                version = upd['version']
                update['name'] = '{0}'.format(str(update_name))
                update['package_name'] = '{0}'.format(str(package_name))
                update['version'] = '{0}'.format(str(version))
                self._available_updates.append(update)
                user_available_updates.append(update)

            for svc in software['running_services']:
                # Strip of a GUID at end of service name
                svc = substitute(
                    r'(^.*)\.[0-9A-F]{8}(-[0-9A-F]{4}){4}[0-9A-F]{8}$',
                    r'\1', svc)
                # Strip leading hex from service name
                svc = substitute(
                    r'^0x[0-9a-f]{1,16}\.(.*)$',
                    r'\1', svc)
                self._services.append(svc)
                user_services.append(svc)

            apps = software['applications']
            chrome_version = 'N/A'
            for app in apps:
                application = {}
                for i in app:
                    if i is not None:
                        application['name'] = u'{0}'.format(app['name'])
                        application['path'] = u'{0}'.format(app['path'])
                        application['version'] = u'{0}'.format(app['version'])
                        self._applications.append(application)
                        user_applications.append(application)
                        if application['name'] == 'Google Chrome.app':
                            chrome_version = application['version']
            plugs = software['plugins']
            for plug in plugs:
                plugin = {}
                if plug is not None:
                    plugin['name'] = u'{0}'.format(plug['name'])
                    plugin['path'] = u'{0}'.format(plug['path'])
                    plugin['version'] = u'{0}'.format(plug['version'])
                    self._plugins.append(plugin)
                    user_plugins.append(plugin)

            self._process_extension_attributes(computer)

            self._ip_simple_name_map[u'{0}'.format(ip_address)] = u'{0}'.format(name)
            self._available_software_updates.extend(user_available_software_updates)
            self._casper_software.extend(casper_software)
            self._assets.append(user_asset)

            tag = _get_user_tag(str(last_contact_time), name, email)

            _append_tagged(
                self._user_virtual_machines,
                self._user_tagged_virtual_machines,
                'virtual machines',
                tag)
            _append_tagged(
                user_asset,
                self._user_tagged_assets,
                'asset',
                tag)
            _append_tagged(
                user_applications,
                self._user_tagged_applications,
                'applications',
                tag)
            _append_tagged(
                user_plugins,
                self._user_tagged_plugins,
                'plugins',
                tag)
            _append_tagged(
                user_available_updates,
                self._user_tagged_available_updates,
                'available_updates',
                tag)
            # What's the difference between available updates and available 'software' updates?
            # No idea... go figure it out yourself
            _append_tagged(
                user_available_software_updates,
                self._user_tagged_available_software_updates,
                'available_software_updates',
                tag)
            _append_tagged(
                user_services,
                self._user_tagged_services,
                'services',
                tag)
            tag['chrome_version'] = chrome_version
            _append_tagged(
                self._user_chrome_extensions,
                self._user_tagged_chrome_extensions,
                'chrome extensions',
                tag)
            del tag['chrome_version']
        print('\r%d/%d computers processed, complete!' % (
            total_records, total_records) + ' ' * 80)
