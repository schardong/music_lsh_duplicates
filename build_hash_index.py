#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import pickle
import editdistance
import numpy as np
from collections import defaultdict
from multiprocessing import Process
from datasketch import MinHash, MinHashLSH

# Algorithm outline:
#  For each website:
#   For each artist:
#     For each song:
#      list_shingles = build_shingles(song)
#      song_minhash = build_minhash(list_shingles)
#      update_lsh(song_minhash)
#  For all buckets in lsh:
#   For each element in a bucket:
#    if len(element) > 1:
#     we have a possible duplicate. Parse the song's keys and retrieve the
#     lyrics from the main data structure for further comparison using edit
#     distance.

SHINGLE_SIZES = [5, 7, 10]
LSH_THRESHOLDS = [0.1, 0.3, 0.5, 0.7, 0.9]
NUM_PERMUTATIONS = [64, 128, 256]
BENCHMARK_FILE = os.path.join('out', 'output_lsh_benchmarks.csv')
WEBSITE_BENCHMARK_FILE = os.path.join('out', 'output_website_benchmarks.csv')
TRAIN_DATASET_FILE = os.path.join('out', 'train_set_pickle')

def build_shingle_list(input_str, ngram_size=3):
    """
    Given a text, this function builds it's n-grams.

    This function builds a list of n-grams given an input text and the number of
    elements per token. Optionally, the input text will be parsed in order to
    remove whitespace and punctuation characters before the processing.

    Arguments:
    input_str -- The input text as a single string.
    n -- The size of the n-gram. Must be greater than 0. If n > len(input_str)
      then input_str will be returned intact. Default value is 3.
    regex_prog -- The regex program to use in order to split the input text.
      Default value is None, meaning that the standard split function will be
      used.

    Returns:
    A list of n-grams built from the input dataset.
    """
    if input_str is None or len(input_str) == 0:
        raise ValueError('Input text must not be empty.')

    tokens = input_str.split()
    if ngram_size > len(tokens):
        return ' '.join(tokens)

    return [' '.join(tokens[i:i+ngram_size]) for i in range(0, len(tokens) - ngram_size + 1)]


def build_minhash(shingle_list, num_perm=128):
    """
    Builds a MinHash object given a list of shingles.

    Arguments:
    shingle_list -- A list containing the n-grams(shingles).
    num_perm -- The number of permutation functions to pass to the MinHash.

    Returns:
    A datasketch.MinHash object built from the shingles with num_perm
    permutations.
    """
    if shingle_list is None or len(shingle_list) == 0:
        raise ValueError('Invalid list of shingles. Must not be empty.')
    if num_perm <= 0:
        raise ValueError('Invalid number of permutations. Must be larger than 0.')

    mhash = MinHash(num_perm=num_perm)
    for shingle in shingle_list:
        try:
            mhash.update(shingle.encode('utf8'))
        except UnicodeEncodeError:
            continue
    return mhash

def build_train_validation_datasets(song_list, train_proportion=0.5):
    """
    Given a list of songs and a proportion of training elements, this functions
    selects uniformly at random which songs will compose the training and train
    validation datasets.

    Arguments:
    song_list -- The list of songs to be split.
    train_proportion -- The proportion of elements to be assigned to the training
    set. The remaining 1-train_proportion elements will be assigned to the
    validation set. Default value is 0.5, half of the elements will be assigned
    to each set.

    Returns:
    Two lists. The first list contains the new training set and the second list
    contains the validation set.
    """
    if not song_list or len(song_list) == 0:
        raise ValueError('Invalid list of songs.')
    if train_proportion >= 1 or train_proportion <= 0:
        raise ValueError('Invalid train set proportion. Value must be in range (0, 1)')

    choice = np.random.sample(len(song_list))
    train_set = [s for i, s in enumerate(song_list) if choice[i] <= train_proportion]
    validation_set = [s for i, s in enumerate(song_list) if choice[i] > train_proportion]
    return train_set, validation_set


def build_lyrics_dict(lyrics_list):
    """
    Given a list of tuples, this function builds a triple nested dictionary
    indexed by the website, artist and song-name, with each lyric as the mapped
    data.

    Arguments:
    lyrics_list -- List of tuples in the form
    (website, artist-name, song-name, song-lyrics).

    Returns:
    A dictionary indexed by the website, artist and song name. The songs will be
    stored under each song name dict.
    """
    if not lyrics_list or len(lyrics_list) == 0:
        raise ValueError('Invalid lyrics list.')

    lyrics_dict = {}
    for song in lyrics_list:
        website = song[0]
        artist = song[1]
        song_name = song[2]

        if website not in lyrics_dict:
            lyrics_dict[website] = {}
        if artist not in lyrics_dict[website]:
            lyrics_dict[website][artist] = defaultdict(dict)

        lyrics_dict[website][artist][song_name] = song[3]

    return lyrics_dict


