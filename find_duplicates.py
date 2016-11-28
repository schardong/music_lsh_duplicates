#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import os
import string
import pickle
import editdistance
from datasketch import MinHash, MinHashLSH

# Algorithm outline:
#  For each website:
#   For each artist:
#     For each song:
#      list_shingles = build_shingles(song)
#      song_minhash = build_minhash(list_shingles)
#      update_lsh(song_minhash)
#  For all buckets in lsh:
#   if len(bucket) > 1:
#    songs = get_songs_from_bucket
#    songs.class = 'duplicates'

#Tasks:
# Artist name normalization function (replace special characters by spaces. Replace quotes by nothing).
# Pre-process the songs lyrics to remove special characters before building the shingles.


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
        mhash.update(shingle.encode('utf8'))
    return mhash


def normalize_string(input_text):
    """
    Given an input string, this function removes all special characters and
    returns a clean version of the original text. Any quote characters are
    replaced by an empty string.

    Arguments:
    input_text -- The input string

    Returns:
    A cleaned-up version of the input text.
    """
    if input_text is None or len(input_text) == 0:
        raise ValueError('Invalid list of song lyrics.')

    tmp_text = input_text.replace('\'', '').lower()
    normalized_text = re.sub('[' + string.punctuation + string.whitespace + ']',
                             ' ',
                             tmp_text)
    normalized_text = ' '.join(normalized_text.split())
    return normalized_text


if __name__ == '__main__':
    crawler_output_files = [os.path.join('out', 'lyrics_pickle_output_vagalume_0'),
                            os.path.join('out', 'lyrics_pickle_output_letras'),
                            os.path.join('out', 'lyrics_pickle_output_musica'),
                            os.path.join('out', 'lyrics_pickle_output_letrasdemusicas')]

    ## Reading the datasets.
    lyrics_by_site = []
    for out_path in crawler_output_files:
        ## For each website, we load the list of song tuples
        ## (website, artist-name, song-name, song-lyrics), normalize the artist
        ## name and song lyrics, and then we add the resulting songs to the
        ## dataset again.
        if not os.path.exists(out_path):
            continue
        with open(out_path, 'rb') as file_in:
            lyrics_tuples_list = pickle.load(file_in)
            for song_idx, song in enumerate(lyrics_tuples_list):
                if len(song[3]) == 0:
                    continue
                song = list(song)
                song[1] = normalize_string(song[1])
                song[3] = normalize_string(song[3])
                lyrics_tuples_list[song_idx] = tuple(song)

            lyrics_by_site.extend(lyrics_tuples_list)

    print('Number of song lyrics: {}'.format(len(lyrics_by_site)))

    mhash_lsh = MinHashLSH(threshold=0.5)
    for lyric_idx, lyrics in enumerate(lyrics_by_site):
        ## TODO(gschardong): Remove this after thorough testing.
        if lyric_idx > 2000:
            break
        print('Processed {}/{} songs.'.format(lyric_idx, len(lyrics_by_site)))
        if len(lyrics[3]) == 0:
            continue
        shingle_list = build_shingle_list(lyrics[3])
        if len(shingle_list) == 0:
            continue
        mhash = build_minhash(shingle_list)
        key = lyrics[0] + '|' + lyrics[1] + '|' + lyrics[2]
        mhash_lsh.insert(key, mhash)

    possible_duplicates = []
    for bucket in mhash_lsh.hashtables:
        for elem in bucket.values():
            if len(elem) > 1:
                possible_duplicates.append(elem)
