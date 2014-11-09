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
        print "Trying to login as %s at '%s'...\n\n"%(self.siteUsername, self.requestUrl)
        self.pageRequest = urllib2.Request(self.requestUrl, encodedData, self.httpHeaders)
        if self.__class__.DEBUG:
            print "Encoded Data: %s\n\n"%encodedData
        while True:
            try:
                self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            except:
                print "Failed to make the login request to '%s' - Error: %s\n\n"%(self.requestUrl, sys.exc_info()[1].__str__())
                return(None)
            responseHeaders = self.pageResponse.info()
            if responseHeaders.has_key('Set-Cookie') and responseHeaders['Set-Cookie'] is not None:
                self.sessionCookies = responseHeaders['Set-Cookie']
                cookiesList = self.sessionCookies.split(",")
                for cookie in cookiesList:
                    if type(cookie) == str and type(self.httpHeaders['Cookie']) == str:
                        self.httpHeaders['Cookie'] += "; " + cookie
                if self.httpHeaders['Cookie'] is not None:
                    self._processCookie()
            self.httpHeaders['Referer'] = self.requestUrl
            if responseHeaders.has_key('Location'):
                self.requestUrl = responseHeaders['Location']
                if not self.__class__._isAbsoluteUrl(self.requestUrl):
                    self.requestUrl = "https://secure.bharatmatrimony.com" + self.requestUrl
                self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
            else:
                self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
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


    def _processCookie(self):
        """
        Method to remove extra semicolons and repeatitive keys in cookies. To be used internally.
        This is slightly different from the other implementation (in facebook.py and twitter.py)
        because it is capable of handling '=' character in the cookie values.
        """
        self.sessionCookies = self.httpHeaders['Cookie']
        cookies = self.sessionCookies.split(";")
        cookiesDict = {}
        for cookie in cookies:
            cookie = re.sub(re.compile(r"\s+$"), "", cookie)
            cookie = re.sub(re.compile(r"^\s+"), "", cookie)
            cookie = re.sub(self.__class__.multipleWhiteSpacesPattern, "", cookie)
            if cookie == "":
                continue
            elif re.search(re.compile(r"Max\-Age=([^;]+)"), cookie) or re.search(re.compile(r"=\"?delete"), cookie) or re.search(re.compile(r"[pP]ath=[^;]+"), cookie) or re.search(re.compile(r"[eE]xpires"), cookie) or re.search(re.compile(r"Secure"), cookie) or re.search(re.compile(r"HttpOnly"), cookie) or re.search(re.compile(r"Priority=HIGH", re.IGNORECASE), cookie) or re.search(re.compile(r"[dD]omain"), cookie):
                continue
            else:
                cookieparts = cookie.split("=")
                if cookieparts.__len__() < 2:
                    continue
                cookiesDict[cookieparts[0]] = cookieparts[1]
                if cookieparts.__len__() > 2:
                    for j in range(2, cookieparts.__len__()):
                        cookiesDict[cookieparts[0]] += "=" + cookieparts[j]
        self.sessionCookies = ""
        for cookie in cookiesDict.keys():
            self.sessionCookies += cookie + "=" + cookiesDict[cookie] + ";"
        self.httpHeaders['Cookie'] = self.sessionCookies
        return(self.sessionCookies)


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
    
