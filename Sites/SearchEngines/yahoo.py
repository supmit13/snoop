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



class Yahoo(Crawler):
    """
    This class handles crawling and extraction of data from yahoo search.
    It is derived from class Crawler.
    """
    
    def __init__(self):
        self.__class__.DEBUG = True
        super(Yahoo, self).__init__("../../conf/snoop.cnf", "https://www.yahoo.com/", "https://www.yahoo.com/")
        self.searchEntries = []
        self.searchListingPageDepth = self.cfgParser.get("SearchEngines", "yahoolistingdepth")
        responseHeaders = self.pageResponse.info()
        if responseHeaders.has_key('Set-Cookie'):
            self.httpHeaders['Cookie'] += responseHeaders['Set-Cookie']
            self._processCookie()
        self.httpHeaders['Referer'] = self.requestUrl
        if responseHeaders.has_key('Location'):
            self.requestUrl = responseHeaders['Location']
        else:
            print "Could not get the redirection URL to the search interface page.\n\n"
            return(None)
        if not self.__class__._isAbsoluteUrl(self.requestUrl):
            self.requestUrl = "https://www.yahoo.com" + self.requestUrl
        self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
        except:
            print "Could not make the redirection request to the search page. Error: %s\n\n"%sys.exc_info()[1].__str__()
            return(None)
        responseHeaders = self.pageResponse.info()
        if responseHeaders.has_key('Set-Cookie'):
            self.httpHeaders['Cookie'] += responseHeaders['Set-Cookie']
            self._processCookie()
        self.httpHeaders['Referer'] = self.requestUrl
        self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())


    def doLogin(self, username="", password=""):
        pass # No login is required to search


    def _getSearchResults(self, searchPageContent, bstr='1'):
        soup = BeautifulSoup(searchPageContent)
        print "Extracting links and content...\n\n"
        olist = soup.find("ol", {'start' : bstr})
        if not olist:
            return([])
        ocontents = olist.renderContents()
        listentries = olist.findAll("li")
        searchEntries = []
        for entry in listentries:
            anchor = entry.find("a")['href']
            if self.__class__.DEBUG:
                print "Found link %s...\n\n"%anchor
            content = entry.renderContents()
            element = [anchor, content.decode('utf-8'), ]
            searchEntries.append(element)
        return(searchEntries)

   
    def conductSearch(self, searchEntity):
        soup = BeautifulSoup(self.currentPageContent)
        searchForm = soup.find("form", {'class' : 'search-form'})
        searchAction = searchForm['action']
        searchMethod = searchForm['method']
        searchFieldname = searchForm.find("input", {'type' : 'text'})['name']
        otherFields = searchForm.findAll("input", {'type' : 'hidden'})
        buttonField = searchForm.find("button", {'type' : 'submit'})
        self.postData = {searchFieldname : searchEntity, buttonField['id'] : buttonField['value']}
        for field in otherFields:
            fldname = ""
            fldval = ""
            if field.has_key('name'):
                fldname = field['name']
            elif field.has_key('id'):
                fldname = field['id']
            else:
                continue
            if field.has_key('value'):
                fldval = field['value']
            self.postData[fldname] = fldval
        encodedData = urllib.urlencode(self.postData)
        self.requestUrl = searchAction
        if searchMethod.lower() == 'post':
            print "Making request to '%s'... \n\n"%(self.requestUrl)
            self.pageRequest = urllib2.Request(self.requestUrl, encodedData, self.httpHeaders)
        else:
            print "Making request to '%s'... \n\n"%(self.requestUrl + "?" + encodedData)
            self.pageRequest = urllib2.Request(self.requestUrl + "?" + encodedData, None, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
        except:
            print "Failed to make the search request for '%s'. Error: %s\n\n"%(searchEntity, sys.exc_info()[1].__str__())
            return(None)
        responseHeaders = self.pageResponse.info()
        if responseHeaders.has_key('Set-Cookie'):
            self.httpHeaders['Cookie'] += responseHeaders['Set-Cookie']
            self._processCookie()
        self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
        print "Parsing the first page of search results...\n\n"
        pageCtr = 1
        data_b = 1
        print "Starting to iterate over %s pages...\n\n"%self.searchListingPageDepth
        while int(pageCtr) < int(self.searchListingPageDepth):
            soup = BeautifulSoup(self.currentPageContent)
            searchEntries = self._getSearchResults(self.currentPageContent, data_b.__str__())
            data_b += 10
            pageCtr += 1
            self.searchEntries.append(searchEntries)
            nextPageAnchor = soup.find("a", {'data-b' : data_b.__str__()})
            if not nextPageAnchor:
                print "Could not find the next page link. Either we have iterated over the entire search listing, or we are on a wrong page.\n\n"
                break
            nextPageUrl = nextPageAnchor['href']
            self.requestUrl = nextPageUrl
            self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
            print "Fetching page #%s from '%s'... \n\n"%(pageCtr.__str__(), self.requestUrl)
            try:
                self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            except:
                print "Failed to fetch page #%s... Error: %s\n\n"%(pageCtr, sys.exc_info()[1].__str__())
                continue
            self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())

        return(self.searchEntries)


    def _findAllLocalPageUrls(self, domain):
        """
        This method checks for all anchor tags only. Other tags
        may be handled later. Returns a list of unique URLs
        """
        print "Fetching all local URLs from this page.\nAssumption: We will find all relevant local URLs from this page."
        allAnchors = re.findall(self.__class__.anchorTagPattern, self.currentPageContent)
        urlsDict = {}
        domainPattern = re.compile(domain, re.IGNORECASE)
        for anchor in allAnchors:
            anchor = re.sub(self.__class__.doubleQuotePattern, "", anchor)
            if self.__class__.bookmarkLinkPattern.search(anchor): # We don't want bookmark links that point inside the same page.
                continue
            if not self.__class__._isAbsoluteUrl(anchor):
                anchor = self.baseUrl + anchor
                urlsDict[anchor.__str__()] = 1
            else:
                domainSearch = domainPattern.search(anchor)
                if domainSearch:
                    urlsDict[anchor.__str__()] = 1
        return urlsDict.keys()


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
    yahoo = Yahoo()
    searchResults = yahoo.conductSearch(searchEntity)
    fy = open("../html/yahoo.txt", "w")
    for entry in searchResults:
        if entry.__len__() == 2:
            fy.write(entry[0].__str__() + " =====>> " + entry[1].__str__() + "\n\n")
        else:
            fy.write(entry.__str__() + "\n\n")
    fy.close()
    
