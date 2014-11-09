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



class BharatMatrimony(Crawler):
    """
    This class handles crawling and extraction of data from BharatMatrimony.com, a popular site
    for finding and managing matrimonial aliances. It is derived from class Crawler.
    """
    def __init__(self):
        self.__class__.DEBUG = True
        super(BharatMatrimony, self).__init__("../../conf/snoop.cnf", "https://www.bharatmatrimony.com/", "https://www.bharatmatrimony.com/")
        self.availableCreds = self.loadCredentials("bharatmatrimony")


    def doLogin(self, username="", password=""):
        soup = BeautifulSoup(self.currentPageContent)
        loginForm = soup.find("form", {'name' : 'Login'})
        if not loginForm:
            print "Could not find the login form in the page. Please ensure that we are on the correct page.\n\n"
            return(None)
        loginAction = loginForm['action']
        loginMethod = loginForm['method']
        self.requestUrl = loginAction
        if not self.__class__._isAbsoluteUrl(self.requestUrl):
            self.requestUrl = self.baseUrl + self.requestUrl

        credsLen = self.availableCreds.__len__()
        randomIndex = random.randint(0, credsLen - 1)

        bhmUsernames = self.availableCreds.keys()
        self.siteUsername = bhmUsernames[randomIndex]
        self.sitePassword = self.availableCreds[self.siteUsername]
        
        usernameFieldname = loginForm.find("input", {'type' : 'text'})['name']
        passwordFieldname = loginForm.find("input", {'type' : 'password'})['name']
        self.postData = {usernameFieldname : self.siteUsername, passwordFieldname : self.sitePassword, }
        hiddenFields = loginForm.find("input", {'type' : 'hidden'})
        for hdnfld in hiddenFields:
            fldname = ""
            fldvalue = ""
            if hdnfld.has_key('name'):
                fldname = hdnfld['name']
            elif hdnfld.has_key('id'):
                fldname = hdnfld['id']
            else:
                continue
            if hdnfld.has_key('value'):
                fldvalue = hdnfld['value']
            else:
                pass
            self.postData[fldname] = fldvalue
        checkboxField = loginForm.find("input", {'type' : 'checkbox'})
        checkboxname, checkboxvalue = "", ""
        if checkboxField.has_key('name'):
            checkboxname = checkboxField['name']
        if checkboxField.has_key('value'):
            checkboxvalue = checkboxField['value']
        self.postData[checkboxname] = checkboxvalue
        self.postData['TEMPPASSWD1'] = 'Password'
        encodedData = urllib.urlencode(self.postData)
        self.pageRequest = urllib2.Request(self.requestUrl, encodedData, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
        except:
            print "Failed to make the login request - Error: %s\n\n"%sys.exc_info()[1].__str__()
            return(None)
        return(self.currentPageContent)


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
    bhm = BharatMatrimony()
    pageContent = bhm.doLogin()
    if pageContent:
        ff = open("../html/bharatmatrimony.html", "w")
        ff.write(pageContent)
        ff.close()
    if not bhm.assertLogin("Sign Out"):
        print "Could not log in"
        sys.exit()
    else:
        print "Successfully logged in as %s\n"%bhm.siteUsername
    bhm.conductSearch(searchEntity)
    
