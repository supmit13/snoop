var tabs = require("sdk/tabs");
var self = require("sdk/self");

// In order to access multiple domains, we use the following technique to bypass the cross-origin request policy:
// We open a window in which we load the sites we need, but the window is kept in the background, allowing you to
// do whatever you are doing. I understand it is not a great way to handle things, but in the absence of any better
// way (to access multiple domains from javascript code), I am forced to use this. Each of the sites get loaded in
// its own window/tab, and the javascript code here will read the contents as and when they get loaded. The windows/
// tabs are closed automatically once their purpose is served.
//var scriptlines = "function crawlPages(){var fbUrl=\"http://www.facebook.com\";var twtrUrl=\"http://www.twitter.com\";var lnUrl=\"http://www.linkedin.com\";var request = new XMLHttpRequest();request.onreadystatechange = function(){ if (request.readyState === 4) {if (request.status === 200) { console.log(\"OK\"); } else { console.log(\"NOT OK\" + request.status); }}};request.open(\"GET\", fbUrl , true);request.send(null);}";
var scriptlines = "function crawlPages(){var fbUrl=\"http://www.facebook.com\";var twtrUrl=\"http://www.twitter.com\";var lnUrl=\"http://www.linkedin.com\";var fbw=window.open(fbUrl);var twtrw=window.open(twtrUrl);var lnw=window.open(lnUrl);fbw.onload=function(){alert(\"LOADED FB\");};twtrw.onload=function(){alert(\"LOADED TWTR\");};lnw.onload=function(){alert(\"LOADED LN\");};}";

var button = require("sdk/ui/button/action").ActionButton({
  id: "style-tab",
  label: "Style Tab",
  icon: "./icon16.png",
  onClick: openApp
});


function openApp(tab) {
  tabs.activeTab.attach({
  contentScript: "var homeUrl = 'http://localhost:8000/';window.location.href=homeUrl;",
  });
  var pageMod = require("sdk/page-mod");
    pageMod.PageMod({
    include: "http://localhost:8000/",
    contentScript: scriptlines + "document.defaultView.addEventListener('message', function(event) { console.log(event.data); console.log(event.origin); crawlPages(); }, false);"
  });
}

