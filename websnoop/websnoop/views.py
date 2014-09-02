from django.conf import settings
from django.core.cache import cache


import os
import logging
import datetime
import cPickle




def defaultHandler(request, params):
    responseHtml = pageHeader("some page title")
    return(HttpResponse(responseHtml))


 
