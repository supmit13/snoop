from django.shortcuts import render
import os, sys, re, time, gzip
import datetime
from collections import OrderedDict
from django.http import HttpResponse

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import hashers
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.contrib.gis.utils import GeoIP
from django.template import RequestContext
from django.template.loader import get_template
from django.template import Template, Context
from django.conf import settings




# Create your views here.

def getInputs(request):
    pass


def getPages(request):
    pass
