import os, sys, re, time, gzip
import datetime
from django.template import RequestContext
from django.template.loader import get_template
from django.template import Template, Context
from django.http import HttpResponse

#from django.contrib.gis.geoip import GeoIP
from django.contrib.gis.geoip.base import GeoIP
import websnoop.settings as settings


def getGeolocationFromIP(ipaddr):
    g = GeoIP()
    request_src  = g.city(ipaddr)
    logRequest(request_src)
    try:
        return (request_src['city'], request_src['country_name'])
    except:
        return ('', '')


"""
Dump the location struct returned by a GeoIP 'city()' call into the mongo db database.
"""
def logRequest(loc_struct):
    pass


def inputForm(csrftoken="", loginsession=""):
    """
    Display the search inputs form
    """
    t = get_template("templates/inputform.html")
    formhtml = t.render(Context({'csrftoken' : csrftoken, 'loginsession' : loginsession}))
    return(formhtml)


def pageheader(title, uname='guest'):
    """
    Utility routine to write the header part of the web interface.
    """
    t = get_template("templates/pageheader.html")
    page = pagejs()
    datejs = datepickerjs("entitydob")
    cachecontrolhtml = cachecontrolheaders()
    bootstraphtml = bootstrapincludes()
    htmlcontent = t.render(Context({'title' : title, 'pagejs' : page, 'datejs' : datejs, 'cachecontrolhtml' : cachecontrolhtml, 'bootstraphtml' : bootstraphtml, 'username' : uname }))
    return(htmlcontent)


def pagejs():
    """
    Utility routine to handle the javascript and prototype.js activities.
    It gathers the inputs and makes prototype.js based ajax calls to the
    URLs specified by the user as well as the social networking sites
    supported by snoop.
    """
    validationjs = inputvalidationjs()
    
    t = get_template("templates/pagejs.html")
    htmlcontent = validationjs + t.render(Context({  }))
    return (htmlcontent)


def bootstrapincludes():
    """
    Utility routine for the date picker part of the report generation interface.
    """
    t = get_template("templates/bootstrapincludes.html")
    htmlcontent = t.render(Context({}))
    return(htmlcontent)


def cachecontrolheaders():
    """
    Utility routine to write the cache control headers of the report generation interface.
    """
    t = get_template("templates/cachecontrol.html")
    htmlcontent = t.render(Context({}))
    return(htmlcontent)


def inputvalidationjs():
    """
    Utility routine to write the input validation javascript. The javascript code
    will validate the input from the user by checking for the existence of valid values
    for all required fields. It will return 1 for success and 0
    for failure. The javascript/prototype.js code to crawl the social networking and
    user submitted URLs will be fired on the basis of its outcome.
    """
    t = get_template("templates/inputvalidationjs.html")
    htmlcontent = t.render(Context({}))
    return(htmlcontent)


def pagefooter():
    """
    Utility routine to write the footer part of the report generation interface.
    """
    t = get_template("templates/pagefooter.html")
    htmlcontent = t.render(Context({}))
    return htmlcontent


def datepickerjs(targetfieldname1, targetfieldname2=None, targetfieldname3=None):
    """
    Utility routine to write the date picker functionality of the report generation interface.
    """
    t = get_template("templates/datepickerjs.html")
    htmlcontent = t.render(Context({'targetfieldname1' : targetfieldname1, 'targetfieldname2' : targetfieldname2, 'targetfieldname3' : targetfieldname3}))
    return(htmlcontent)
