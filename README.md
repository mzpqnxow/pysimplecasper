## pysimplecasper

See the ```driver.py``` file for usage information

## Notes

You will need a username/password to use the Casper API. These should be set in your environment as:
  * CASPER_USER
  * CASPER_PASS
  * CASPER_HOST

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

  * /JSSResource/computers
  * /JSSResource/computers/id/<id>
  * /JSSResource/patches
  * /JSSResource/patches/id/<id>

The way the Casper API works is pretty straightforward. Generally you make one requests to get a list of identifiers, which are integers. You then make a series of requests, one per identifier, to get data for a specific resource, like a computer or a patch. While the returned data for patches is relatively small and simple, computer records are significant in size and somewhat complex, so they must be massaged a little to make all of the data useful
