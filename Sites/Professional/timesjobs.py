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
        responseHeaders = self.pageResponse.info()
        if not responseHeaders.has_key('Location'):
            print "Could not find the redirection URL to go to the login page.\n"
            return(None)
        self.httpHeaders['Referer'] = self.requestUrl
        self.requestUrl = responseHeaders['Location']
        self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.sessionCookies = self.__class__._getCookieFromResponse(self.pageResponse)
            self.httpHeaders["Cookie"] = self.httpHeaders["Cookie"].__str__() + self.sessionCookies.__str__()
            self._processCookie()
        except:
            print "Could not fetch the login page.\n"
            return(None)
        self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
        return (self.currentPageContent)


    def doLogin(self, username="", password=""):
        html = self.currentPageContent
        soup = BeautifulSoup(html)


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




if __name__ == "__main__":
    searchEntity = sys.argv[1]
    tj = TimesJobs()
    pageContent = tj.doLogin()
    if not tj.assertLogin("Logout"):
        print "Could not log in. Username: %s, Password: %s\n"%(tj.siteUsername, tj.sitePassword)
        sys.exit()
    else:
        print "Successfully logged in as %s\n"%tj.siteUsername
    searchHtml = tj.conductSearch(searchEntity)
    if not tj.isLoggedIn(re.compile("Logout", re.MULTILINE|re.DOTALL|re.IGNORECASE)):
        print "Session corrupted... Please rerun app with another user creds.\n"
    searchResult = tj.parseSearchHtml()
