// Single-page routing: a request for a path with no file extension is a page of the web interface,
// so it is served index.html, and the app's router shows the page. API paths never reach this
// function, because they have their own behaviour, so an API error is never replaced.
function handler(event) {
  var request = event.request;
  var last = request.uri.split('/').pop();
  if (last.indexOf('.') === -1) {
    request.uri = '/index.html';
  }
  return request;
}
