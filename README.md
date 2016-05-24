# xblock-dalite
XBlock for Dalite-NG

## Set-up instructions 

This XBlock uses lti passports in following format: 

    [passport-id]:dalite-xblock:[base64 encoded data]
    
eg. 

    dalite-ng:dalite-xblock:aHR0cDovLzE5Mi4xNjguMzMuMToxMDEwMDthbHBoYTtiZXRh
    
where: 

* `passport-id` is unique identifier of this passport
* `dalite-xblock` is a constant string.
* `base64 encoded data` is base64 encoded string. 

When `base64 encoded data` is decoded it contains three fields delimited by `;`:
 
* dalite base url (with protocol, and port if applicable): `http://192.168.33.1:10100`. This entry does not 
  contain `/lti/` path. 
* lti client key
* lti client secret

To generate passports in this format you might use `tools/generate_dalite_passport.py` script (can be run on a 
plain python2.7 interpreter): 

    $ export PYTHONPATH=$(pwd)
    $ python tools/generate_dalite_passport.py --dalite-url http://192.168.33.1:10100 --passport-id dalite-ng --lti-key alpha --lti-secret beta
    "dalite-ng:dalite-xblock:aHR0cDovLzE5Mi4xNjguMzMuMToxMDEwMDthbHBoYTtiZXRh"
