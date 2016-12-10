#!/usr/bin/python3
# -*- coding: utf-8 -*-


import sys
import pickle
from multiprocessing import Pool
from find_duplicates import is_same_string


NUM_PROCS = 32

def usage(scriptname):
    print("Usage: %s pickle_processed_dict_filename pickle_count_true_and_matches_filename"
          % scriptname)
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

    assert len(key1_split) == 3
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

    except:
        print("Error comparing '%s' and '%s'. Returning False for matching." % (key1, key2))
        return False

    return True

def divide_work(l, num_pieces):
    size_of_each_chunk = float(len(l))/float(num_pieces)
    size_done = 0.0
    last_done = 0
    list_of_chunks = []
    for _ in range(num_pieces):
        size_done += size_of_each_chunk
        chunk = l[last_done:int(size_done)]
        list_of_chunks.append(chunk)
        last_done = int(size_done)
    if last_done != len(l):
        list_of_chunks[-1].append(l[-1])
    return list_of_chunks


def generate_count_true_and_matches(pickle_processed_dict_filename):
    def save_if_match(list_of_pairs_of_dict_lyrics_keys):
        matches_set = set()
        for dict_lyrics_key1, dict_lyrics_key2 in list_of_pairs_of_dict_lyrics_keys:
            if (dict_lyrics_key1, dict_lyrics_key2) not in matches_set:
                is_a_match = check_match(dict_lyrics_key1,
                                         dict_lyrics_key2)
                if is_a_match:
                    matches_set.add((dict_lyrics_key1, dict_lyrics_key2))
                    matches_set.add((dict_lyrics_key2, dict_lyrics_key1))
                    count_true += 1
        return count_true, matches_set


    count_true_total = 0
    matches_set_total = set()

    with open(pickle_processed_dict_filename, "rb") as pickle_processed_dict_file:
        dict_lyrics = pickle.load(pickle_processed_dict_file)

        list_of_comparisons = []
        for dict_lyrics_key1 in dict_lyrics:
            for dict_lyrics_key2 in dict_lyrics:
                if dict_lyrics_key1 >= dict_lyrics_key2:
                    # By including > we only compare each pair once.
                    continue
                list_of_comparisons.append((dict_lyrics_key1, dict_lyrics_key2))

        jobs = divide_work(list_of_comparisons, NUM_PROCS)
        pool_results = []
        with Pool(processes=NUM_PROCS) as p:
            for job in jobs:
                pool_results.append(p.apply_async(save_if_match, job))

        for result in pool_results:
            curr_count, curr_matches = result.get()
            count_true_total += curr_count
            matches_set_total.union(curr_matches)

    return count_true_total, matches_set_total


if __name__ == "__main__":
    if len(sys.argv) < 3:
        usage(sys.argv[0])

    pickle_processed_dict_filename = sys.argv[1]
    pickle_count_true_and_matches_filename = sys.argv[2]

    count_true, matches = generate_count_true_and_matches(pickle_processed_dict_filename)

    with open(pickle_count_true_and_matches_filename, "wb") as pickle_count_true_and_matches_file:
        pickle.dump((count_true, matches), pickle_count_true_and_matches_file)
