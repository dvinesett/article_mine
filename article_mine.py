#! /usr/bin/env python3

import collections
import functools
import itertools
import newspaper
import scipy.spatial.distance
import re
import sys


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
        article = newspaper.Article(url, language='en')
        article.download()
        article.parse()
        articles.append([article.title, article.text])

    data_matrix = get_data_matrix(articles)
    # write_matrix(data_matrix)
    title_combinations = article_combinations(articles)
    euclidean_distances = get_similarity(title_combinations, data_matrix, scipy.spatial.distance.euclidean)
    cosine_distances = get_similarity(title_combinations, data_matrix, scipy.spatial.distance.cosine)
    jaccard_distances = get_similarity(title_combinations, data_matrix, scipy.spatial.distance.jaccard)
    similarity_matrix = get_similarity_matrix(title_combinations,
                                              euclidean_distances,
                                              cosine_distances,
                                              jaccard_distances)
    write_matrix(similarity_matrix)


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
    data_matrix = [('ARTICLES', all_words)]
    for article in articles:
        # row looks like (article_name, (count, count, count, ... ))
        row = (article[0], tuple(article_counters[article[0]][word] for word in all_words))
        data_matrix.append(row)
    return data_matrix


def write_matrix(matrix):

    for row in matrix:
        counts = ','.join((str(count) for count in row[1]))
        print(row[0] + ',' + counts)


def article_combinations(articles):
    article_titles = [article[0] for article in articles]
    return tuple(i for i in itertools.combinations(article_titles, 2))


def get_similarity(title_combinations, data_matrix, distance_function):
    # I have to unpack the data matrix and repack it into a dictionary. this could be way more efficient
    data_matrix_dict = {}
    # skip header row
    for row_num in range(1, len(data_matrix)):
        title = data_matrix[row_num][0]
        article_body = data_matrix[row_num][1]
        data_matrix_dict[title] = article_body

    distances = [distance_function.__name__]
    for title_pair in title_combinations:
        distances.append(distance_function(data_matrix_dict[title_pair[0]],
                                           data_matrix_dict[title_pair[1]]))
    return distances


def get_similarity_matrix(title_combinations, *distances):
    distance_names = tuple(distance[0] for distance in distances)
    matrix = [('PAIRS', distance_names)]
    for i in range(len(title_combinations)):
        pair_text = '|'.join(title_combinations[i])
        row = pair_text, tuple(distance[i + 1] for distance in distances)
        matrix.append(row)
    return matrix

if __name__ == "__main__":
    main(sys.argv)
