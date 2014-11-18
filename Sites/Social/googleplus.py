import os, sys, re, time, gzip
import urllib, urllib2, httplib
from BeautifulSoup import BeautifulSoup
from urlparse import urlparse, urlsplit
import StringIO
import mimetypes, mimetools
from ConfigParser import ConfigParser
sys.path.append("../../")
from Crawler import Crawler
import random
import md5, base64



class GooglePlus(Crawler):
    """
    This class handles crawling and extraction of data from google+.
    It is derived from class Crawler.
    """
    def __init__(self):
        self.__class__.DEBUG = True
        super(GooglePlus, self).__init__("../../conf/snoop.cnf", "https://plus.google.com/", "https://plus.google.com/")
        self.availableCreds = self.loadCredentials("googleplus")
        gsoup = BeautifulSoup(self.currentPageContent)
        redirectAnchor = gsoup.find("a")
        redirectUrl = redirectAnchor['href']
        self.requestUrl = redirectUrl
        self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.sessionCookies = self.__class__._getCookieFromResponse(self.pageResponse)
            self.httpHeaders["Cookie"] = self.sessionCookies
        except:
            print __file__.__str__() + ": Couldn't fetch page due to limited connectivity (2). Please check your internet connection and try again. " + sys.exc_info()[1].__str__()
        self.httpHeaders["Referer"] = self.requestUrl
        # Initialize the account related variables...
        self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())


    def doLogin(self, username="", password=""):
        soup = BeautifulSoup(self.currentPageContent)
        loginForm = soup.find("form", {'id' : 'gaia_loginform'})
        if not loginForm:
            print "Couldn't find the login form... Quiting.\n"
            return(None)
        loginAction = loginForm['action']
        loginMethod = loginForm['method']
        if not self.__class__._isAbsoluteUrl(loginAction):
            loginAction = self.baseUrl + loginAction
        usernameField = loginForm.find("input", {'type' : 'email'})
        if not usernameField:
            usernameField = loginForm.find("input", {'type' : 'text'})
        passwordField = loginForm.find("input", {'type' : 'password'})
        otherHiddenFields = loginForm.findAll("input", {'type' : 'hidden'})

        # Now select a username and password from self.availableCreds randomly
        credsLen = self.availableCreds.__len__()
        randomIndex = random.randint(0, credsLen - 1)
        gplusUsernames = self.availableCreds.keys()
        self.siteUsername = gplusUsernames[randomIndex]
        self.sitePassword = self.availableCreds[self.siteUsername]
        
        self.postData = {}
        if usernameField.has_key('name'):
            self.postData[usernameField['name']] = self.siteUsername
        elif usernameField.has_key('id'):
            self.postData[usernameField['id']] = self.siteUsername
        else:
            print "This doesn't look like a login form.\n"
            return (None)
        if passwordField.has_key('name'):
            self.postData[passwordField['name']] = self.sitePassword
        elif passwordField.has_key('id'):
            self.postData[passwordField['id']] = self.sitePassword
        else:
            print "This doesn't look like a login form.\n"
            return (None)
        for hfld in otherHiddenFields:
            fldname = ""
            if hfld.has_key('name'):
                fldname = hfld['name']
            elif hfld.has_key('id'):
                fldname = hfld['id']
            else: # Let this pass...
                continue
            fldvalue = ""
            if hfld.has_key('value'):
                fldvalue = hfld['value']
            fldname = fldname.encode('utf-8')
            fldvalue = fldvalue.encode('utf-8')
            if fldname == 'checkConnection':
                fldvalue = "youtube:1177:0"
            if fldname == 'pstMsg':
                fldvalue = '1'
            #if fldname == 'bgresponse':
            #    continue
            self.postData[fldname] = fldvalue
        self.postData['signIn'] = "Sign in"
        self.postData['PersistentCookie'] = "yes"
        encodedData = urllib.urlencode(self.postData)
        #b = base64.b64encode(encodedData)
        #encodedData += "&bgresponse=%s"%b
        self._processCookie()
        # Set headers appropriately
        httpHeaders = {}
        for hdr in self.httpHeaders.keys():
            httpHeaders[hdr.lower()] = self.httpHeaders[hdr]
        httpHeaders['content-type'] = "application/x-www-form-urlencoded"
        httpHeaders[':host'] = "accounts.google.com"
        httpHeaders[':method'] = "POST"
        httpHeaders[':path'] = "/ServiceLoginAuth"
        httpHeaders[':scheme'] = "https"
        httpHeaders[':version'] = "HTTP/1.1"
        httpHeaders['origin'] = "https://accounts.google.com"
        httpHeaders['content-length'] = encodedData.__len__()
        httpHeaders['accept-encoding'] = 'gzip,deflate,sdch'

        self.requestUrl = loginAction
        if self.requestUrl is not None:
            self.pageRequest = urllib2.Request(self.requestUrl, encodedData, self.httpHeaders)
            try:
                self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
                self.sessionCookies = self.__class__._getCookieFromResponse(self.pageResponse)
                self.httpHeaders["Cookie"] += self.sessionCookies
                responseHeaders = self.pageResponse.info()
                if responseHeaders.has_key('location'):
                    self.requestUrl = responseHeaders['location']
                else:
                    print "Could not find redirection URL during logging in. Giving up...\n"
                    return None
            except:
                print __file__.__str__() + ": Failed to make the login request. Error: %s\n"%(sys.exc_info()[1].__str__())
                return(None)
        httpHeaders[':method'] = 'GET'
        httpHeaders.pop('content-type', None)
        httpHeaders.pop('content-length', None)
        self._processCookie()
        httpHeaders['cookie'] = self.httpHeaders["Cookie"]
        httpHeaders['accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        httpHeaders[':path'] = self.requestUrl
        httpHeaders[':path'] = re.sub(re.compile("https://accounts.google.com"), "", httpHeaders[':path'])
        httpHeaders['cache-control'] = 'max-age=0'
        if httpHeaders.has_key("connection"):
            httpHeaders.pop('connection', None)
        if httpHeaders.has_key("keep-alive"):
            httpHeaders.pop('keep-alive', None)
        if httpHeaders.has_key("origin"):
            httpHeaders.pop("origin", None)
        if httpHeaders.has_key("accept-charset"):
            httpHeaders.pop("accept-charset", None)
        httpHeaders['allow-chrome-signin'] = '1'

        self.pageRequest = urllib2.Request(self.requestUrl, None, httpHeaders)
        print httpHeaders
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.sessionCookies = self.__class__._getCookieFromResponse(self.pageResponse)
            self.httpHeaders["Cookie"] += self.sessionCookies
            self._processCookie()
            self.httpHeaders['Referer'] = self.requestUrl
        except:
            print "Could not make the redirect request to '%s' successfully. Error: %s\n"%(self.requestUrl, sys.exc_info()[1].__str__())
            return None
        continuePattern = re.compile(r"&continue=([^&]+)&", re.IGNORECASE)
        continueMatch = continuePattern.search(self.requestUrl)
        if continueMatch:
            continueGroups = continueMatch.groups()
            continueUrl = continueGroups[0]
            httpHeaders['referer'] = self.requestUrl
            self.requestUrl = continueUrl
            httpHeaders.pop(':path', None)
            self.requestUrl = self.requestUrl.replace("%3A", ":").replace("%2F", "/").replace("%3F", "?").replace("%3D", "=")
            print "Continuing with the next URL %s\n"%self.requestUrl
            httpHeaders[':host'] = 'plus.google.com'
            httpHeaders[':path'] = self.requestUrl
            httpHeaders[':path'] = re.sub(re.compile(r"https://plus.google.com"), "", httpHeaders[':path'])
        else:
            print "The URL to continue doesn't look right. %s\n"%self.requestUrl
            return(None)
        if self.__class__.DEBUG:
            print "\n===========================================\n"
            print "Request URL: " + self.requestUrl.__str__()
            print "HTTP Headers: " + httpHeaders.__str__()
            print "\n===========================================\n"
        self.pageRequest = urllib2.Request(self.requestUrl, None, httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
        except:
            print "Continue  request (to %s) did not succeed. Quitting... Error: %s\n"%(self.requestUrl, sys.exc_info()[1].__str__())
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
    gplus = GooglePlus()
    ff = open("..\\html\\googleplus.html", "w")
    ff.write(gplus.currentPageContent)
    ff.close()
    pageContent = gplus.doLogin()
    if pageContent:
        ff = open("googlepluslogin.html", "w")
        ff.write(pageContent)
        ff.close()
    if not gplus.assertLogin("Sign Out"):
        print "Could not log in"
        sys.exit()
    else:
        print "Successfully logged in as %s\n"%gplus.siteUsername
    gplus.conductSearch(searchEntity)
    
