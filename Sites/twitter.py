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



class Twitter(Crawler):
    """
    This class handles crawling and extraction of data from twitter.com.
    It is derived from class Crawler.
    """
    def __init__(self):
        self.__class__.DEBUG = True
        super(Twitter, self).__init__("../conf/snoop.cnf", "https://twitter.com/", "https://twitter.com/")
        self.availableCreds = self.loadCredentials("twitter")


    def doLogin(self, username="", password=""):
        html = self.currentPageContent
        soup = BeautifulSoup(html)
        signindiv = soup.find("div", {'class' : 'signin-dialog-body'})
        signinform = signindiv.find("form")
        emailField = signinform.find("input", {'type' : 'text'})
        action = signinform['action']
        passwordField = signinform.find("input", {'type' : 'password'})
        hiddenFields = signinform.findAll("input", {'type' : 'hidden'})
        self.postData = {}
        credsLen = self.availableCreds.__len__()
        randomIndex = random.randint(0, credsLen - 1)
        twtUsernames = self.availableCreds.keys()
        self.siteUsername = twtUsernames[randomIndex]
        self.sitePassword = self.availableCreds[self.siteUsername]
        emailFieldName = emailField['name']
        self.postData[emailFieldName] = self.siteUsername
        passwordFieldName = passwordField['name']
        self.postData[passwordFieldName] = self.sitePassword
        for fld in hiddenFields:
            fldName = fld['name']
            if fld.has_key('value'):
                self.postData[fldName] = fld['value']
            else:
                self.postData[fldName] = ""
        encodedData = urllib.urlencode(self.postData)
        self.requestUrl = action
        self.pageRequest = urllib2.Request(self.requestUrl, encodedData, self.httpHeaders)
        print encodedData
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.sessionCookies = self.__class__._getCookieFromResponse(self.pageResponse)
            self.httpHeaders["Cookie"] = self.sessionCookies
            responseHeaders = self.pageResponse.info()
            if responseHeaders.has_key('location'):
                self.requestUrl = responseHeaders['location']
                #print self.requestUrl
            else:
                print "Could not find redirection URL during logging in. Giving up...\n"
                return None
        except:
            print "Failed while making the POST request to login. Giving up...\n"
            return None
        self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.sessionCookies = self.__class__._getCookieFromResponse(self.pageResponse)
            self.httpHeaders["Cookie"] = self.sessionCookies
        except:
            print "Failed to login into twitter"
            return(None)
        self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
        return (self.currentPageContent)


    def conductSearchUnsigned(self, searchEntity):
        soup = BeautifulSoup(self.currentPageContent)
        searchForm = soup.find("form", {'id' : 'global-nav-search'})
        searchBox = searchForm.find("input", {'type' : 'text'})
        searchBoxName = searchBox['name']
        action = searchForm['action']
        self._processCookie()
        queryDict = {searchBoxName : searchEntity}
        queryStr = urllib.urlencode(queryDict)
        self.requestUrl = self.baseUrl + action + "?" + queryStr
        self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
        except:
            print "Could not conduct search on twitter. Error: %s\n"%sys.exc_info()[1].__str__()
            return(None)
        ff = open("dumptwitter1.html", "w")
        ff.write(self.currentPageContent)
        ff.close()
        return(self.currentPageContent)


    def conductSearch(self, searchEntity):
        self.requestUrl = "https://twitter.com/i/search/typeahead.json"
        queryDict = { 'count' : '50', 'experiments' : '', 'filters' : 'true', 'q' : searchEntity, 'result_type' : 'topics,users', 'src' : 'SEARCH_BOX' }
        queryStr = urllib.urlencode(queryDict)
        self.requestUrl = self.requestUrl + "?" + queryStr
        self._processCookie()
        soup = BeautifulSoup(self.currentPageContent)
        twitteridPattern = re.compile(r"userId&quot;:&quot;(\d+)&quot;", re.MULTILINE|re.DOTALL)
        twitteridMatch = twitteridPattern.search(self.currentPageContent)
        twitterid = ""
        if twitteridMatch:
            twitterid = twitteridMatch.groups()[0]
        signoutForm = soup.find("form", {'id' : 'signout-form'})
        authToken = ""
        if signoutForm:
            authTokenElement = signoutForm.find("input", {'name' : 'authenticity_token'})
            if authTokenElement:
                authToken = authTokenElement['value']
        externalReferer = ""
        self.httpHeaders['Cookie'] += "twid=\"u=%s\";auth_token=%s;remember_checked_on=0;_gat=1;goth=1; eu_cn=1;external_referer=\"%s\";"%(twitterid, authToken, externalReferer)
        # This will need a few 'special' headers
        headers = {}
        for hdr in self.httpHeaders.keys():
            headers[hdr] = self.httpHeaders[hdr]
        headers[':host'] = 'twitter.com'
        headers[':method'] = 'GET'
        headers[':path'] = self.requestUrl
        headers[':path'] = re.sub("https://twitter.com", "", headers[':path'])
        headers[':scheme'] = 'https'
        headers[':version'] = 'HTTP/1.1'
        headers['accept'] = 'application/json, text/javascript, */*; q=0.01'
        headers.pop('Accept', None)
        headers['accept-encoding'] = 'gzip,deflate'
        headers.pop('Accept-Encoding', None)
        headers['accept-language'] = 'en-US,en;q=0.8'
        headers.pop('Accept-Language', None)
        headers['cookie'] = headers['Cookie']
        headers.pop('Cookie', None)
        headers['referer'] = headers['Referer']
        headers.pop('Referer', None)
        headers['user-agent'] = headers['User-Agent']
        headers.pop('User-Agent', None)
        headers['x-phx'] = 'true'
        headers['x-requested-with'] = 'XMLHttpRequest'
        self.pageRequest = urllib2.Request(self.requestUrl, None, headers)
        if self.__class__.DEBUG:
            print "\n===========================================\n"
            print self.requestUrl
            print headers
            print "\n===========================================\n"
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
        except:
            print "Could not conduct search on twitter. Error: %s\n"%sys.exc_info()[1].__str__()
            return(None)
        # self.currentPageContent should contain json string
        print self.currentPageContent


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
                elif re.search(re.compile(r"Path"), cookie) or re.search(re.compile(r"Secure"), cookie) or re.search(re.compile(r"HTTPOnly"), cookie) or re.search(re.compile(r"Expires"), cookie):
                    continue
                else:
                    cookieparts = cookie.split("=")
                    if cookieparts.__len__() > 1:
                        cookiesDict[cookieparts[0]] = cookieparts[1]
                    else:
                        cookiesDict[cookieparts[0]] = ""
            self.sessionCookies = ""
            for cookie in cookiesDict.keys():
                self.sessionCookies += cookie + "=" + cookiesDict[cookie] + ";"
            self.httpHeaders['Cookie'] = self.sessionCookies
            return(self.sessionCookies)
    


if __name__ == "__main__":
    searchEntity = sys.argv[1]
    twtr = Twitter()
    content = twtr.doLogin()
    fh = open("logintwitter.html", "w")
    fh.write(content)
    fh.close()
    if not twtr.assertLogin("Sign out"):
        print "Login failed."
        sys.exit()
    else:
        print "Successfully logged in as %s\n"%twtr.siteUsername
    twtr.conductSearch(searchEntity)
