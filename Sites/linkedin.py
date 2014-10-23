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



class LinkedIn(Crawler):
    """
    This class handles crawling and extraction of data from linkedin.com.
    It is derived from class Crawler.
    """
    def __init__(self):
        self.__class__.DEBUG = True
        super(LinkedIn, self).__init__("../conf/snoop.cnf", "https://www.linkedin.com/", "https://www.linkedin.com/")
        self.availableCreds = self.loadCredentials("linkedin")


    def doLogin(self, username="", password=""):
        html = self.currentPageContent
        soup = BeautifulSoup(html)
        loginForm = soup.find("form", {'name' : 'login'})
        emailField = loginForm.find("input", {'type' : 'text'})
        passwdField = loginForm.find("input", {'type' : 'password'})
        loginAction = loginForm['action']
        otherFields = loginForm.findAll("input", {'type' : 'hidden'})
        self.postData = {}
        credsLen = self.availableCreds.__len__()
        randomIndex = random.randint(0, credsLen - 1)
        lnkinUsernames = self.availableCreds.keys()
        self.siteUsername = lnkinUsernames[randomIndex]
        self.sitePassword = self.availableCreds[self.siteUsername]
        self.postData[emailField['name']] = self.siteUsername
        self.postData[passwdField['name']] = self.sitePassword
        for fld in otherFields:
            if fld.has_key('name'):
                self.postData[fld['name']] = ""
                if fld.has_key('value'):
                    self.postData[fld['name']] = fld['value']
            elif fld.has_key('id'):
                self.postData[fld['name']] = ""
                if fld.has_key('value'):
                    self.postData[fld['name']] = fld['value']
            else:
                continue
        self.postData['isJsEnabled'] = 'true'
        encodedData = urllib.urlencode(self.postData)
        encodedData += "&signin=Sign+In"
        if not re.search(self.__class__.absUrlPattern, loginAction):
            loginAction = self.baseUrl + loginAction
        self.requestUrl = loginAction
        self._processCookie()
        self.httpHeaders['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        self.httpHeaders['Cache-Control'] = 'max-age=0'
        self.httpHeaders['Content-Type'] = 'application/x-www-form-urlencoded'
        self.httpHeaders['Content-Length'] = encodedData.__len__()
        self.pageRequest = urllib2.Request(self.requestUrl, encodedData, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.sessionCookies = self.__class__._getCookieFromResponse(self.pageResponse)
            self.httpHeaders["Cookie"] += self.sessionCookies
            responseHeaders = self.pageResponse.info()
            if responseHeaders.has_key('Location'):
                self.requestUrl = responseHeaders['Location']
            else:
                print "Could not find redirection URL during logging in. Giving up...\n"
                return None
        except:
            print "Failed while making the POST request to login. Giving up...\n"
            return None
        self._processCookie()
        self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        if self.__class__.DEBUG:
            print "\n===========================================\n"
            print "Request URL: " + self.requestUrl
            print "Request Headers: " + self.httpHeaders.__str__()
            print "Encoded Data: " + encodedData
            print "\n===========================================\n"
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.httpHeaders['Referer'] = self.requestUrl
        except:
            print "Failed while redirecting to user's homepage during login. Giving up... %s\n"%sys.exc_info()[1].__str__()
            return None
        self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
        return (self.currentPageContent)


    def conductSearch(self, searchEntity):
        pass


    def buildGraph(self):
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
            elif re.search(re.compile(r"Max\-Age=\-"), cookie) or re.search(re.compile(r"=\"?delete"), cookie) or re.search(re.compile(r"Path="), cookie) or re.search(re.compile(r"Expires"), cookie) or re.search(re.compile(r"Secure"), cookie) or re.search(re.compile(r"HttpOnly"), cookie):
                continue
            else:
                cookieparts = cookie.split("=")
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
    linkedin = LinkedIn()
    pageContent = linkedin.doLogin()
    ff = open("linkedinlogin.html", "w")
    ff.write(pageContent)
    ff.close()
    linkedin.conductSearch(searchEntity)
