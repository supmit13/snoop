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
import md5, base64



class YellowPages(Crawler):
    """
    This class handles crawling and extraction of data from wayn.
    It is derived from class Crawler.
    """
    def __init__(self):
        self.__class__.DEBUG = True
        super(YellowPages, self).__init__("../../conf/snoop.cnf", "https://www.yellowpages.com/", "https://www.yellowpages.com/login")
        self.availableCreds = self.loadCredentials("yellowpages")


    def _preLoginQueries(self):
        soup = BeautifulSoup(self.currentPageContent)
        anchorTag = soup.find("a")
        ahref = ""
        if anchorTag is None:
            print "Could not find the first redirection to the login page.\n"
            return(None)
        print "Trying to get the login page....\n\n"
        ahref = anchorTag['href']
        ahref = ahref.replace("&amp;", "&")
        self.requestUrl = ahref
        self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.httpHeaders['Referer'] = self.requestUrl
        except:
            print "Could not get to the page redirected to '%s'. Error: %s\n"%(self.requestUrl, sys.exc_info()[1].__str__())
            return(None)
        # ================ First Redirection Done ============= #
        
        responseHeaders = self.pageResponse.info()
        if responseHeaders.has_key('Set-Cookie'):
            self.httpHeaders['Cookie'] += "; " + responseHeaders['Set-Cookie']
        if responseHeaders.has_key('Location'):
            self.requestUrl = responseHeaders['Location']
        else:
            print "Couldn't find the redirection #2 URL.\n"
            return(None)
        if not self.__class__._isAbsoluteUrl(self.requestUrl):
            self.requestUrl = "https://accounts.yellowpages.com" + self.requestUrl
        self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            responseHeaders = self.pageResponse.info()
            if responseHeaders.has_key('Set-Cookie'):
                self.httpHeaders["Cookie"] += "; " + responseHeaders['Set-Cookie']
        except:
            print "Could not make the redirection request #2 to '%s'\n"%self.requestUrl
            return(None)
        # ================ Second Redirection Done ============= #

        if responseHeaders.has_key("Location"):
            self.requestUrl = responseHeaders['Location']
        else:
            print "Could not get the 3rd redirection URL. Last request sent to '%s'\n"%self.requestUrl
            return(None)
        self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            responseHeaders = self.pageResponse.info()
            if responseHeaders.has_key('Set-Cookie'):
                self.httpHeaders["Cookie"] += "; " + responseHeaders['Set-Cookie']
            self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
            self.httpHeaders['Referer'] = self.requestUrl
        except:
            print "Could not make the 3rd redirection.\n"
            return(None)
        # ================ Third Redirection Done ============= #
        print "Retrieved login page...\n\n"
        
        return(self.currentPageContent)


    def doLogin(self, username="", password=""):
        self.currentPageContent = self._preLoginQueries()
        print "Filling up login form ... \n\n"
        soup = BeautifulSoup(self.currentPageContent)
        loginForm = soup.find("form")
        usernameFieldname = loginForm.find("input", {'type' : 'text'})['name']
        passwordFieldname  = loginForm.find("input", {'type' : 'password'})['name']
        otherFields = loginForm.findAll("input")
        loginAction = loginForm['action']
        if not self.__class__._isAbsoluteUrl(loginAction):
            self.requestUrl = 'https://accounts.yellowpages.com' + loginAction
        else:
            self.requestUrl = loginAction

        credsLen = self.availableCreds.__len__()
        randomIndex = random.randint(0, credsLen - 1)
        ypUsernames = self.availableCreds.keys()
        self.siteUsername = ypUsernames[randomIndex]
        self.sitePassword = self.availableCreds[self.siteUsername]
        
        self.postData = {usernameFieldname : self.siteUsername, passwordFieldname : self.sitePassword, }
        for fld in otherFields:
            if not fld.has_key('name') or not fld.has_key('value'):
                continue
            fieldname = fld['name']
            fieldvalue = fld['value']
            self.postData[fieldname] = fieldvalue
        encodedData = urllib.urlencode(self.postData)
        self._processCookie()
        httpHeaders = {}
        for hdr in self.httpHeaders.keys():
            httpHeaders[hdr] = self.httpHeaders[hdr]
        httpHeaders['Content-Type'] = 'application/x-www-form-urlencoded'
        httpHeaders['Content-Length'] = encodedData.__len__()
        httpHeaders['Host'] = 'accounts.yellowpages.com'
        print "Making login request (to '%s')...\n\n"%self.requestUrl
        self.pageRequest = urllib2.Request(self.requestUrl, encodedData, httpHeaders)
        if self.__class__.DEBUG:
            print "Cookies: " + httpHeaders['Cookie'] + "\n\n"
            print "Sending data %s \n\n"%encodedData
        self.httpHeaders['Referer'] = self.requestUrl # Will be used in the redirected requests
        while True:
            try:
                self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
                responseHeaders = self.pageResponse.info()
                self.httpHeaders['Host'] = "accounts.yellowpages.com"
                if responseHeaders.has_key('Set-Cookie'):
                    cookiesList = responseHeaders['Set-Cookie'].split(",") # We are expecting multiple 'Set-Cookie' headers...
                    for cookie in cookiesList:
                        self.httpHeaders['Cookie'] += "; " + cookie
                    self._processCookie()
                if responseHeaders.has_key('Location'):
                    self.requestUrl = responseHeaders['Location'];
                    if self.requestUrl == '/':
                        self.requestUrl = "http://www.yellowpages.com/"
                    if re.search(re.compile(r"www.yellowpages.com"), self.requestUrl):
                        self.httpHeaders['Host'] = "www.yellowpages.com"
                else: # This has returned a 200 OK response. So much just to get in! :-(
                    self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
                    return(self.currentPageContent)
            except:
                print "Login request to '%s' failed with error '%s'\n\n"%(self.requestUrl, sys.exc_info()[1].__str__())
                return(None)
            self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
            print "Redirecting to '%s'... \n\n"%self.requestUrl

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
            elif re.search(re.compile(r"Max\-Age=([^;]+)"), cookie) or re.search(re.compile(r"=\"?delete"), cookie) or re.search(re.compile(r"[pP]ath=[^;]+"), cookie) or re.search(re.compile(r"Expires"), cookie) or re.search(re.compile(r"Secure"), cookie) or re.search(re.compile(r"HttpOnly"), cookie) or re.search(re.compile(r"Priority=HIGH", re.IGNORECASE), cookie) or re.search(re.compile(r"[dD]omain"), cookie):
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
    yp = YellowPages()
    pagecontent = yp.doLogin()
    if not pagecontent:
        print "Could not login into yellowpages.\n\n"
    else:
        if yp.assertLogin(yp.siteUsername):
            print "Successfully logged in as %s\n\n"%yp.siteUsername
        else:
            print "Could not login into yellowpages.\n\n"
    
    
