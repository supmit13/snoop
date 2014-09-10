import os, sys, re, time
from datetime import datetime

from django.template import RequestContext
from django.template.loader import get_template
from django.template import Template, Context
from django.http import HttpResponse
from websnoop.utils import pageheader, pagejs, bootstrapincludes, cachecontrolheaders, inputvalidationjs, pagefooter, datepickerjs, getGeolocationFromIP, inputForm

from websnoop import settings

def showFinderForm(request):
    formPageTitle = "Add Customizations"
    srcIP = request.META['REMOTE_ADDR']
    loc_tup = getGeolocationFromIP(srcIP)

    topMessage = "Hi Guest, looks like you are from %s in %s. Looking for someone? Welcome to snoop!"%(loc_tup[0], loc_tup[1])

    html = pageheader(topMessage)
    helpMessage = """<center><b>In order to help us help you, could you please furnish some relevant
                information on the object of your quest? We promise you that the information you furnish here will not
                be used to associate you with any activity on this website.</b></center>"""
    html += helpMessage
