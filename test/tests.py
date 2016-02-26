#!/usr/bin/env python3

import sys
import urllib.request
import unittest
sys.path.insert(0, '../')
import cnn_scrape as scrape

# doesn't work lol


class TestUrlMethods(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

        url = 'http://www.cnn.com/2016/02/22/us/kalamazoo-michigan-shooting/index.html'
        req = urllib.request.Request(url)
        self.raw_html = urllib.request.urlopen(req).read().decode('utf-8')
        # used this regex for formatting file body r'((.){0,90}(\w*)\.?,?\??"?\'?)\s?'
        self.title = 'Kalamazoo shooting suspect appears in court - CNN.com'
        with open('test_article.txt') as f:
            self.body = f.read().replace("\n", " ")

    def test_scrape(self):
        pass

if __name__ == '__main__':
    unittest.main()