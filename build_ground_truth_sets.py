#!/usr/bin/python3
# -*- coding: utf-8 -*-


import sys
import pickle
import itertools
from multiprocessing import Pool
from find_duplicates import is_same_string

NUM_PROCESSES = 4

def usage(scriptname):
    print("Usage: %s pickle_processed_dict_filename pickle_count_true_and_matches_filename" % scriptname)
    exit(1)


def is_same_string_from_vagalume(website1_name, website2_name, string1, string2):
    vagalume_website_name = 'vagalume.com.br'

    if website1_name != vagalume_website_name or website2_name != vagalume_website_name:
        return False

    if string1 == string2 or string1 == string2 + " traducao" or string2 == string1 + " traducao":
        return True

    return False


def check_match(key1, key2):
# 'key[12]' is a string with the following:
# 'website_name|artist_name|lyrics_name'

    key1_split = key1.split('|')
    key2_split = key2.split('|')

    if not len(key1_split) == 3:
        print('Original key:{}\nSplit key:{}'.format(key1, key1_split))
        assert False
    assert len(key2_split) == 3

    try:
        # Checks whether artist name is the same
        is_same_artist_name, _ = is_same_string(key1_split[1], key2_split[1], 1)
        if not is_same_artist_name:
            return False

        is_same_lyrics_from_vagalume = is_same_string_from_vagalume(key1_split[0],
                                                                    key2_split[0],
                                                                    key1_split[2],
                                                                    key2_split[2])

        # Checks whether lyrics name is the same
        is_same_lyrics_name, _ = is_same_string(key1_split[2], key2_split[2], 1)
        if not is_same_lyrics_name and not is_same_lyrics_from_vagalume:
            return False

    except Exception:
        print("Error comparing '%s' and '%s'. Returning False for matching." % (key1, key2))
        return False

    return True


def generate_matches(lyrics_tuple_list):
    '''
    Given a list of tuples in the form ('website|artist|songname', 'lyrics'),
    this function searches through them and returns a dictionary containing the
    matches and a counter of how many matches occured.

    Arguments:
    lyrics_tuple_list -- The list of tuples in the form:
    [('website|artist|songname', 'lyrics'), ...)

    Returns:
    The number of matches and a set containing tuples of songs that matched, e.g.
    set((key1, key2), (key2, key1), (key4, key3), (key3, key4), ...)
    '''
    if not lyrics_tuple_list or len(lyrics_tuple_list) == 0:
        raise ValueError('Invalid lyrics dictionary')

    match_count = 0
    match_set = set()

    for key1, key2 in itertools.combinations(lyrics_tuple_list, 2):
        if (key1, key2) not in match_set:
            is_match = check_match(key1, key2)
            if is_match:
                match_set.add((key1, key2))
                match_set.add((key2, key1))
                match_count += 1

    return match_count, match_set


def main():
    if len(sys.argv) < 3:
        usage(sys.argv[0])

    pickle_processed_dict_filename = sys.argv[1]
    pickle_ground_truth_output = sys.argv[2]

    count_true = 0
    matches = set()
    with open(pickle_processed_dict_filename, 'rb') as file_input:
        print('RUNNING!')
        dict_lyrics = pickle.load(file_input)

        chunk_size = int(len(dict_lyrics) / NUM_PROCESSES)
        items = list(dict_lyrics.keys())
        dict_chunks = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
        print('Split the data into {} chunks of {} elements.'.format(NUM_PROCESSES, chunk_size))

        pool = Pool(processes=NUM_PROCESSES)
        results = pool.map(generate_matches, dict_chunks)
        print('DONE!')

        count_true = sum(r[0] for r in results)
        matches = set.union(*(s[1] for s in results))

        print('Number of matches found = {}'.format(count_true))

    with open(pickle_ground_truth_output, "wb") as file_out:
        pickle.dump((count_true, matches), file_out)


if __name__ == "__main__":
    main()
