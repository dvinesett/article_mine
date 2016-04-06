#! /usr/bin/env python3

import collections
import copy
import functools
import itertools
import newspaper
import scipy.spatial.distance
import random
import re
import sys


def main(argv=None):
    urls = []
    if len(argv) < 2:
        raise FileNotFoundError('Please input a file with urls as the first argument')
    with open(argv[1]) as f:
        for line in f.readlines():
            line = line.rstrip("\n")
            # url will be the last "column" in line
            # this leaves room for user-created tags
            if line != '':
                line = line.split()[-1]
                urls.append(line)
    articles = []
    print("downloading")
    for url in urls:
        print(".", url)
        article = newspaper.Article(url, language='en')
        article.download()
        article.parse()
        articles.append([article.title, article.text])
    print("done downloading")
    data_matrix = get_data_matrix(articles)
    # write_matrix(data_matrix)
    # title_combinations = article_combinations(articles)
    # euclidean = get_similarity(title_combinations, data_matrix, euclidean_similarity)
    # cosine = get_similarity(title_combinations, data_matrix, cosine_similarity)
    # jaccard = get_similarity(title_combinations, data_matrix, jaccard_similarity)
    # similarity_matrix = get_similarity_matrix(title_combinations,
    #                                           euclidean,
    #                                           cosine,
    #                                           jaccard)
    # write_matrix(similarity_matrix)

    print("start euclidean")
    euclidean_clusters = k_means(data_matrix, 5, euclidean_similarity)
    print("euclidean", [i[1] for i in euclidean_clusters])
    print("-------\nstart cosine")
    cosine_clusters = k_means(data_matrix, 5, cosine_similarity)
    print("cosine", [i[1] for i in cosine_clusters])
    print("-------\nstart jaccard")
    jaccard_clusters = k_means(data_matrix, 5, jaccard_similarity)
    print("jaccard", [i[1] for i in jaccard_clusters])

    euclidean_sse = sse(data_matrix, euclidean_clusters)
    cosine_sse = sse(data_matrix, cosine_clusters)
    jaccard_sse = sse(data_matrix, jaccard_clusters)

    print(euclidean_sse)
    print(cosine_sse)
    print(jaccard_sse)


def get_data_matrix(articles):
    """

    :param articles: dictionary of articles with key as article title and value as the text
    :return: data matrix in the format
    """
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
        frequencies = data_matrix[row_num][1]
        if distance_function.__name__ == 'jaccard':
            frequencies = [bool(i) for i in frequencies]
        data_matrix_dict[title] = frequencies

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


def extrapolate_data_matrix(data_matrix):
    """
    returns list of words and list of articles
    """
    return data_matrix[0][1], data_matrix[1:]


def k_means(data_matrix, clusters: int, similarity_function):
    words, article_data = extrapolate_data_matrix(data_matrix)

    # get word counts to have a good idea where to place random clusters
    word_counts = [[] for _ in range(len(words))]
    for article in article_data:
        for i in range(len(words)):
            word_counts[i].append(article[1][i])
            # word_counts.extend(article[1])
    cluster_locations = [[random.choice(word_counts[i]) for i in range(len(words))] for _ in range(clusters)]

    same = False
    clustered_articles = None
    old_clustered_articles = [[] for _ in range(clusters)]
    while not same:
        # clear article cluster association data
        clustered_articles = [[] for _ in range(clusters)]

        for i in range(len(article_data)):
            # calculate distance between each article and cluster then assign lowest distance to cluster
            min_cluster = sys.maxsize, 0
            for j in range(clusters):
                similarity = similarity_function(article_data[i][1], cluster_locations[j])
                # print("article", i, "cluster", j, similarity, "<", min_cluster[1], "=", similarity < min_cluster[1])
                if similarity > min_cluster[1]:
                    min_cluster = j, similarity
            clustered_articles[min_cluster[0]].append(i)

        # recalculate cluster locations
        for i in range(clusters):
            # if cluster has articles associated with it, recalculate as mean of clustered articles
            if clustered_articles[i]:
                cluster_locations[-i] = _mean([article_data[j][1] for j in clustered_articles[i]])
                # print("num clustered", clustered_articles[i])
            else:
                cluster_locations[i] = [0 for _ in range(len(words))]
        # print(clustered_articles)
        # print([sum(i) for i in cluster_locations])
        # clusters_locations wrapped in sets
        if _unordered_equals(old_clustered_articles, clustered_articles):
            same = True
        old_clustered_articles = copy.deepcopy(clustered_articles)

    # transpose elements in (cluster_locations, clustered_articles) before returning
    return [list(col) for col in zip(*(cluster_locations, clustered_articles))]


def sse(data_matrix, clusters):
    _, article_data = extrapolate_data_matrix(data_matrix)
    total = 0
    for cluster_location, articles in clusters:
        total += sum(euclidean_similarity(cluster_location, article_data[article][1])**2 for article in articles)
    return total


def euclidean_similarity(u, v):
    return (1 + scipy.spatial.distance.euclidean(u, v))**-1


def cosine_similarity(u, v):
    return scipy.spatial.distance.cosine(u, v)


def jaccard_similarity(u, v):
    return scipy.spatial.distance.jaccard(u, v)


def _mean(vector):
    """
    returns mean of vectors. e.g.
    data = [[1,2,3,],
            [4,5,6],
            [7,8,16]]
    _mean(data)
    [4.0, 5.0, 8.333333333333334]
    """
    return [sum(col)/len(col) for col in zip(*vector)]


def _unordered_equals(u, v):
    """
    basically works like "set(u) == set(v)" should if lists were hashable
    @:param u - 2d vector
    @:param v - 2d vector
    @:returns bool
    """
    us = set(tuple(j for j in i) for i in u)
    vs = set(tuple(j for j in i) for i in v)
    return us == vs



if __name__ == "__main__":
    main(sys.argv)
