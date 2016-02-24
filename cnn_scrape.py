#! /usr/bin/env python3

import collections
import functools
from html.parser import HTMLParser
import re
import sys
import urllib.request
import urllib.error


def main(argv=None):
    urls = []
    if len(argv) < 2:
        raise FileNotFoundError('Please input a file with urls as the first argument')
    with open(argv[1]) as f:
        for line in f.readlines():
            line = line.rstrip("\n")
            if line != '':
                urls.append(line)
    articles = []
    for url in urls:
        articles.append(get_article(url))

    data_matrix = get_data_matrix(articles)
    write_data_matrix(data_matrix)


class CNNScraper(HTMLParser):
    def __init__(self):
        self._get_data = False
        self._get_title = False
        self.title = 'NoTitleError'
        self.body = ''
        super().__init__()

    def handle_starttag(self, tag, attributes):
        if tag == 'p':
            for attr in attributes:
                if attr[0] == 'class' and 'zn-body__paragraph' in attr[1]:
                    self._get_data = True
        if tag == 'h1':
            for attr in attributes:
                if attr[0] == 'class' and 'pg-headline' in attr[1]:
                    self._get_title = True

    def handle_endtag(self, tag):
        if tag == 'p':
            self._get_data = False
        if tag == 'h1':
            self._get_title = False

    def handle_data(self, data):
        if self._get_data is True:
            self.body += ' ' + data
        if self._get_title is True:
            self.title = data

    def scrape_article(self, url):
        self.feed(url)
        self.body.replace("\n", " ")
        return [self.title, self.body]


def get_article(url: str):
    req = urllib.request.Request(url)
    try:
        html_gunk = urllib.request.urlopen(req).read().decode('utf-8')
    except urllib.error.HTTPError as e:
        print("{0} error: {2}".format(e.code, e.reason))
    except urllib.error.URLError as e:
        print("error invalid url: {1}".format(e.reason))
    else:
        cnn_parser = CNNScraper()
        return cnn_parser.scrape_article(html_gunk)


def get_data_matrix(articles):
    article_counters = {}
    for article in articles:
        # remove commas from titles. they will mess up csv file
        article[0] = article[0].replace(',', '')
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
    data_matrix = [('words', all_words)]
    for article in articles:
        # row looks like (article_name, (count, count, count, ... ))
        row = (article[0], tuple(article_counters[article[0]][word] for word in all_words))
        data_matrix.append(row)
    return data_matrix


def write_data_matrix(data_matrix):
    for row in data_matrix:
        counts = ','.join((str(count) for count in row[1]))
        print(row[0], ',', counts)

if __name__ == "__main__":
    main(sys.argv)
