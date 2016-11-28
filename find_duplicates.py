#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import os
import string
import pickle
from datasketch import MinHash, MinHashLSH

# Algorithm outline:
#  For each website:
#   For each artist:
#     For each song:
#      list_shingles = build_shingles(song)
#      song_minhash = build_minhash(list_shingles)
#      update_lsh(song_minhash)



def build_shingle_list(input_str, ngram_size=3, regex_prog=None):
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
    if regex_prog is not None:
        tokens = regex_prog.split(input_str)
    else:
        tokens = input_str.split()
    if ngram_size > len(tokens):
        return tokens
    return [" ".join(tokens[i:i+ngram_size]) for i in range(0, len(tokens) - ngram_size + 1)]


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
    crawler_output_files = [os.path.join('out', 'lyrics_pickle_output_vagalume_0'),
                            os.path.join('out', 'lyrics_pickle_output_letras'),
                            os.path.join('out', 'lyrics_pickle_output_cifraclub'),
                            os.path.join('out', 'lyrics_pickle_output_musica'),
                            os.path.join('out', 'lyrics_pickle_output_letrasdemusicas')]
    lyrics_by_site = []
    for out_path in crawler_output_files:
        if not os.path.exists(out_path):
            continue
        with open(out_path, 'rb') as file_in:
            lyrics = pickle.load(file_in)
            lyrics_by_site.extend(lyrics)
    print('Number of lyrics: {}'.format(len(lyrics_by_site)))

    #ascii_chars_prog = re.compile('[' + string.whitespace + string.punctuation + '\n' + ']')
    for lindex, lyrics in enumerate(lyrics_by_site):
        print('Processing song {} - {}'.format(lindex, lyrics[2]))
        if len(lyrics[3]) == 0:
            continue
        shingle_list = build_shingle_list(lyrics[3])#, regex_prog=ascii_chars_prog)
        if len(shingle_list) == 0:
            continue
        minhash = build_minhash(shingle_list)
