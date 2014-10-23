import os, sys, re, time, gzip
import urllib, urllib2, httplib
from BeautifulSoup import BeautifulSoup
from urlparse import urlparse, urlsplit
import StringIO
import mimetypes, mimetools
from ConfigParser import ConfigParser
sys.path.append("..")
from Crawler import Crawler
import random



class GooglePlus(Crawler):
    """
    This class handles crawling and extraction of data from google+.
    It is derived from class Crawler.
    """
    def __init__(self):
        self.__class__.DEBUG = True
        super(GooglePlus, self).__init__("../conf/snoop.cnf", "https://plus.google.com/", "https://plus.google.com/")
        self.availableCreds = self.loadCredentials("googleplus")


    def doLogin(self, username="", password=""):
        pass


    def conductSearch(self, searchEntity):
        pass


    def buildGraph(self):
        pass




if __name__ == "__main__":
    searchEntity = sys.argv[1]
    gplus = GooglePlus()
    pageContent = gplus.doLogin()
    if pageContent:
        ff = open("googlepluslogin.html", "w")
        ff.write(pageContent)
        ff.close()
    if not gplus.assertLogin("Sign Out"):
        print "Could not log in"
        sys.exit()
    else:
        print "Successfully logged in as %s\n"%gplus.siteUsername
    gplus.conductSearch(searchEntity)
    
