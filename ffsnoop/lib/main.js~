var tabs = require("sdk/tabs");
var self = require("sdk/self");

var button = require("sdk/ui/button/action").ActionButton({
  id: "style-tab",
  label: "Style Tab",
  icon: "./icon-16.png",
  onClick: openApp
});

function openApp(tab) {
  tabs.activeTab.attach({
  contentScript: "window.location.href='http://localhost:8000/'",
});
 
}
