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



class LinkedIn(Crawler):
    """
    This class handles crawling and extraction of data from linkedin.com.
    It is derived from class Crawler.
    """
    def __init__(self):
        self.__class__.DEBUG = True
        super(LinkedIn, self).__init__("../../conf/snoop.cnf", "https://www.linkedin.com/", "https://www.linkedin.com/")
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
        if not self.__class__._isAbsoluteUrl(loginAction):
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
        
        # Now, the most important 3 steps, otherwise linkedin won't let you in.
        self.httpHeaders['Host'] = 'www.linkedin.com'
        self.httpHeaders.pop('Content-Type', None)
        self.httpHeaders.pop('Content-Length', None)
        # Without the above steps, linkedin gives HTTP Error 999 - Request Denied.
        
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
        soup = BeautifulSoup(self.currentPageContent)
        searchForm = soup.find("form", {'id' : 'global-search'})
        searchAction = searchForm['action']
        if not self.__class__._isAbsoluteUrl(searchAction):
            searchAction = self.baseUrl + searchAction
        queryField = searchForm.find("input", {'type' : 'text'})
        queryFieldName = queryField['name']
        otherHiddenFields = searchForm.findAll("input", {'type' : 'hidden'})
        queryDict = {queryFieldName : searchEntity}
        for fld in otherHiddenFields:
            fldName = ''
            if fld.has_key('name'):
                fldName = fld['name']
            elif fld.has_key('id'):
                fldName = fld['id']
            else:
                continue
            fldValue = ''
            if fld.has_key('value'):
                fldValue = fld['value']
            queryDict[fldName] = fldValue
        queryString = urllib.urlencode(queryDict)
        self.requestUrl = searchAction + "?" + queryString
        self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.httpHeaders['Referer'] = self.requestUrl
        except:
            print "Search request failed with error %s\n"%sys.exc_info()[1].__str__()
            return (None)
        self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
        # Parse the resulting HTML in another method... For now, just returning it.
        return (self.currentPageContent)


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
    if not linkedin.assertLogin("Sign Out"):
        print "Could not log in. Username: %s, Password: %s\n"%(linkedin.siteUsername, linkedin.sitePassword)
        print "Dumping file in '../html/linkedin_loginfail.html'\n"
        fl = open("../html/linkedin_loginfail.html", "w")
        fl.write(pageContent)
        fl.close()
        sys.exit()
    else:
        print "Successfully logged in as %s\n"%linkedin.siteUsername
    searchHtml = linkedin.conductSearch(searchEntity)
    if not linkedin.isLoggedIn(re.compile("Sign Out", re.MULTILINE|re.DOTALL|re.IGNORECASE)):
        print "Session corrupted... Please rerun app with another user creds.\n"
    if searchHtml:
        ff = open("linkedinlogin3.html", "w")
        ff.write(searchHtml)
        ff.close()
    searchResult = linkedin.parseSearchHtml()
