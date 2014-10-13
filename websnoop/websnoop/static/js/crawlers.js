// File containing javascript functions to crawl all supported social networking
// websites. All implemented functions are called through the single interface
// function named 'crawl'. The arguments to 'crawl' are the list of social net-
// working websites that the user wants crawled (default is all).



function createCORSRequest(method, url) {
  var xhr = new XMLHttpRequest();
  if ("withCredentials" in xhr) {
    xhr.open(method, url, true);
    xhr.setRequestHeader('Content-Type', 'text/plain');
    xhr.setRequestHeader('Origin', 'cpan.org');
  } 
  else {
    if (typeof XDomainRequest != "undefined") {
      xhr = new XDomainRequest();
      xhr.open(method, url);
    } 
    else{
      xhr = null;
    }
  }
  return xhr;
}


function getTitle(text) {
    return text.match('<title>(.*)</title>')[1];
}


function crawl(query){
    var report = "";
    // Iterate over all social networking sites referenced in 'query'.
    var url = 'http://www.cpan.org/';
    var xhr = createCORSRequest('GET', url);
    if (!xhr) {
        alert(url + ' does not support CORS');
    	return;
    }

    //xhr.onload = function() {
    xhr.onreaadystatechange = function() {
    	var text = xhr.responseText;
    	var title = getTitle(text);
    	alert('Response from CORS request to ' + url + ': ' + title);
    };

    xhr.onerror = function() {
    	alert('Woops, there was an error making the request.');
    };
    xhr.send();
    alert("xhr responseText: " + xhr.responseText);
    return(report);
}




