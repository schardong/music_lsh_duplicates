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
    for song in train_dataset:
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
    for bucket in lsh.hashtables:
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
    char_margin -- The number of characters to use as margin.

    Returns:
    True if string_a matches string_b with at most "char_margin" different
    characters. Also returns the distance between the two strings.
    """
    if not string_a or len(string_a) == 0:
        raise ValueError('Invalid input string.')
    if not string_b or len(string_b) == 0:
        raise ValueError('Invalid input string.')
    if len(string_a) < char_margin or len(string_b) < char_margin:
        raise ValueError('Input strings shorter than tolerance margin.')

    d = editdistance.eval(string_a, string_b)
    return d < char_margin, d


if __name__ == '__main__':
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
    train_dataset = []
    with open(os.path.join('out', 'train_set_pickle'), 'rb') as train_set_in:
        train_dataset = pickle.load(train_set_in)

    ## Aproximately 20% of the original set will be used as validation for the training.
    ## This ammounts to 14% of the training set.
    train_dataset, _ = build_train_validation_datasets(train_dataset, 0.86)

    ## Building the LSH index.
    lsh = MinHashLSH(threshold=LSH_THRESHOLD,
                     num_perm=NUM_PERMUTATIONS)

    start_time = timeit.default_timer()
    for song_idx, song in enumerate(train_dataset):
        ## TODO(gschardong): Remove this after testing
        if song_idx > 20000:
            break
        
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
            ## This error occurs if there is a song with the same name in the hash.
            print('Key = {}'.format(mhash_k))

    end_time = timeit.default_timer()
    lsh_build_time = end_time - start_time

    ## Getting the keys of the possible duplicates.
    possible_duplicates = get_possible_duplicates(lsh)

    ## Building the website,artist,song_name dict to easily retrieve the lyrics.
    lyrics_dict = build_lyrics_dict(train_dataset)

    ## Comparing the possible duplicates.
    num_duplicates = 0
    start_time = timeit.default_timer()
    for dups in possible_duplicates:
        for idx, key in enumerate(dups):
            site_a, artist_a, song_a = key.split('|')
            lyrics_a = lyrics_dict[site_a][artist_a][song_a]

            for next_idx in range(idx+1, len(dups)):
                site_b, artist_b, song_b = dups[next_idx].split('|')

                ## If the artists are different, we don't compare the lyrics.
                if not is_same_string(artist_a, artist_b, char_margin=1):
                    continue
                lyrics_b = lyrics_dict[site_b][artist_b][song_b]

                try:
                    if is_same_string(lyrics_a, lyrics_b, 10):
                        num_duplicates += 1
                except ValueError:
                    print('{}'.format(dups[next_idx]))

    end_time = timeit.default_timer()
    dup_check_time = end_time - start_time

    ## Writing the general benchmark results.
    file_row = ','.join([str(SHINGLE_SIZE),
                         str(lsh.b),
                         str(lsh.r),
                         str(lsh.threshold),
                         str(lsh_build_time),
                         str(dup_check_time),
                         'NA',
                         'NA'])

    if not os.path.exists(BENCHMARK_FILE):
        with open(BENCHMARK_FILE, 'a+') as file_out:
            header = ['Shingle.Size',
                      'Num.Bands',
                      'Rows.Per.Band',
                      'Threshold',
                      'Time.LSH.Build',
                      'Time.Check.Dups',
                      'Precision',
                      'Recall']
            file_out.write(','.join(header) + '\n')
            file_out.write(file_row)
    else:
        with open(BENCHMARK_FILE, 'a+') as file_out:
            file_out.write(file_row)


#if __name__ == '__main__':
#    main()



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
