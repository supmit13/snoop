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



class Google(Crawler):
    """
    This class handles crawling and extraction of data from wayn.
    It is derived from class Crawler.
    """
    url = "http://www.google.co.in/search?sourceid=chrome&ie=UTF-8&q=##PLACEHOLDER##&oq=##PLACEHOLDER##&start=##PAGENUM##"
    placeholderPattern = re.compile("##PLACEHOLDER##")
    pageNumPattern = re.compile("##PAGENUM##")
    
    def __init__(self, cfgFile="../../conf/snoop.cnf", siteUrl="http://www.google.com/"):
        self.__class__.DEBUG = True
        print "Initializing...\n\n"
        self.opener = urllib2.build_opener() # This is my normal opener....
        self.cfgParser = ConfigParser()
        self.cfgParser.read(cfgFile)
        self.searchListingPageDepth = self.cfgParser.get("SearchEngines", "googlelistingdepth")
        self.sessionCookies = ""
        self.httpHeaders = { 'User-Agent' : r'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.10) Gecko/20111103 Firefox/3.6.24',  'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language' : 'en-us,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate', 'Accept-Charset' : 'ISO-8859-1,utf-8;q=0.7,*;q=0.7', 'Keep-Alive' : '115', 'Connection' : 'keep-alive', }
        self.homeDir = os.getcwd()
        self.websiteUrl = siteUrl
        self.useProxy = False # By default, useProxy is false, i.e, we do not use proxies.
        self.requestUrl = self.websiteUrl
        self.baseUrl = None
        self.pageRequest = None
        self.domainName = None
        if self.websiteUrl:
            parsedUrl = urlparse(self.requestUrl)
            self.baseUrl = parsedUrl.scheme + "://" + parsedUrl.netloc
            netlocParts = parsedUrl.netloc.split(".")
            self.domainName = ".".join(netlocParts[1:])
            # Here we just get the webpage pointed to by the website URL
        self.pageResponse = None
        self.requestMethod = "GET"
        self.postData = {}
        self.sessionCookies = None
        self.currentPageContent = None
        self.siteUsername = None
        self.sitePassword = None
        self.__isLoggedIn = False
        self.searchResults = None
        self.logFile = self.cfgParser.get("Logging", "logfile")
        self.logPath = self.cfgParser.get("Logging", "logpath")

        self.proxyUrls = None
        self.searchResults = None
        try:
            proxiesLine = self.cfgParser.get("Proxy", "urlslist")
            self.proxyUrls = proxiesLine.split(",")
            self.useProxy = True
        except:
            pass


    def doLogin(self, username="", password=""):
        pass # No login is required to search

    def _searchGoogle(self, targetString, pageNum=0):
        blockSize = 10
        startBlock = (pageNum * blockSize).__str__()
        targetString = targetString.replace(" ", "+")
        targetUrl = re.sub(self.__class__.placeholderPattern, targetString, self.__class__.url)
        targetUrl = re.sub(self.__class__.pageNumPattern, startBlock, targetUrl)
        self.requestUrl = targetUrl
        self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        try:
            self.pageResponse = self.opener.open(self.pageRequest)
            self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
        except:
            print "Could not fetch the page: %s"%sys.exc_info()[1].__str__()
            return None
        return self.currentPageContent


    def _getSearchResults(self, searchPageContent):
        startPhrase = "<body"
        endPhrase = "function _gjp(){"
        if not searchPageContent:
            return(None)
        pageParts = searchPageContent.split(startPhrase)
        desiredPart = pageParts[1]
        pageParts2 = desiredPart.split(endPhrase)
        desiredPart = pageParts2[0]
        #return desiredPart
        h3classrPattern = re.compile("<h3\s+class=\"r\">", re.IGNORECASE | re.MULTILINE | re.DOTALL)
        # Here, find out <h3 class="r">....
        allSearchHits = h3classrPattern.split(desiredPart)
        allAnchorLinks = []
        for searchHit in allSearchHits:
            try:
                soup = BeautifulSoup(searchHit)
                anchor = soup.find("a")
                if anchor is not None and anchor.has_key("href"):
                    href = anchor['href']
                    allAnchorLinks.append(href)
            except:
                continue
        return allAnchorLinks


    # 'conductGoogleSearch' actually calls '_searchGoogle' and '_getSearchResults' to do the job of actually
    # searching and parsing the google search pages and returns a tuple of URLs pointing to the various sites
    # that appeared in the search listing. The arguments to this function are the search string and the 
    # count of pages that need to be traversed.    
    def conductSearch(self, searchEntity):
        print "Retrieving the search page...\n\n"
        searchPage = self._searchGoogle(searchEntity) # Get the first search page.
        pageCtr = 0
        anchors = []
        anchors = self._getSearchResults(searchPage)
        print "Retrieved anchors from the first search listing page. Going to iterate over %s pages...\n\n"%self.searchListingPageDepth
        while int(pageCtr) < int(self.searchListingPageDepth):
            pageCtr += 1
            print "Looking up page #%s of %s in search listing...\n\n"%(pageCtr.__str__(), self.searchListingPageDepth)
            searchPage = self._searchGoogle(searchEntity, pageCtr)
            anchors2 = []
            anchors2 = self._getSearchResults(searchPage)
            if not anchors2:
                if self.__class__.DEBUG:
                    print "No anchors found in page.\n\n"
                continue
            anchors.extend(anchors2)
        anchors = tuple(anchors)
        return anchors


    def _getDomain(cls, webUrl):
        obj = urlparse(webUrl)
        domain = obj.netloc
        domain = re.sub(re.compile(r"\:\d{2,4}"), "", domain)
        return(domain)
    _getDomain = classmethod(_getDomain)


    # This method checks for all anchor tags only. Other tags may be handled later. Returns a list of unique URLs
    def _findAllLocalPageUrls(self, domain):
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

    # This method checks if the list of anchors/links passed as argument has unique domains. 
    # If not, we retain only the first anchor/link and drop all the subsequent anchors.
    # This should be fine since when we process the first anchor, we will process all pages
    # from the website. Of course, we assume, though I am not sure if we may do so, that
    # the dropped link appears as a link in the page being processed.
    def checkDomainUniqueness(self, anchorsList):
        uniqueDomainAnchorsDict = {}
        for anchor in anchorsList:
            domain = self.__class__._getDomain(anchor)
            if uniqueDomainAnchorsDict.has_key(domain): # We already have a link for this domain.
                continue
            else: 
                uniqueDomainAnchorsDict[domain] = anchor
        return(uniqueDomainAnchorsDict.values())



if __name__ == "__main__":
    searchEntity = sys.argv[1]
    google = Google()
    searchResults = google.conductSearch(searchEntity)
    fg = open("google.txt", "w")
    for entry in searchResults:
        fg.write(entry)
    fg.close()
    
