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



class TimesJobs(Crawler):
    """
    This class handles crawling and extraction of data from linkedin.com.
    It is derived from class Crawler.
    """
    def __init__(self):
        self.__class__.DEBUG = True
        super(TimesJobs, self).__init__("../../conf/snoop.cnf", "http://hire.timesjobs.com/index.html", "http://hire.timesjobs.com/index.html")
        self.availableCreds = self.loadCredentials("timesjobs")
        self.httpHeaders['Referer'] = self.requestUrl
        # Look for window.location pattern
        jsLocationPattern = re.compile(r"window\.location\s*=\s*\"([^\"]+)\"", re.MULTILINE|re.DOTALL)
        jsLocMatch = re.search(jsLocationPattern, self.currentPageContent)
        if not jsLocMatch:
            print "Probably we are in a wrong page - can't find the location to go to using javascript.\n"
            return None
        jsLocGroups = jsLocMatch.groups()
        if jsLocGroups.__len__() < 1:
            print "Could not find the location to go to using javascript.\n"
            return None
        self.requestUrl = jsLocGroups[0]
        if not self.__class__._isAbsoluteUrl(self.requestUrl):
            self.requestUrl = self.baseUrl + self.requestUrl
        self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        print "Requesting page pointed to by '%s' using javascript.\n"%self.requestUrl
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.sessionCookies = self.__class__._getCookieFromResponse(self.pageResponse)
            self.httpHeaders['Cookie'] = self.sessionCookies.__str__()
            self._processCookie()
        except:
            print "Error in getting redirection URL to login page - %s\n"%sys.exc_info()[1].__str__()
            return None
        responseHeaders = self.pageResponse.info()
        if not responseHeaders.has_key('Location'):
            print "Could not find the redirection to go to the login page.\n"
            return None
        self.httpHeaders['Referer'] = self.requestUrl
        self.requestUrl = responseHeaders['Location']
        if not self.__class__._isAbsoluteUrl(self.requestUrl):
            self.requestUrl = self.baseUrl + self.requestUrl
        url, cookie = self.requestUrl.split(";")
        self.httpHeaders['Cookie'] = cookie
        self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        print "Requesting page pointed to by '%s' using javascript.\n"%self.requestUrl
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.sessionCookies = self.__class__._getCookieFromResponse(self.pageResponse)
            if self.sessionCookies is not None:
                self.httpHeaders['Cookie'] = self.httpHeaders['Cookie'].__str__() + "; " + self.sessionCookies.__str__()
                self._processCookie()
            self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
        except:
            print "Error in getting login page - %s\n"%sys.exc_info()[1].__str__()
            return None
        # Set page path
        self.pagePath = self.requestUrl
        pagePathParts = self.pagePath.split(r"/")
        pagePathParts.pop()
        self.pagePath = "/".join(pagePathParts)
        

    def doLogin(self, username="", password=""):
        html = self.currentPageContent
        soup = BeautifulSoup(html)
        loginForm = soup.find("form") # There is only one form on the page.
        loginAction = loginForm['action']
        loginMethod = loginForm['method']
        if not self.__class__._isAbsoluteUrl(loginAction):
            loginAction = self.pagePath + "/" + loginAction
        self.requestUrl = loginAction
        usernameFieldname = loginForm.find("input", {'type' : 'text'})['name']
        passwordFieldname = loginForm.find("input", {'type' : 'password'})['name']
        allHiddenFields = loginForm.findAll("input", {'type' : 'hidden'})
        
        self.postData = {}
        credsLen = self.availableCreds.__len__()
        randomIndex = random.randint(0, credsLen - 1)
        tjUsernames = self.availableCreds.keys()
        self.siteUsername = tjUsernames[randomIndex]
        self.sitePassword = self.availableCreds[self.siteUsername]
        self.postData = { usernameFieldname : self.siteUsername, passwordFieldname : self.sitePassword }
        for hiddenfld in allHiddenFields:
            if hiddenfld.has_key('name') and hiddenfld.has_key('value'):
                self.postData[hiddenfld['name']] = hiddenfld['value']
        self.postData['button'] = 'Secure Login'
        encodedData = urllib.urlencode(self.postData)
        if self.__class__.DEBUG:
            print "Sending login data...\n%s\n"%encodedData
        httpHeaders = {}
        for hdr in self.httpHeaders.keys():
            httpHeaders[hdr] = self.httpHeaders[hdr]
        httpHeaders['Content-Type'] = "application/x-www-form-urlencoded"
        httpHeaders['Content-Length'] = encodedData.__len__()
        httpHeaders['Cache-Control'] = "max-age=0"
        httpHeaders['Host'] = "hire.timesjobs.com"
        httpHeaders['Origin'] = "http://hire.timesjobs.com"
        self.pageRequest = urllib2.Request(self.requestUrl, encodedData, httpHeaders)
        while True:
            print "Requesting for '%s'...\n\nHeaders: %s\n\n===================================\n\n"%(self.requestUrl, httpHeaders.__str__())
            try:
                self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
                self.sessionCookies = self.__class__._getCookieFromResponse(self.pageResponse)
                if self.sessionCookies is not None:
                    self.httpHeaders["Cookie"] = self.httpHeaders["Cookie"].__str__() + "; " + self.sessionCookies.__str__()
                    self._processCookie()
                self.httpHeaders['Referer'] = self.requestUrl
            except:
                print "Failed to send request to '%s'. Error: %s\n"%(self.requestUrl, sys.exc_info()[1].__str__())
                return(None)
            responseHeaders = self.pageResponse.info()
            if responseHeaders.has_key('Location'):
                self.requestUrl = responseHeaders['Location']
                self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
                httpHeaders = self.httpHeaders
            else: # Returned with code 200
                self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
                self.__isLoggedIn = True
                return (self.currentPageContent)


    def conductSearch(self, searchEntity):
        soup = BeautifulSoup(self.currentPageContent)
        


    def buildGraph(self):
        pass


    def parseSearchHtml(self):
        """
        Parses the HTML content in the object's currentPageContent attribute and sets the
        object's 'searchResults' attribute with the resultant dict. Returns the number of
        matches found (i.e., the number of keys in the dict).
        """
        pass


    def _processCookie(self):
        """
        Method to remove extra semicolons and repeatitive keys in cookies. To be used internally.
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
            elif re.search(re.compile(r"Max\-Age=(\-|0)"), cookie) or re.search(re.compile(r"=\"?delete"), cookie) or re.search(re.compile(r"Path="), cookie) or re.search(re.compile(r"Expires"), cookie) or re.search(re.compile(r"Secure"), cookie) or re.search(re.compile(r"HttpOnly"), cookie):
                continue
            else:
                cookieparts = cookie.split("=")
                if cookieparts.__len__() == 2:
                    cookiesDict[cookieparts[0]] = cookieparts[1]
                if cookieparts.__len__() > 2:
                    for j in range(2, cookieparts.__len__()):
                        cookiesDict[cookieparts[0]] += "=" + cookieparts[j]
        self.sessionCookies = ""
        for cookie in cookiesDict.keys():
            self.sessionCookies += cookie + "=" + cookiesDict[cookie] + ";"
        self.httpHeaders['Cookie'] = self.sessionCookies
        return(self.sessionCookies)


    def logout(self):
        print "Trying to log out...\n"
        if not self.__isLoggedIn:
            print "User doesn't appear to be logged in. No action needed.\n"
            return None
        soup = BeautifulSoup(self.currentPageContent)
        logoutSpans = soup.findAll("span", {'class' : 'resume_title'})
        logoutUrl = None
        for logoutSpan in logoutSpans:
            logoutAnchor = logoutSpan.findNext("a")
            if logoutAnchor.renderContents() == "Logout":
                logoutUrl = logoutAnchor['href']
                break
        if not logoutUrl:
            print "Could not find the logout URL. User is probably not logged in.\n"
            return None
        if not self.__class__._isAbsoluteUrl(logoutUrl):
            logoutUrl = self.baseUrl + logoutUrl
        self.requestUrl = logoutUrl
        self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
        except:
            print "Could not logout from the session. Please reset the session manually by visiting the website.\n"
            return None
        responseHeaders = self.pageResponse.info()
        if not responseHeaders.has_key("Location"):
            print "Could not do the redirection during logout operation. That means you have to visit the website and reset the session manually.\n"
            return None
        self.requestUrl = responseHeaders['Location']
        if not self.__class__._isAbsoluteUrl(self.requestUrl):
            self.requestUrl = self.baseUrl + self.requestUrl
        self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.sessionCookies = self.httpHeaders['Cookie'] = ""
            self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
            self.__isLoggedIn = False
            print "Logged out of the session successfully.\n"
            return self.currentPageContent
        except:
            print "Could not fetch the redirect URL during logout. Please reset the session manually by visiting the website.\nError: %s\n"%sys.exc_info()[1].__str__()
            return None



if __name__ == "__main__":
    searchEntity = sys.argv[1]
    tj = TimesJobs()
    pageContent = tj.doLogin()
    if not tj.assertLogin(tj.siteUsername):
        print "Could not log in. Username: %s, Password: %s. Damn it!\n"%(tj.siteUsername, tj.sitePassword)
        sys.exit()
    else:
        print "Successfully logged in as %s\n"%tj.siteUsername
    searchHtml = tj.conductSearch(searchEntity)
    if not tj.isLoggedIn(re.compile("Logout", re.MULTILINE|re.DOTALL|re.IGNORECASE)):
        print "Session corrupted... Please rerun app with another user creds.\n"
    searchResult = tj.parseSearchHtml()
    tj.logout()
