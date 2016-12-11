#!/usr/bin/python3
# -*- coding: utf-8 -*-


import sys
import pickle

def usage(scriptname):
    print("Usage: %s pickle_processed_dict_filename pickle_count_true_and_matches_filename"
          % scriptname)
    exit(1)


def generate_count_true_and_matches(pickle_processed_dict_filename):
    def get_original_string(key):
        return '|'.join((key[1], key[0]))

    count_true = 0
    matches = set()

    with open(pickle_processed_dict_filename, "rb") as pickle_processed_dict_file:
        dict_lyrics = pickle.load(pickle_processed_dict_file)

        list_lyrics = []
        for key in dict_lyrics:
            key_list = key.split("|")
            list_lyrics.append(('|'.join(key_list[1:]), key_list[0]))
        list_lyrics.sort(key=lambda x: x[0])

        for index, elem in enumerate(list_lyrics):
            if index + 1 == len(list_lyrics):
                break
            next_comparison_index = index + 1
            while elem[0] == list_lyrics[next_comparison_index][0]:
                pair = (get_original_string(elem),
                        get_original_string(list_lyrics[next_comparison_index]))
                matches.add(pair)
                matches.add((pair[1], pair[0]))
                count_true += 1
                next_comparison_index += 1

    return count_true, matches


if __name__ == "__main__":
    if len(sys.argv) < 3:
        usage(sys.argv[0])

    pickle_processed_dict_filename = sys.argv[1]
    pickle_count_true_and_matches_filename = sys.argv[2]

    count_true, matches = generate_count_true_and_matches(pickle_processed_dict_filename)

    with open(pickle_count_true_and_matches_filename, "wb") as pickle_count_true_and_matches_file:
        pickle.dump((count_true, matches), pickle_count_true_and_matches_file)
