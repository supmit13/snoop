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



class Wayn(Crawler):
    """
    This class handles crawling and extraction of data from wayn.
    It is derived from class Crawler.
    """
    def __init__(self):
        self.__class__.DEBUG = True
        super(Wayn, self).__init__("../../conf/snoop.cnf", "https://www.wayn.com/", "https://www.wayn.com/")
        self.availableCreds = self.loadCredentials("wayn")


    def doLogin(self, username="", password=""):
        soup = BeautifulSoup(self.currentPageContent)
        loginForm = soup.find("form", {'name' : 'loginform'})
        if not loginForm:
            print "Could not find the login form.\n"
            return (None)
        loginAction = loginForm['action']
        if not self.__class__._isAbsoluteUrl(loginAction):
            loginAction = self.baseUrl + loginAction
        self.httpHeaders['Referer'] = self.requestUrl
        self.requestUrl = loginAction
        usernameField = loginForm.find("input", {'type' : 'text'})
        passwordField = loginForm.find("input", {'type' : 'password'})
        if not usernameField or not passwordField:
            print "Could not find the username or password field.\n"
            return (None)
        self.postData = {}
        usernameFieldname, passwordFieldname = "", ""
        if usernameField.has_key('name'):
            usernameFieldname = usernameField['name']
        elif usernameField.has_key('id'):
            usernameFieldname = usernameField['id']
        else:
            print "Can't find the name or Id of the username field. Please review the contents of the page to check if we are on the right page.\n"
            return(None)
        if passwordField.has_key('name'):
            passwordFieldname = passwordField['name']
        elif passwordField.has_key('id'):
            passwordFieldname = passwordField['id']
        else:
            print "Can't find the name or id of the password field. Please review the contents  of the page to check if we are on the right page.\n"
            return (None)

        # Now select a username and password from self.availableCreds randomly
        credsLen = self.availableCreds.__len__()
        randomIndex = random.randint(0, credsLen - 1)
        waynUsernames = self.availableCreds.keys()
        self.siteUsername = waynUsernames[randomIndex]
        self.sitePassword = self.availableCreds[self.siteUsername]

        passwordValue = md5.md5(self.sitePassword)
        passwordDigest = passwordValue.hexdigest()
        self.postData[usernameFieldname] = self.siteUsername
        self.postData[passwordFieldname] = passwordDigest

        otherFields = loginForm.findAll("input", {'type' : 'hidden'})
        for fld in otherFields:
            fldname, fldvalue = "", ""
            if fld.has_key('name'):
                fldname = fld['name']
            elif fld.has_key('id'):
                fldname = fld['id']
            else: #field has neither name nor id, so we just skip it.
                continue
            if  fld.has_key('value'):
                fldvalue = fld['value']
            if fldname == 'password':
                self.postData['password'] = passwordDigest
                self.postData['passwd'] = ''
                continue
            self.postData[fldname] = fldvalue
        encodedData = urllib.urlencode(self.postData)
        self.pageRequest =  urllib2.Request(self.requestUrl, encodedData, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.sessionCookies = self.__class__._getCookieFromResponse(self.pageResponse)
            self.httpHeaders["Cookie"] += self.sessionCookies.__str__()

            self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
            self.httpHeaders['Referer'] = self.requestUrl
        except:
            print "Could not send the login request - Error: %s\n"%sys.exc_info()[1].__str__()
            return(None)
        # Now make the actual content fetching request to wayn.com
        self.requestUrl = "https://www.wayn.com/"
        self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.sessionCookies = self.__class__._getCookieFromResponse(self.pageResponse)
            self.httpHeaders["Cookie"] += self.sessionCookies.__str__()
            self._processCookie()
            self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
            self.httpHeaders['Referer'] = self.requestUrl
            return(self.currentPageContent)
        except:
            print "Could not make the second request for login - Error: %s\n"%sys.exc_info()[1].__str__()
            return(None)


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
            elif re.search(re.compile(r"Max\-Age=(\-|0)"), cookie) or re.search(re.compile(r"=\"?delete"), cookie) or re.search(re.compile(r"Path="), cookie) or re.search(re.compile(r"Expires"), cookie) or re.search(re.compile(r"Secure"), cookie) or re.search(re.compile(r"HttpOnly"), cookie) or re.search(re.compile(r"Priority=HIGH", re.IGNORECASE), cookie):
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
    wayn = Wayn()
    pageContent = wayn.doLogin()
    if pageContent:
        ff = open("../html/waynlogin.html", "w")
        ff.write(pageContent)
        ff.close()
    if not wayn.assertLogin("Log out"):
        print "Could not log in"
        sys.exit()
    else:
        print "Successfully logged in as %s\n"%wayn.siteUsername
    wayn.conductSearch(searchEntity)
    
