## pysimplecasper

See the ```driver.py``` file for usage information

## Before using

You will need a username/password to use the Casper API and you will need to specify the FQDN of your Casper endpoint. These should be set in your environment as follows:

  * ```CASPER_USER```
  * ```CASPER_PASS```
  * ```CASPER_HOST```

I recommend using something like this

```
(venv) user@host:~/pysimplecasper.git$ cat ~/.casper_creds 
export CASPER_USER=someuser
export CASPER_PASS=somepassword
export CASPER_HOST=casper.yourdomain.com
(venv) user@host:~/pysimplecasper.git$ source ~/.casper_creds 
(venv) user@host:~/pysimplecasper.git$ ./driver.py
```

## Stability, maturity

This code is not production quality. It is really just a glorified snippet/example. The only Casper API endpoints it current uses:

  * ```/JSSResource/computers```
  * ```/JSSResource/computers/id/<id>```
  * ```/JSSResource/patches```
  * ```/JSSResource/patches/id/<id>```

The way the Casper API works is pretty straightforward. Generally you make one request to get a list of identifiers, which are integers. You then make a series of requests, one per identifier, to get data for a specific resource, like a `computer` or a `patch`. While the returned data for each patch record is relatively small and simple, computer records are somewhat significant in size and somewhat complex in structure, so they must be massaged a little to make all of the data useful. The code in simplecasper builds a bunch of lookup tables and lists that are easy to dump to CSV or JSON files. Optionally they can do things like report ```Counter``` style dictionaries (for example, list all applications on known by Casper and list the count of instances in a dict)

## Extending

If you want to extend this, you can find out about each of the (many) Casper API endpoints by visiting http://casper.endpoint.fqdn/api. Note that by default API requests will return XML. If you prefer JSON (who doesn't?) than you will need to include an ```Accept: application/json``` header as is done in ```simplecasper/api.py``` in the CasperAPI class. While there are many API endpoints, many of them are really just for querying specific subsets of the ```computers``` endpoint. It may be easier to just process the computers result to strip out the data you want as opposed to adding an interface for each API endpoint. YMMV.

## Summary of driver.py output and how the data might be used

The following files are output by ```driver.py```, which uses the ```CasperAPI``` class:

* ```user_chrome_extensions.json``` - A list of Chrome Extensions per-user, this can be used to ensure there are not any questionable or otherwise disallowed Chrome Extensions on each of your user's machines
* ```user_patches.json``` - A list of patches that each user has applied to their respective machines, useful for identifying machines that are out of compliance. It is not necessary to understand what each patch is, instead you can just compare each patch list with a known good patch list, taken from a computer that has been manually patched up to the latest
* ```user_applications.json``` - A list of all applications installed on each of your user's machines. Useful in the same way as the Chrome Extension list is useful- identify non-compliant packages, forbidden by written policy but not controlled by hard technical policy
* ```user_plugins.json``` - Same as Chrome Extensions but for plug-ins
* ```user_available_software_updates.json``` - The inverse of user_patches.json, this shows patches that are *not* applied but probably should be, per-user machine
* ```ip_to_user_object.json``` - Given an IP address, return the ```computer``` object. You can then process the ```computer``` object to pull out any data you may need
* ```ip_to_username.json``` - Given an IP address, return the ```username``` for that computer
* ```user_services.json``` - Return a list of all services active on each user's computer
* ```services_counter.json``` - Return a Counter() object of services found across the entire fleet. For example, you may want to investigate services that are only found on a single system as it can be considered anomalous. You can also determine the popularity of certain services to gauge exposure to a vulnerability in that service
* ```chrome_extensions_counter.json``` - Same as ```services_counter.json``` but for Chrome Extensions
* ```user_assets.json``` - Return a summary of "asset" information per-user computer, such as make, model, etc.
* ```user_virtual_machines.json``` - Return a list of installed virtual machines on each user's computer
* ```virtual_machines_counter.json``` - The summarized fleet-wide view of virtual machines with a counter next to each virtual machine name
* ```user_missing_patches``` - Similar to ```user_available_software_updates.json```, includes a small subset of user information along with a list of missing patches for a computer