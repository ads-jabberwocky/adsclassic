#!/usr/bin/env python
try:  # python 2
    from BaseHTTPServer import HTTPServer, test
    from CGIHTTPServer import CGIHTTPRequestHandler
except ImportError:  # python 3
    from http.server import HTTPServer, CGIHTTPRequestHandler, test


class myCGIHTTPRequestHandler(CGIHTTPRequestHandler):
    def send_head(self):
        # rewrite URLs: /abs/[bibcode] => script in /cgi-bin
        if self.path.startswith('/abs/'):
            self.path = '/cgi-bin/nph-data_query?link_type=ABSTRACT&bibcode=' + self.path[5:]
        return CGIHTTPRequestHandler.send_head(self)


if __name__ == '__main__':
    test(myCGIHTTPRequestHandler, HTTPServer)