from django.shortcuts import render
import os, sys, re, time, gzip
import datetime
from collections import OrderedDict
from django.http import HttpResponse

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import hashers
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
#from django.contrib.gis.utils import GeoIP
from django.contrib.gis.geoip.base import GeoIP
from django.template import RequestContext
from django.template.loader import get_template
from django.template import Template, Context
from django.conf import settings

import websnoop.settings as snoopsettings
from webscrape import mongo_conn




# Create your views here.


def getPages(request):
    pass


def getInputs(request):
    csrftoken = request.POST[u'csrfmiddlewaretoken']
    result = 0
    if not os.path.exists(snoopsettings.IMAGE_UPLOAD_DIR + csrftoken):
        os.makedirs(snoopsettings.IMAGE_UPLOAD_DIR + csrftoken, 0777) # Create the image directory with the csrftoken string
    #print request.POST.keys()
    if request.FILES.has_key('frontimage'):
        frontimagefile = request.FILES['frontimage']
        frontimagefilename = snoopsettings.IMAGE_UPLOAD_DIR + csrftoken + os.path.sep + 'frontimage' + os.path.splitext(frontimagefile.name)[1]
        try:
            with open(frontimagefilename, 'wb+') as destination:
                for chunk in frontimagefile.chunks():
                    destination.write(chunk)
            result += 1
        except:
            pass
    else:
        request.FILES['frontimage'] = ""
        frontimagefilename = ""
    if request.FILES.has_key('profileimage'):
        profileimagefile = request.FILES['profileimage']
        profileimagefilename = snoopsettings.IMAGE_UPLOAD_DIR + csrftoken + os.path.sep + 'profileimage' + os.path.splitext(profileimagefile.name)[1]
        try:
            with open(profileimagefilename, 'wb+') as destination:
                for chunk in profileimagefile.chunks():
                    destination.write(chunk)
            result += 2
        except:
            pass
    else:
        request.FILES['profileimage'] = ""
        profileimagefilename = ""
    if request.FILES.has_key('elevationimage'):
        elevationimagefile = request.FILES['elevationimage']
        elevationimagefilename = snoopsettings.IMAGE_UPLOAD_DIR + csrftoken + os.path.sep + 'elevationimage' + os.path.splitext(elevationimagefile.name)[1]
        try:
            with open(elevationimagefilename, 'wb+') as destination:
                for chunk in elevationimagefile.chunks():
                    destination.write(chunk)
            result += 3
        except:
            pass
    else:
        request.FILES['elevationimage'] = ""
        elevationimagefilename = ""
    
    # Retrieve all the form fields/values, start creating a mongo db document, and
    # place the tasks of searching social media in the celery task queue.
    db = snoopsettings.MONGO_DBS['snoopinfo']['name']
    username = snoopsettings.MONGO_DBS['snoopinfo']['user']
    password = snoopsettings.MONGO_DBS['snoopinfo']['pass']
    collection = snoopsettings.MONGO_DBS['snoopinfo']['collection']
    db = mongo_conn[db]

    collection = db[collection]
    db.collection.insert({'entityname' : request.POST['entityname'], 'permanentaddress' : request.POST['permanentaddress'], 'identificationdetail' : request.POST['identificationdetail'], 'searchcities' : request.POST['searchcities'], 'searchcountries' : request.POST['searchcountries'], 'entitydescription' : request.POST['entitydescription'],\
                          'emailids' : request.POST['emailids'], 'phonenumbers' : request.POST['phonenumbers'], 'websiteurls' : request.POST['websiteurls'], 'facebookhandles' : request.POST['facebookhandles'], 'linkedinhandles' : request.POST['linkedinhandles'], 'twitterhashtags' : request.POST['twitterhashtags'], 'googleplushandles' : request.POST['googleplushandles'],\
                          'whatsapphandles' : request.POST['whatsapphandles'], 'instagramhandles' : request.POST['instagramhandles'], 'socialnetworkhandle' : request.POST['socialnetworkhandle'], 'neighborhood' : request.POST['neighborhood'], 'searchlocality' : request.POST['searchlocality'], 'eventperiod' : request.POST['eventperiod'], 'associatedevent' : request.POST['associatedevent'],\
                          'eventplace' : request.POST['eventplace'], 'entitydob' : request.POST['entitydob'], 'occupation' : request.POST['occupation'], 'infourls' : request.POST['infourls'], 'csrfmiddlewaretoken' : request.POST['csrfmiddlewaretoken'], 'loginsession' : request.POST['loginsession'], 'frontimage' : frontimagefilename, 'profileimage' : profileimagefilename, 'elevationimage' : elevationimagefilename})
    # So, now data has been safely tucked away in the mongo db... So we may now concentrate on creating a task on each of the soc. net. queues.
    return(HttpResponse(result.__str__()))

