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



class Facebook(Crawler):
    """
    This class handles crawling and extraction of data from facebook.com.
    It is derived from class Crawler.
    """
    def __init__(self):
        self.__class__.DEBUG = True
        super(Facebook, self).__init__("../../conf/snoop.cnf", "http://www.facebook.com/", "https://www.facebook.com/login.php?login_attempt=1")
        self.httpHeaders['Accept-Encoding'] = "gzip,deflate,sdch"
        self.httpHeaders['Cache-Control'] = "max-age=0"

        # headers specific to facebook
        self.contentSecurityPolicy = ""
        self.xFbDebug = ""
        responseHeaders = self.pageResponse.info()
        if responseHeaders.has_key('content-security-policy'):
            self.contentSecurityPolicy = responseHeaders.getheaders('content-security-policy')
        if responseHeaders.has_key('x-fb-debug'):
            self.xFbDebug = responseHeaders.getheaders('x-fb-debug')
            
        self.availableCreds = self.loadCredentials("facebook")
        #print self.availableCreds
        

    def doLogin(self, username="", password=""):
        soup = BeautifulSoup(self.currentPageContent)
        loginForm = soup.find("form", {'id' : 'login_form'})
        emailField = loginForm.find("input", {'type' : 'text'})
        emailFieldName = emailField['name']
        passwdField = loginForm.find("input", {'type' : 'password'})
        passwdFieldName = passwdField['name']
        otherLoginFields = loginForm.findAll("input", {'type' : 'hidden'})
        otherFieldNames = {}
        for loginField in otherLoginFields:
            if loginField.has_key("name"):
                otherFieldNames[loginField['name']] = loginField['value'] or None
            elif loginField.has_key("id"):
                otherFieldNames[loginField['id']] = loginField['value'] or None

        checkbox = loginForm.find("input", {'type' : 'checkbox'})
        otherFieldNames[checkbox['name']] = checkbox['value']
        submitButton = loginForm.find("input", { 'type' : 'submit' })
        otherFieldNames[submitButton['id']] = submitButton['value']

        # Now select a username and password from self.availableCreds randomly
        credsLen = self.availableCreds.__len__()
        randomIndex = random.randint(0, credsLen - 1)
        fbUsernames = self.availableCreds.keys()
        self.siteUsername = fbUsernames[randomIndex]
        self.sitePassword = self.availableCreds[self.siteUsername]
        self.requestMethod = 'POST'
        self.postData = { emailFieldName : self.siteUsername, passwdFieldName : self.sitePassword }
        for fieldName in otherFieldNames.keys():
            self.postData[fieldName] = otherFieldNames[fieldName]
        self.httpHeaders['Referer'] = self.requestUrl
        self.requestUrl = loginForm['action']
        if not self.__class__._isAbsoluteUrl(self.requestUrl):
            self.requestUrl = self.baseUrl + self.requestUrl
        self.loginUrl = self.requestUrl
        
        urlencodedData = urllib.urlencode(self.postData)
        self.pageRequest = urllib2.Request(self.requestUrl, urlencodedData, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.sessionCookies = self.__class__._getCookieFromResponse(self.pageResponse)
            self.httpHeaders["Cookie"] = self.sessionCookies
            responseHeaders = self.pageResponse.info()
            if responseHeaders.has_key('location'):
                self.requestUrl = responseHeaders['location']
            else:
                print "Could not find redirection URL during logging in. Giving up...\n"
                return None
        except:
            print "Failed while making the POST request to login. Giving up...\n"
            return None
        if self.__class__.DEBUG:
            print "\n===========================================\n"
            print "Request URL: " + self.requestUrl
            print "Session Cookies: " + self.sessionCookies
            print "\n===========================================\n"
        self.pageRequest = urllib2.Request(self.requestUrl, None, self.httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            self.httpHeaders['Referer'] = self.requestUrl
        except:
            print "Failed while redirecting to user's homepage during login. Giving up...\n"
            return None
        self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
        return (self.currentPageContent)


    def conductSearch(self, searchText):
        """
        Conducts a search for searchText on facebook search box. Returns a
        list of matches with links to the matched profiles and some basic info.
        """
        soup = BeautifulSoup(self.currentPageContent)
        # Make sure we are logged in...
        if not self.isLoggedIn():
            print "We are not logged in. Please login to conduct a search.\n"
            return None
        # Find the search form ... This is to check that we can actually conduct a search from this page.
        inputBoxes = soup.findAll("input", {'type' : 'text'})
        foundSearchBox = False
        for box in inputBoxes:
            if box.has_key('name') and box['name'] == 'q':
                foundSearchBox = True
                break
        # Create the search query...
        grammarVersion, viewer, revision = "", "", ""
        self.requestUrl = "https://www.facebook.com/typeahead/search/facebar/query/?"
        queryParams = {'value' : '["%s"]'%searchText, 'context' : 'facebar'}
        grammarVersionPattern = re.compile(r"\"grammar_version\":\"([^\"]+)\"", re.MULTILINE | re.DOTALL)
        viewerPattern = re.compile(r"\"viewer\":(\d+),", re.MULTILINE | re.DOTALL)
        revisionPattern = re.compile(r"\"revision\":(\d+),", re.MULTILINE | re.DOTALL)
        grammarVersionMatch = grammarVersionPattern.search(self.currentPageContent)
        if grammarVersionMatch:
            grammarVersionGroups = grammarVersionMatch.groups()
            grammarVersion = grammarVersionGroups[0]
        viewerMatch = viewerPattern.search(self.currentPageContent)
        if viewerMatch:
            viewerGroups = viewerMatch.groups()
            viewer = viewerGroups[0]
        revisionMatch = revisionPattern.search(self.currentPageContent)
        if revisionMatch:
            revisionGroups = revisionMatch.groups()
            revision = revisionGroups[0]
        queryParams['grammar_version'] = grammarVersion
        queryParams['viewer'] = viewer
        queryParams['rsp'] = 'search'
        queryParams['max_results'] = '50'
        queryParams['__user'] = viewer
        queryParams['__a'] = '1'
        queryParams['__rev'] = revision
        #queryParams['__dyn'] = '7n8anEBQ9FoBZypQ9UoHFaeFDzECQqbx2mbACFaaBGeqrYw8popyui9zpUgDyQqV8KVpoW8xG'
        #queryParams['__req'] = '18'
        #queryParams['qid'] = '22'
        #queryParams['sid'] = '0.20711175492033362'
        queryString = urllib.urlencode(queryParams)
        self.requestUrl += queryString
        self.requestUrl = self.requestUrl.replace("%5B", '[').replace("%5D", ']')

        # Create custom headers with lowercase header names...
        httpHeaders = {}
        for hdr in self.httpHeaders.keys():
            httpHeaders[hdr] = self.httpHeaders[hdr]
        httpHeaders[':host'] = 'www.facebook.com'
        httpHeaders['accept'] = '*/*'
        httpHeaders[':scheme'] = 'https'
        httpHeaders[':method'] = 'GET'
        httpHeaders[':path'] = self.requestUrl
        httpHeaders[':path'] = re.sub(re.compile(r'https://www.facebook.com'), "", httpHeaders[':path'])
        httpHeaders[':version'] = r"HTTP/1.1"
        httpHeaders['referer'] = httpHeaders['Referer']
        httpHeaders['accept-language'] = httpHeaders['Accept-Language']
        httpHeaders['accept-encoding'] = httpHeaders['Accept-Encoding']
        self._processCookie()
        httpHeaders['cookie'] = "locale=en_US;" + self.httpHeaders['Cookie']
        httpHeaders['user-agent'] = httpHeaders['User-Agent']

        # delete all the headers whose keys start with uppercase letter
        httpHeaders.pop('Referer', None)
        httpHeaders.pop('Accept', None)
        httpHeaders.pop('Connection', None)
        httpHeaders.pop('Cache-Control', None)
        httpHeaders.pop('Keep-Alive', None)
        httpHeaders.pop('Accept-Charset', None)
        httpHeaders.pop('Accept-Language', None)
        httpHeaders.pop('Accept-Encoding', None)
        httpHeaders.pop('Cookie', None)
        httpHeaders.pop('User-Agent', None)
        if self.__class__.DEBUG:
            print "\n===========================================\n"
            print self.requestUrl
            print httpHeaders
            print "\n===========================================\n"
        # Now, create the request and hit search...
        self.pageRequest = urllib2.Request(self.requestUrl, None, httpHeaders)
        try:
            self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
            # Process pageResponse to extract search results...
            self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
            return(self.currentPageContent)
        except:
            print "Could not make the HTTP request for search term '%s' - Error: %s\n"%(searchText, sys.exc_info()[1].__str__())
            return (None)


    
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
    

    def getContacts(self, targetEntity):
        """
        Retrieves the list of level 1 friends (or group members) of the target entity.
        Returns the list of URLs to those entities along with some basic data.
        """
        pass


    def buildGraph(self, targetEntity, level=2):
        """
        Create a graph of contacts (or members in case of groups) of the target entity.
        Returns the results in the form of a dictionary. The 'level' parameter specifies
        the depth and it defaults to 2.
        """
        pass


    def parsePageHtml(self):
        """
        Parses the HTML content in the object's currentPageContent attribute and sets the
        object's 'searchResults' attribute with the resultant dict. Returns the number of
        matches found.
        """
        html = self.currentPageContent
        soup = BeautifulSoup(html)
        allSpans = soup.findAll("span")
        pageUrl, gender, interests, languages, mobilephone, email,address = "", "", "", "", "", "",""
        for span in allSpans:
            spanContent = span.renderContents()
            if spanContent != "Contact Information":
                continue
            spanNext = span.findNext("span")
            spanNextText = spanNext.renderContents()
            spanNext2 = spanNext
            if spanNextText == "Mobile Phones":
                spanNext2 = spanNext.findNext("span")
                mobilephone = spanNext2.renderContents()
            spanNext2 = spanNext2.findNext("span")
            spanNext2Text = spanNext2.renderContents()
            while spanNext2Text != "Address":
                spanNext2 = spanNext2.findNext("span")
                spanNext2Text = spanNext2.renderContents()
                spanNext2Text = spanNext2Text.strip()
            spanNext3 = spanNext2.findNext("span")
            if spanNext3 is not None:
                address = spanNext3.renderContents()
            spanNext4 = spanNext3.findNext("span")
            while spanNext4.renderContents() != "Email":
                spanNext4 = spanNext4.findNext("span")
            spanNext4 = spanNext4.findNext("span")
            email = spanNext4.renderContents()      

        for span in allSpans:
            spanContent = span.renderContents()
            if spanContent != "Basic Information":
                continue
            if spanContent == "Basic Information":
                spanNext = span.findNext("span")
                spanNextText = spanNext.renderContents()
                while spanNextText != "Gender":
                    spanNext = spanNext.findNext("span")
                    spanNextText = spanNext.renderContents()
                spanNext2 = spanNext.findNext("span")
                gender = spanNext2.renderContents()
                spanNext3 = spanNext2.findNext("span")
                if spanNext3.renderContents() == "Interested In":
                    spanNext3 = spanNext3.findNext("span")
                    interests = spanNext3.renderContents()
                spanNext4 = spanNext3.findNext("span")
                while spanNext4.renderContents() != "Languages":
                    spanNext4 = spanNext4.findNext("span")
                spanNext4 = spanNext4.findNext("span")
                languages = spanNext4.renderContents()
        mobilephone = re.sub(self.__class__.htmlTagPattern, "", mobilephone)
        address = re.sub(self.__class__.htmlTagPattern, "", address)
        email = re.sub(self.__class__.htmlTagPattern, "", email)
        info = {'mobile' : mobilephone, 'address' : address, 'email' : email, 'gender' : gender, 'interests' : interests, 'languages' : languages }
        return(info)






if __name__ == "__main__":
    searchEntity = sys.argv[1]
    facebook = Facebook()
    pageContent = facebook.doLogin()
    ff = open("dumplogin.html", "w")
    ff.write(pageContent)
    ff.close()
    if not facebook.assertLogin("Home") or not facebook.assertLogin("Inbox"):
        print "Could not login as %s\nTry with a different username.\n"%facebook.siteUsername
        sys.exit()
    else:
        soup = BeautifulSoup(pageContent)
        nameSpan = soup.find("span", {'class' : '_2dpb'})
        name = nameSpan.text
        print "Logged in successfully as '%s'\n"%name
    searchResult = facebook.conductSearch(searchEntity)
