#!/usr/bin/python3
# -*- coding: utf-8 -*-

#import pickle
import re
import string
from datasketch import MinHash, MinHashLSH

# Algorithm outline:
#  For each website:
#   For each artist:
#     For each song:
#      list_shingles = build_shingles(song)
#      song_minhash = build_minhash(list_shingles)
#      update_lsh(song_minhash)

def build_shingle_list(input_str, n=3, regex_prog = None):
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
    tokens = []
    if input_str is None or len(input_str) == 0:
        raise ValueError('Input text must not be empty.')
    if n > len(input_str):
        return input_str
    if regex_prog is not None:
        tokens = regex_prog.split(input_str)
    else:
        tokens = input_str.split()
    return [" ".join(tokens[i:i+n]) for i in range(0, len(tokens) - n + 1)]


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
        mhash.update(shingle.encode('utf8'))
    return mhash

def build_minhash_lsh(minhash_list):
    pass

if __name__ == '__main__':
    str1 = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. In ut vehicula lacus, quis eleifend nulla. Maecenas at nulla dictum, accumsan dolor in, euismod felis. Morbi rhoncus a ligula nec venenatis.'
    str2 = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. In ut vehicula lacus, quis eleifend nulla. Maecenas at nulla dictum, accumsan dolor in, euismod felis. Integer sollicitudin arcu sit amet ullamcorper iaculis. Nulla.'

    sd1, sd2 = build_shingle_list(str1), build_shingle_list(str2)
    mhash1, mhash2 = build_minhash(sd1), build_minhash(sd2)
    print('Shingles = {}\nEstimated cardinality = {}\nByte size = {} bytes\n\n'.format(sd1, mhash1.count(), mhash1.bytesize()))
    print('Shingles = {}\nEstimated cardinality = {}\nByte size = {} bytes\n\n'.format(sd2, mhash2.count(), mhash2.bytesize()))
    print('Estimated Jaccard similarity = {}'.format(mhash1.jaccard(mhash2)))

    set1 = set(sd1)
    set2 = set(sd2)

    jc = float(len(set1.intersection(set2)))/float(len(set1.union(set2)))
    print('Real Jaccard similarity = {}'.format(jc))
