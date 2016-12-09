#!/usr/bin/python3
# -*- coding: utf-8 -*-


import sys
import pickle
import string
from find_duplicates import is_same_string


def usage(scriptname):
    print("Usage: %s pickle_processed_dict_filename pickle_count_true_and_matches_filename" % scriptname)
    exit(1)


def check_match(key1, key2, lyrics1, lyrics2):
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
        
        # Checks whether lyrics name is the same
        is_same_lyrics_name, _ = is_same_string(key1_split[2], key2_split[2], 1)
        if not is_same_lyrics_name:
            return False
        
        # Checks whether one of the lyrics is empty
        if lyrics1 == "" or lyrics2 == "":
            return False
        
        # Checks whether lyrics is the same
        is_same_lyrics, _ = is_same_string(lyrics1, lyrics2, 0.1)
        if not is_same_lyrics:
            return False
    except Exception as e:
        print("Error comparing '%s' and '%s'. Returning False for matching." % (key1, key2))
        return False
    
    return True


def generate_count_true_and_matches(pickle_processed_dict_filename): 
    count_true = 0
    matches = {}
    
    with open(pickle_processed_dict_filename, "rb") as pickle_processed_dict_file:
        dict_lyrics = pickle.load(pickle_processed_dict_file)
        
        for dict_lyrics_key1 in dict_lyrics:
            for dict_lyrics_key2 in dict_lyrics:
                if dict_lyrics_key1 == dict_lyrics_key2:
                    continue
                
                if (dict_lyrics_key1, dict_lyrics_key2) not in matches:
                    is_a_match = check_match(dict_lyrics_key1, dict_lyrics_key2, \
                                             dict_lyrics[dict_lyrics_key1], dict_lyrics[dict_lyrics_key2])
                    
                    if is_a_match:
                        matches[(dict_lyrics_key1, dict_lyrics_key2)] = True
                        matches[(dict_lyrics_key2, dict_lyrics_key1)] = True
                        count_true += 1
                    else:
                        matches[(dict_lyrics_key1, dict_lyrics_key2)] = False
                        matches[(dict_lyrics_key2, dict_lyrics_key1)] = False
    
    return count_true, matches


if __name__ == "__main__":
    if (len(sys.argv) < 3):
        usage(sys.argv[0])
    
    pickle_processed_dict_filename = sys.argv[1]
    pickle_count_true_and_matches_filename = sys.argv[2]
    
    count_true, matches = generate_count_true_and_matches(pickle_processed_dict_filename)
    
    with open(pickle_count_true_and_matches_filename, "wb") as pickle_count_true_and_matches_file:
        pickle.dump((count_true, matches), pickle_count_true_and_matches_file)
