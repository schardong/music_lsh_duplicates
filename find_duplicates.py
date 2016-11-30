#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import pickle
import timeit
import editdistance
import numpy as np
from collections import defaultdict
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

SHINGLE_SIZE = 5
LSH_THRESHOLD = 0.5
NUM_PERMUTATIONS = 128
BENCHMARK_FILE = os.path.join('out', 'output_lsh_benchmarks.csv')
WEBSITE_BENCHMARK_FILE = os.path.join('out', 'output_website_benchmarks.csv')

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


def main():
    """
    Main function. This function loads the training dataset, splits it into
    training and validation datasets and runs the LSH algorithm with the given
    parameters on the tranining dataset. Later, the parameters are tested using
    the validation dataset.

    After the parameters are adjusted, the test dataset is loaded and the same
    algorithm is applied. The algorithm's performance with both sets if compared
    for inconsistensies.
    """
    train_set_file = os.path.join('out', 'train_set_pickle')

    ## Reading the traning dataset.
    train_dataset = []
    with open(train_set_file, 'rb') as train_set_in:
        train_dataset = pickle.load(train_set_in)

    ## Aproximately 20% of the original set will be used as validation for the training.
    ## This ammounts to 14% of the training set.
    train_dataset, _ = build_train_validation_datasets(train_dataset, 0.86)

    ## Building the LSH index.
    lsh = MinHashLSH(threshold=LSH_THRESHOLD,
                     num_perm=NUM_PERMUTATIONS)
    start_time = timeit.default_timer()
    for song in train_dataset:
        lyrics = song[3]
        if len(lyrics) == 0:
            continue
        shingle_list = build_shingle_list(lyrics, ngram_size=SHINGLE_SIZE)
        if len(shingle_list) == 0:
            continue

        mhash = build_minhash(shingle_list, num_perm=NUM_PERMUTATIONS)
        mhash_k = song[0] + '|' + song[1] + '|' + song[2]
        try:
            lsh.insert(mhash_k, mhash)
        except ValueError:
            print('Key = {}'.format(mhash_k))

    end_time = timeit.default_timer()

    ## Getting the keys of the possible duplicates.
    possible_duplicates = []
    for bucket in lsh.hashtables:
        for elem in bucket.values():
            if len(elem) > 1:
                possible_duplicates.append(elem)

    ## Building the website,artist,song_name dict to easily retrieve the lyrics.
    lyrics_dict = {}
    for song in train_dataset:
        website = song[0]
        artist = song[1]
        song_name = song[2]

        if website not in lyrics_dict:
            lyrics_dict[website] = {}
        if artist not in lyrics_dict[website]:
            lyrics_dict[website][artist] = defaultdict(dict)

        lyrics_dict[website][artist][song_name] = song[3]

    #for dups in possible_duplicates:
    #    must_compare_keys = []
    #    for key in dups:
    #        website, artist, song_name = key.split('|')
    #        must_compare_keys.append([website, artist, song_name])


    ## Writing the general benchmark results.
    file_row = ','.join([str(SHINGLE_SIZE),
                         str(lsh.b),
                         str(lsh.r),
                         str(lsh.threshold),
                         str(end_time - start_time),
                         'NA',
                         'NA',
                         'NA'])

    if not os.path.exists(BENCHMARK_FILE):
        with open(BENCHMARK_FILE, 'a+') as file_out:
            header = ['Shingle.Size',
                      'Num.Bands',
                      'Rows.Per.Band',
                      'Threshold',
                      'Time.LSH.Build',
                      'Time.Dedup',
                      'Precision',
                      'Recall']
            file_out.write(','.join(header) + '\n')
            file_out.write(file_row)
    else:
        with open(BENCHMARK_FILE, 'a+') as file_out:
            file_out.write(file_row)


if __name__ == '__main__':
    main()
#-------------------------------------------------------------------------------
def old_content():
    ## Reading the datasets if needed.
    if lyrics_dict is None:
        print('Reading the datasets.')
        lyrics_dict = {}
        for out_path in crawler_output_files:
            ## For each website, we load the list of song tuples
            ## (website, artist-name, song-name, song-lyrics), normalize the artist
            ## name and both song name and lyrics, and then we add the resulting
            ## lyrics to a dictionary indexed by the song name, which is in a
            ## dictionary indexed by artist, which is in a dictionary indexed by the
            ## website.
            print('Trying to read {}'.format(out_path))
            if not os.path.exists(out_path):
                continue
            with open(out_path, 'rb') as file_in:
                lyrics_tuples_list = pickle.load(file_in)
                website_dict = defaultdict(dict)
                for song in lyrics_tuples_list:
                    ## If the any song field lyrics is empty, we jump to the next
                    ## iteration.
                    if all([len(s) for s in song]) is False:
                        continue
                    artist = normalize_string(song[1])
                    song_name = normalize_string(song[2])
                    lyrics = normalize_string(song[3])
                    website_dict[artist][song_name] = lyrics


                    lyrics_dict[lyrics_tuples_list[0][0]] = website_dict

    print('Number of websites: {}'.format(len(lyrics_dict)))
    print('Number of song lyrics in database: {}'.format(sum([len(artist)
                                                              for website in lyrics_dict.values()
                                                              for artist in website.values()])))

    ## Building the MinHashLSH index.
    mhash_lsh = MinHashLSH(threshold=0.1)
    website_time_dict = {}
    start_time = timeit.default_timer()
    for website_name, website in lyrics_dict.items():
        print('Processing website {}. Number of artists: {}'.format(website_name, len(website.keys())))
        website_start_time = timeit.default_timer()
        for artist_name, artist in website.items():
            for lyric_name, lyric in artist.items():
                if len(lyric) == 0:
                    continue
                shingle_list = build_shingle_list(lyric, ngram_size = SHINGLE_SIZE)
                if len(shingle_list) == 0:
                    continue
                mhash = build_minhash(shingle_list)
                mhash_key = website_name + '|' + artist_name + '|' + lyric_name
                mhash_lsh.insert(mhash_key, mhash)
        website_end_time = timeit.default_timer();
        website_time_dict[website_name] = website_end_time - website_start_time
    end_time = timeit.default_timer()
