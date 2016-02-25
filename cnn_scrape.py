#! /usr/bin/env python3

import collections
import functools
from html.parser import HTMLParser
import re
import sys
import urllib.error
from urllib.parse import urlparse
import urllib.request


def main(argv=None):
    urls = []
    if len(argv) < 2:
        raise FileNotFoundError('Please input a file with urls as the first argument')
    with open(argv[1]) as f:
        for line in f.readlines():
            line = line.rstrip("\n")
            if line != '':
                urls.append(urlparse(line))
    articles = []
    for url in urls:
        articles.append(get_article(url))

    data_matrix = get_data_matrix(articles)
    write_data_matrix(data_matrix)


class CNNScraper(HTMLParser):
    def __init__(self):
        self.get_data = False
        self.get_title = False
        self.title = 'NoTitleError'
        self.body = ''
        super().__init__()

    def scrape_article(self, url):
        self.feed(url)
        self.body.replace("\n", " ")
        return [self.title, self.body]


class CNNRegularScraper(CNNScraper, HTMLParser):
    def __init__(self):
        super().__init__()

    def handle_starttag(self, tag, attributes):
        if tag == 'p':
            for name, value in attributes:
                if name == 'class' and 'zn-body__paragraph' in value:
                    self.get_data = True
        if tag == 'h1':
            for name, value in attributes:
                if name == 'class' and 'pg-headline' in value:
                    self.get_title = True

    def handle_endtag(self, tag):
        if tag == 'p':
            self.get_data = False
        if tag == 'h1':
            self.get_title = False

    def handle_data(self, data):
        if self.get_data:
            self.body += ' ' + data
        if self.get_title:
            self.title = data


class CNNMoneyScraper(CNNScraper, HTMLParser):
    def __init__(self):
        super().__init__()
        self.recording = 0
        self.tag_stack = []

    def handle_starttag(self, tag, attributes):
        self.tag_stack.append((tag, attributes))
        if tag == 'h1':
            for name, value in attributes:
                if name == 'class' and 'article-title' in value:
                    self.get_title = True
        if tag != 'div':
            return
        if self.recording:
            self.recording += 1
            return
        for name, value in attributes:
            if name == 'id' and value == 'storytext':
                break
        else:
            return
        self.recording = 1

    def handle_endtag(self, tag):
        self.tag_stack.pop()
        if tag == 'div' and self.recording:
            self.recording -= 1
        elif tag == 'h1':
            self.get_title = False

    def handle_data(self, data):
        if self.recording and 'p' in self.tag_stack:
            self.body += ' ' + data
        if self.get_title:
            self.title = data


def get_article(url_parsed):
    req = urllib.request.Request(url_parsed.geturl())
    try:
        html_gunk = urllib.request.urlopen(req).read().decode('utf-8')
    except urllib.error.HTTPError as e:
        print("{0} error: {2}".format(e.code, e.reason))
    except urllib.error.URLError as e:
        print("error invalid url: {1}".format(e.reason))
    else:
        # if you add a new subdomain, likely should add it before 'cnn.com' so it gets chosen first
        if 'money.cnn.com' in url_parsed.netloc:
            cnn_parser = CNNMoneyScraper()
        elif 'cnn.com' in url_parsed.netloc:
            cnn_parser = CNNRegularScraper()
        else:
            raise NotImplementedError('url "{0}" not supported'.format())
        return cnn_parser.scrape_article(html_gunk)


def get_data_matrix(articles):
    article_counters = {}
    for article in articles:
        # remove commas from titles. they will mess up csv file
        article[0] = article[0].replace(',', '').strip(' ')
        # replace hyphens with spaces and make all characters lowercase
        article[1] = article[1].replace('-', ' ').lower()
        # remove any character that is not a word, space, or '
        # ' is kept for contractions and possessive words
        article[1] = re.sub(r'[^\w\s\']', '', article[1])
        words = article[1].split()
        remove_words = []
        for i in range(len(words)):
            # strip quotes and ' off the ends of words (' in the middle of words is retained)
            words[i] = words[i].strip("'").strip('"')
            # if a "word" is left and it contains only non-alphabetic chars, remove it
            if re.match(r'\W+', words[i]):
                remove_words.append(words[i])
        for word in remove_words:
            words.remove(word)

        article_counters[article[0]] = collections.Counter(words)

    # all_words is a tuple of each unique word
    all_words = tuple(functools.reduce(set.union, map(set, article_counters.values())))
    data_matrix = [('WORDS:', all_words)]
    for article in articles:
        # row looks like (article_name, (count, count, count, ... ))
        row = (article[0], tuple(article_counters[article[0]][word] for word in all_words))
        data_matrix.append(row)
    return data_matrix


def write_data_matrix(data_matrix):
    for row in data_matrix:
        counts = ','.join((str(count) for count in row[1]))
        print(row[0] + ',' + counts)

if __name__ == "__main__":
    main(sys.argv)
