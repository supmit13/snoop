
import os, sys, re, time, gzip
import urllib, urllib2, httplib
from BeautifulSoup import BeautifulSoup
from urlparse import urlparse, urlsplit
import StringIO
import mimetypes, mimetools
from ConfigParser import ConfigParser
#import tidy
import xml.etree.ElementTree as etree


"""
Some utility function definitions
"""
def urlEncodeString(s):
    tmphash = {'str' : s }
    encodedStr = urllib.urlencode(tmphash)
    encodedPattern = re.compile(r"^str=(.*)$")
    encodedSearch = encodedPattern.search(encodedStr)
    encodedStr = encodedSearch.groups()[0]
    encodedStr = encodedStr.replace('.', '%2E')
    encodedStr = encodedStr.replace('-', '%2D')
    encodedStr = encodedStr.replace(',', '%2C')
    return (encodedStr)



class NoRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        infourl = urllib.addinfourl(fp, headers, req.get_full_url())
        infourl.status = code
        infourl.code = code
        return infourl

    http_error_300 = http_error_302
    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302



class Crawler(object):
    DEBUG = True
    # Global regex patterns.
    absUrlPattern = re.compile(r"^https?:\/\/", re.IGNORECASE)
    multipleWhiteSpacesPattern = re.compile(r"\s+", re.MULTILINE | re.DOTALL)
    htmlTagPattern = re.compile(r"<[^>]+>", re.MULTILINE | re.DOTALL)
    htmlEntityPattern = re.compile(r"\W\&\w+;\W")
    pathEndSlashPattern = re.compile(r"\/$")
    newlinePattern = re.compile(r"\n", re.MULTILINE | re.DOTALL)
    emailIdPattern = re.compile(r"\W(\w+\.?\w{0,}@\w+\.\w+\.?\w*)\W", re.MULTILINE | re.DOTALL)
    anchorTagPattern = re.compile(r"<a\s+[^>]{0,}href=([^\s\>]+)\s?.*?>\s*\w+", re.IGNORECASE | re.MULTILINE | re.DOTALL)
    bookmarkLinkPattern = re.compile("^#",re.MULTILINE | re.DOTALL)
    doubleQuotePattern = re.compile('"', re.MULTILINE | re.DOTALL)

    htmlEntitiesDict = {'&nbsp;' : ' ', '&#160;' : ' ', '&amp;' : '&', '&#38;' : '&', '&lt;' : '<', '&#60;' : '<', '&gt;' : '>', '&#62;' : '>', '&apos;' : '\'', '&#39;' : '\'', '&quot;' : '"', '&#34;' : '"'}

    def __init__(self, cfgFile, siteUrl="", loginUrl=""):
        print "Initializing...\n\n"
        # Create the opener object(s). Might need more than one type if we need to get pages with unwanted redirects.
        self.opener = urllib2.build_opener() # This is my normal opener....
        self.no_redirect_opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), NoRedirectHandler()) # this one won't handle redirects.
        #self.debug_opener = urllib2.build_opener(urllib2.HTTPHandler(debuglevel=1))
        # Initialize some object properties.
        self.sessionCookies = ""
        self.httpHeaders = { 'User-Agent' : r'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.10) Gecko/20111103 Firefox/3.6.24',  'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language' : 'en-us,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate', 'Accept-Charset' : 'ISO-8859-1,utf-8;q=0.7,*;q=0.7', 'Keep-Alive' : '115', 'Connection' : 'keep-alive', }
        self.homeDir = os.getcwd()
        self.websiteUrl = siteUrl
        self.loginUrl = loginUrl
        self.useProxy = False # By default, useProxy is false, i.e, we do not use proxies.
        self.requestUrl = self.loginUrl
        if not self.requestUrl:
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
            self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        self.pageResponse = None
        self.requestMethod = "GET"
        self.postData = {}
        self.sessionCookies = None
        self.currentPageContent = None
        if self.websiteUrl:
            try:
                self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
                self.sessionCookies = self.__class__._getCookieFromResponse(self.pageResponse)
                self.httpHeaders["Cookie"] = self.sessionCookies
                if self.__class__.DEBUG:
                    print "Request URL: " + self.requestUrl
                    print "Session Cookies: " + self.sessionCookies.__str__()
            except:
                print __file__.__str__() + ": Couldn't fetch page due to limited connectivity (1). Please check your internet connection and try again. " + sys.exc_info()[1].__str__()
            self.httpHeaders["Referer"] = self.requestUrl
            # Initialize the account related variables...
            self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
            if not self.currentPageContent:
                print "Could not access the website content of " + self.websiteUrl
        self.siteUsername = None
        self.sitePassword = None
        self.__isLoggedIn = False
        self.cfgParser = ConfigParser()
        self.cfgParser.read(cfgFile)
        self.captchaServiceName = self.cfgParser.get("CaptchaAPI", "servicename")
        self.captchaServiceUsername = self.cfgParser.get("CaptchaAPI", "username")
        self.captchaServicePassword = self.cfgParser.get("CaptchaAPI", "password")
        self.logFile = self.cfgParser.get("Logging", "logfile")
        self.logPath = self.cfgParser.get("Logging", "logpath")
        self.credsFile = self.cfgParser.get("CredentialsFile", "credsfile")
        self.availableCreds = {} # This will be a dict containing the available usernames as keys and passwords as values.
        # Should be populated in the respective modules.
        if self.logPath.endswith('/'):
            self.logPath = self.logPath[:-1]
        self.perSiteThreads = self.cfgParser.get("ThreadInfo", "max_per_site_threads")
        # Try to find if proxies are to be used. If so, load them in self.proxyUrls as a list.
        self.proxyUrls = None
        self.searchResults = None
        try:
            proxiesLine = self.cfgParser.get("Proxy", "urlslist")
            self.proxyUrls = proxiesLine.split(",")
            self.useProxy = True
        except:
            pass


    def getPageContent(self):
        if self.pageResponse:
            content = self.pageResponse.read()
            # Remove the line with 'DOCTYPE html PUBLIC' string. It sometimes causes BeautifulSoup to fail in parsing the html
            self.currentPageContent = re.sub(r"<.*DOCTYPE\s+html\s+PUBLIC[^>]+>", "", content)
            return(self.currentPageContent)
        else:
            return None


    def _decodeGzippedContent(cls, encoded_content):
        response_stream = StringIO.StringIO(encoded_content)
        decoded_content = ""
        try:
            gzipper = gzip.GzipFile(fileobj=response_stream)
            decoded_content = gzipper.read()
        except: # Maybe this isn't gzipped content after all....
            decoded_content = encoded_content
        return(decoded_content)

    _decodeGzippedContent = classmethod(_decodeGzippedContent)


    def buildGraph(self):
        pass # To be implemented by derived classes


    def conductSearch(self, searchEntity):
        pass # To be implemented by derived classes

    """
    sitename will be a single word string that identifies the website. e.g facebook, linkedin, etc.
    """
    def loadCredentials(self, sitename): 
        tree = etree.parse(self.credsFile)
        site = tree.find(sitename)
        credslist = site.getchildren()
        for cred in credslist:
            users = cred.getchildren()
            username = users[0].text
            password = users[1].text
            self.availableCreds[username] = password
        return(self.availableCreds)
                

    """
    Cookie extractor method to get cookie values from the HTTP response objects.
    """
    def _getCookieFromResponse(cls, lastHttpResponse):
        cookies = ""
        lastResponseHeaders = lastHttpResponse.info()
        responseCookies = lastResponseHeaders.getheaders("Set-Cookie")
        pathCommaPattern = re.compile(r"path=/;", re.IGNORECASE)
        domainPattern = re.compile(r"Domain=[^;]+", re.IGNORECASE)
        expiresPattern = re.compile(r"Expires=[^;]+;", re.IGNORECASE)
        if responseCookies.__len__() > 1:
            for cookie in responseCookies:
                cookieParts = cookie.split("path=/;")
                cookieParts[0] = re.sub(domainPattern, "", cookieParts[0])
                cookieParts[0] = re.sub(expiresPattern, "", cookieParts[0])
                cookies += "; " + cookieParts[0]
                #print cookieParts[0]
            return(cookies)
   
    _getCookieFromResponse = classmethod(_getCookieFromResponse)


    """
    Class method to identify if a URL (passed to this method) is a relative URL or an absolute one.
    """
    def _isAbsoluteUrl(cls, url):
        s = cls.absUrlPattern.search(url)
        if s:
            return True
        else:
            return False
    _isAbsoluteUrl = classmethod(_isAbsoluteUrl)

    def _getPathToPage(cls, url):
        urlParts = url.split("?")
        urlPartsList = urlParts[0].split("/")
        urlPartsList.pop()
        urlPath = "/".join(urlPartsList)
        return urlPath
    _getPathToPage = classmethod(_getPathToPage)

    def generateContextualFilename(cls, contextString, ext="txt"):
        countryFile = contextString
        countryFile = countryFile.replace(" ", "_")
        countryFile = countryFile.replace(",", "__CMA__")
        countryFile = countryFile.replace("&", "__AMP__")
        countryFile = countryFile.replace(";", "__SCLN__")
        countryFile = countryFile.replace(".", "__DOT__")
        countryFile = countryFile.replace("#", "__HSH__")
        countryFile = countryFile.replace("/", "__FSLH__")
        countryFile = countryFile.replace("(", "__OPNBR1__")
        countryFile = countryFile.replace(")", "__CLSBR1__")
        countryFile = countryFile.replace("{", "__OPNBR2__")
        countryFile = countryFile.replace("}", "__CLSBR2__")
        countryFile = countryFile.replace("[", "__OPNBR3__")
        countryFile = countryFile.replace("]", "__CLSBR3__")
        countryFile = countryFile + "." + ext
        return(countryFile)
    generateContextualFilename = classmethod(generateContextualFilename)

    # Method to assert if the login process was successful.
    def assertLogin(self, assertText):
        assertTextPattern = re.compile(assertText)
        if assertTextPattern.search(self.currentPageContent):
            return True
        return False

    def getConfigParserObject(self):
        return (self.cfgParser)

    def doLogin(self, username="", password=""):
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
            elif re.search(re.compile(r"Max\-Age=\-"), cookie) or re.search(re.compile(r"=deleted"), cookie):
                continue
            else:
                cookieparts = cookie.split("=")
                cookiesDict[cookieparts[0]] = cookieparts[1]
        self.sessionCookies = ""
        for cookie in cookiesDict.keys():
            self.sessionCookies += cookie + "=" + cookiesDict[cookie] + ";"
        self.httpHeaders['Cookie'] = self.sessionCookies
        return(self.sessionCookies)


    def getPage(self, url):
        self.requestUrl = url
        if not self.__class__._isAbsoluteUrl(self.requestUrl):
            self.requestUrl = self.baseUrl + self.requestUrl
        self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        while True:
            try:
                self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
                self.sessionCookies = self.__class__._getCookieFromResponse(self.pageResponse)
                self.httpHeaders["Cookie"] = self.httpHeaders["Cookie"].__str__() + self.sessionCookies.__str__()
                self._processCookie()
                self.httpHeaders['Referer'] = self.requestUrl
                responseHeaders = self.pageResponse.info()
                if responseHeaders.has_key('Location'):
                    self.requestUrl = responseHeaders['Location']
                    self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
                else:
                    self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
                    break
            except:
                print "Error trying to retrieve page pointed to by '%s' - %s\n"%(self.requestUrl, sys.exc_info()[1].__str__())
                return(None)
        return(self.currentPageContent)



    def _getLoginFormElementsDict(self):
        pass

    """
    def sanitizePageHTML(cls, pageContent):
        if not pageContent:
            return None
        tidy_opts = dict(output_xhtml=0, add_xml_decl=0, indent=1, tidy_mark=0)
        tidy_html = tidy.parseString(pageContent, **tidy_opts).__str__()
        return(tidy_html)
    sanitizePageHTML = classmethod(sanitizePageHTML)
    """

    def parsePageHtml(self):
        """
        Parses the HTML content in the object's currentPageContent attribute and sets the
        object's 'searchResults' attribute with the resultant dict. Returns the number of
        matches found.
        """
        pass

    # Method to check if the user is in logged in state. The params are: JobScraper object and a user provided string.
    # The user may or may not provide any string, i.e, the second parameter is optional. 'userPattern' (2nd argument)
    # can be any string that the user (of this method) considers to be a definitive proof of the login state.
    # Returns -1 if the object invoking the method does not have any content in its 'currentPageContent' attribute,
    # 0 if the user is not logged in, and 1, 2, 3 or 4 if the user is logged in. The value is determined by the
    # signout string pattern of the website. Case doesn't matter for the signout string. For 'userPattern', case does matter.
    def isLoggedIn(self, userPattern=None):
        logoutPatterns = (re.compile(r"Logout", re.IGNORECASE), re.compile(r"Log\s+out", re.IGNORECASE), re.compile(r"Signout", re.IGNORECASE), re.compile(r"Sign\s+out", re.IGNORECASE))
        if not self.currentPageContent or self.currentPageContent == "":
            print "No content in 'currentPageContent' attribute.\n"
            self.__isLoggedIn = False
            return(-1)
        else:
            if not userPattern:
                patctr = 1
                for logoutPat in logoutPatterns:
                    if logoutPat.search(self.currentPageContent):
                        self.__isLoggedIn = True
                        return(patctr)
                    else:
                        patctr += 1
            else: # userPattern is passed and is NOT None
                patctr = 1
                userPatternRegex = re.compile(userPattern)
                for logoutPat in logoutPatterns:
                    if logoutPat.search(self.currentPageContent) and userPatternRegex.search(self.currentPageContent):
                        self.__isLoggedIn = True
                        return(patctr)
                    else:
                        patctr += 1
        self.__isLoggedIn = False
        return (0)


    def logout(self):
        """
        Log the user out only if the user is logged in (that is, the method will check self.__isLoggedIn value and will
        try to perform the logout procedure if self.__isLoggedIn == True.
        """
        pass
    

    if __name__ == "__main__":
        pass
