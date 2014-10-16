import os, sys, re, time, gzip
import urllib, urllib2, httplib
from BeautifulSoup import BeautifulSoup
from urlparse import urlparse, urlsplit
import StringIO
import mimetypes, mimetools
from ConfigParser import ConfigParser
sys.path.append("..")
from Crawler import Crawler



class facebook(Crawler):

    def __init__(self):
        self.__class__.DEBUG = True
        super(facebook, self).__init__("../conf/snoop.cnf", "http://www.facebook.com/", "https://www.facebook.com/login.php?login_attempt=1")
        self.availableCreds = self.loadCredentials("facebook")
        print self.availableCreds
        














if __name__ == "__main__":
    facebook = facebook()
