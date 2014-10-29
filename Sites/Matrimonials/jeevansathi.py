import os, sys, re, time, gzip
import urllib, urllib2, httplib
from BeautifulSoup import BeautifulSoup
from urlparse import urlparse, urlsplit
import StringIO
import mimetypes, mimetools
from ConfigParser import ConfigParser
sys.path.append("../..")
from Crawler import Crawler
import random



class Jeevansathi(Crawler):
    """
    This class handles crawling and extraction of data from Jeevansathi.com, a popular site
    for finding and managing matrimonial aliances. It is derived from class Crawler.
    """
    def __init__(self):
        self.__class__.DEBUG = True
        super(Jeevansathi, self).__init__("../../conf/snoop.cnf", "http://www.jeevansathi.com/", "http://www.jeevansathi.com/")
        self.availableCreds = self.loadCredentials("jeevansathi")


    def doLogin(self, username="", password=""):
        soup = BeautifulSoup(self.currentPageContent.encode('utf-8'))
        if not soup:
            print "Could not find any HTML content in currentPageContent...\nQuitting.\n"
            return(None)
        loginForm = soup.find("form", {'name' : 'login'})
        if  not loginForm:
            print "Could not find login form. Check to see if we are on the correct page.\n"
            return(None)
        loginAction = loginForm["action"]
        if not self.__class__._isAbsoluteUrl(loginAction):
            loginAction = self.baseUrl + loginAction

        self.requestUrl = loginAction
        credsLen = self.availableCreds.__len__()
        randomIndex = random.randint(0, credsLen - 1)
        jsvnUsernames = self.availableCreds.keys()
        self.siteUsername = jsvnUsernames[randomIndex]
        self.sitePassword = self.availableCreds[self.siteUsername]
        
        self.postData = {}
        usernameField = loginForm.find("input", {'type' : 'text'})
        usernameFieldName = usernameField['name']
        passwordField = loginForm.find("input", {'type' : 'password'})
        passwordFieldName = passwordField['name']
        otherHiddenFields = loginForm.findAll("input", {'type' : 'hidden'})
        self.postData = {usernameFieldName : self.siteUsername, passwordFieldName : self.sitePassword}
        for hfld in otherHiddenFields:
            hfldName = ""
            if hfld.has_key('name'):
                hfldName = hfld['name']
            elif hfld.has_key('id'):
                hfldName = hfld['id']
            else:
                continue
            hfldValue = ""
            if hfld.has_key('value'):
                hfldValue = hfld['value']
            self.postData[hfldName] = hfldValue
        encodedData = urllib.urlencode(self.postData)
        self.pageRequest = urllib2.Request(self.requestUrl, encodedData, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.sessionCookies = self.__class__._getCookieFromResponse(self.pageResponse)
            self.httpHeaders["Cookie"] += self.sessionCookies
            self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
            self.httpHeaders['Referer'] = self.requestUrl
        except:
            print "Could not make the POST request for login successfully"
            return(None)
        return(self.currentPageContent)


    def getPageFromIframe(self):
        pass


    def conductSearch(self, searchEntity):
        pass


    def buildGraph(self):
        pass


    def parseSearchHtml(self):
        """
        Parses the HTML content in the object's currentPageContent attribute and sets the
        object's 'searchResults' attribute with the resultant dict. Returns the number of
        matches found.
        """
        pass


if __name__ == "__main__":
    searchEntity = sys.argv[1]
    jvns = Jeevansathi()
    pageContent = jvns.doLogin()
    if pageContent:
        ff = open("../html/jeevansathilogin.html", "w")
        ff.write(pageContent)
        ff.close()
    if not jvns.assertLogin("Logout"):
        print "Could not log in"
        sys.exit()
    else:
        print "Successfully logged in as %s\n"%jvns.siteUsername
    jvns.conductSearch(searchEntity)
    