def get_possible_duplicates(lsh_index):
    """
    Given an LSH index, this function iterates through the buckets of the index
    and retrieves a list of possible duplicates.

    Arguments:
    lsh_index -- The LSH index structure.

    Returns:
    A list of lists, where each sublist contains the keys of the possible
    duplicates stored in the LSH hash.
    """
    if not lsh_index:
        raise ValueError('Invalid LSH index.')

    possible_duplicates = []
    for bucket in lsh_index.hashtables:
        for elem in bucket.values():
            if len(elem) > 1:
                possible_duplicates.append(elem)

    return possible_duplicates


def is_same_string(string_a, string_b, char_margin=5):
    """
    Given two strings, this function returns True if they are identical within
    a certain tolerance. This functions uses the edit distance to compare the
    inputs.

    Arguments:
    string_a -- The first string
    string_b -- The second string
    char_margin -- The number or percentage of characters to use as margin. If
    this parameter is float, it will be interpreted as a percentage of characters
    of the smallest string. If is of type int, then it will be interpreted as the
    number of characters of tolerance to declare that the two strings are the same.

    Returns:
    True if string_a matches string_b with at most "char_margin" different
    characters. Also returns the distance between the two strings.
    """
    if not string_a or len(string_a) == 0:
        raise ValueError('Invalid input string.')
    if not string_b or len(string_b) == 0:
        raise ValueError('Invalid input string.')
    if isinstance(char_margin, int):
        if len(string_a) < char_margin or len(string_b) < char_margin:
            raise ValueError('Input strings shorter than tolerance margin.')

    d = editdistance.eval(string_a, string_b)

    if isinstance(char_margin, float):
        shortest_str_len = len(string_a) if len(string_a) < len(string_b) else len(string_b)
        return (False if float(d) / float(shortest_str_len) > char_margin else True), d
    else:
        return d < char_margin, d


def run(shingle_size, num_permutations, lsh_threshold):
    """
    Main function. This function loads the training dataset, splits it into
    training and validation datasets and runs the LSH algorithm with the given
    parameters on the tranining dataset. Later, the parameters are tested using
    the validation dataset.

    After the parameters are adjusted, the test dataset is loaded and the same
    algorithm is applied. The algorithm's performance with both sets if compared
    for inconsistensies.
    """
    ## Reading the traning dataset.
    train_dataset = {}
    with open(TRAIN_DATASET_FILE, 'rb') as train_set_in:
        train_dataset = pickle.load(train_set_in)

    ## Building the LSH index.
    lsh = MinHashLSH(threshold=lsh_threshold,
                     num_perm=num_permutations)

    for key, lyrics in train_dataset.items():
        if len(lyrics) == 0:
            continue

        shingle_list = build_shingle_list(lyrics, ngram_size=shingle_size)
        if len(shingle_list) == 0:
            continue

        mhash = build_minhash(shingle_list, num_perm=num_permutations)
        try:
            lsh.insert(key, mhash)
        except ValueError:
            ## This error occurs if there is a song with the same name in the hash.
            print('Repeated Key = {}'.format(key))

    ## Getting the keys of the possible duplicates.
    possible_duplicates = get_possible_duplicates(lsh)

    possible_duplicates_comb = []
    for dups in possible_duplicates:
        for idx, key in enumerate(dups):
            for next_idx in range(idx+1, len(dups)):
                curr_comb = [key, dups[next_idx]]
                possible_duplicates_comb.append(curr_comb)

    duplicates_filename = 'b-{}_r-{}_shinglesize-{}_numperp-{}_thresh-{}'.format(lsh.b, lsh.r, shingle_size, num_permutations, lsh_threshold)
    pickle.dump(possible_duplicates_comb, open(duplicates_filename, 'wb'))


if __name__ == '__main__':
    process_pool = []

    for curr_shingle_size in SHINGLE_SIZES:
        for curr_num_perm in NUM_PERMUTATIONS:
            for curr_threshold in LSH_THRESHOLDS:
                p = Process(target=run, args=(curr_shingle_size, curr_num_perm, curr_threshold))
                process_pool.append(p)
                p.start()

    for p in process_pool:
        p.join()

