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



class Wayn(Crawler):
    """
    This class handles crawling and extraction of data from wayn.
    It is derived from class Crawler.
    """
    def __init__(self):
        self.__class__.DEBUG = True
        super(Wayn, self).__init__("../conf/snoop.cnf", "https://www.wayn.com/", "https://www.wayn.com/")
        self.availableCreds = self.loadCredentials("wayn")


    def doLogin(self, username="", password=""):
        pass


    def conductSearch(self, searchEntity):
        pass


    def buildGraph(self):
        pass




if __name__ == "__main__":
    searchEntity = sys.argv[1]
    wayn = Wayn()
    pageContent = wayn.doLogin()
    if pageContent:
        ff = open("waynlogin.html", "w")
        ff.write(pageContent)
        ff.close()
    if not wayn.assertLogin("Sign Out"):
        print "Could not log in"
        sys.exit()
    else:
        print "Successfully logged in as %s\n"%wayn.siteUsername
    wayn.conductSearch(searchEntity)
    
