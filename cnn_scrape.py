#! /usr/bin/env python3

import collections
import functools
from html.parser import HTMLParser
import newspaper
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
        article = newspaper.Article(url.geturl(), language='en')
        article.download()
        article.parse()
        articles.append([article.title, article.text])

    data_matrix = get_data_matrix(articles)
    write_data_matrix(data_matrix)


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
