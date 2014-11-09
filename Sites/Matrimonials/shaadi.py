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



class Shaadi(Crawler):
    """
    This class handles crawling and extraction of data from Shaadi.com, a popular site
    for finding and managing matrimonial aliances. It is derived from class Crawler.
    """
    def __init__(self):
        self.__class__.DEBUG = True
        super(Shaadi, self).__init__("../../conf/snoop.cnf", "http://www.shaadi.com/", "http://www.shaadi.com/")
        self.availableCreds = self.loadCredentials("shaadi")
        # The 'Crawler' class' '_getCookieFromResponse' method doesn't handle multiple 'Set-Cookie' headers. So we do it here on pageResponse.
        responseHeaders = self.pageResponse.info()
        allCookies = responseHeaders['Set-Cookie']
        cookiesList = allCookies.split(",")
        self.httpHeaders['Cookie'] = ""
        for cookie in cookiesList:
            self.httpHeaders['Cookie'] += cookie + "; "
        self._processCookie()


    def doLogin(self, username="", password=""):
        soup = BeautifulSoup(self.currentPageContent)
        loginForm = soup.find("form", {'name' : 'loginpage'})
        loginAction = loginForm['action']
        if not self.__class__._isAbsoluteUrl(loginAction):
            loginAction = self.baseUrl + loginAction
        self.httpHeaders['Referer'] = self.requestUrl
        self.requestUrl = loginAction

        credsLen = self.availableCreds.__len__()
        randomIndex = random.randint(0, credsLen - 1)

        shdiUsernames = self.availableCreds.keys()
        self.siteUsername = shdiUsernames[randomIndex]
        self.sitePassword = self.availableCreds[self.siteUsername]

        usernameFieldname = loginForm.find("input", {'type' : 'text'})['name']
        passwordFieldname = loginForm.find("input", {'type' : 'password'})['name']
        otherFields = loginForm.findAll("input", {'type' : 'hidden'})
        self.postData = {usernameFieldname : self.siteUsername, passwordFieldname : self.sitePassword, }
        for field in otherFields:
            fieldname = ""
            fieldvalue = ""
            if field.has_key('name'):
                fieldname = field['name']
            elif field.has_key('id'):
                fieldname = field['id']
            else:
                continue
            if field.has_key('value'):
                fieldvalue = field['value']
            self.postData[fieldname] = fieldvalue
        checkboxField = loginForm.find("input", {'type' : 'checkbox'})
        self.postData[checkboxField['name']] = checkboxField['value']
        submitButtonField = loginForm.find("input", {'type' : 'submit'})
        self.postData[submitButtonField['class']] = submitButtonField['value']
        encodedData = urllib.urlencode(self.postData)
        self._processCookie()
        requestHeaders = {}
        for hdr in self.httpHeaders.keys():
            requestHeaders[hdr] = self.httpHeaders[hdr]
        requestHeaders['Content-Type'] = "application/x-www-form-urlencoded"
        requestHeaders['Content-Length'] = encodedData.__len__()
        if self.__class__.DEBUG:
            print "Sending login request to '%s'\n\n"%self.requestUrl
            print "POST Data: %s\n\n"%encodedData
            print "Headers: %s\n\n"%requestHeaders
        self.pageRequest = urllib2.Request(self.requestUrl, encodedData, requestHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
        except:
            print "Failed to make the login request to '%s' - Error: '%s'\n\n"%(self.requestUrl, sys.exc_info()[1].__str__())
            return(None)
        responseHeaders = self.pageResponse.info()
        self.httpHeaders['Referer'] = self.requestUrl
        if responseHeaders.has_key('Set-Cookie'):
            allCookies = responseHeaders['Set-Cookie'].split(",")
            for cookie in allCookies:
                self.httpHeaders['Cookie'] += cookie + "; "
        self._processCookie()

        if responseHeaders.has_key('Location'):
            self.requestUrl = responseHeaders['Location']
        else:
            print "Could not get the redirect URL on login.\n\n"
            self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
            return(self.currentPageContent)
        if not self.__class__._isAbsoluteUrl(self.requestUrl):
            self.requestUrl = self.baseUrl + self.requestUrl
        self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
        except:
            print "Failed to make the redirect request to '%s' during login. Error: '%s'\n\n"%(self.requestUrl, sys.exc_info()[1].__str__())
            return(None)
        responseHeaders = self.pageResponse.info()
        self.httpHeaders['Referer'] = self.requestUrl
        if responseHeaders.has_key('Set-Cookie'):
            allCookies = responseHeaders['Set-Cookie'].split(",")
            for cookie in allCookies:
                self.httpHeaders['Cookie'] += cookie + "; "
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
    shd = Shaadi()
    pageContent = shd.doLogin()
    if pageContent:
        ff = open("../html/shaadilogin.html", "w")
        ff.write(pageContent)
        ff.close()
    if not shd.assertLogin("<div title=\"Logged in as: "):
        print "Could not log in"
        sys.exit()
    else:
        print "Successfully logged in as %s\n"%shd.siteUsername
    shd.conductSearch(searchEntity)
    
