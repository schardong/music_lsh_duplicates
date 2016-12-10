#!/usr/bin/python3
# -*- coding: utf-8 -*-


import sys
import pickle
import itertools
from multiprocessing import Pool
from find_duplicates import is_same_string

NUM_PROCESSES=4

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
        
        is_same_lyrics_from_vagalume = is_same_string_from_vagalume(key1_split[0], key2_split[0], key1_split[2], key2_split[2])
        
        # Checks whether lyrics name is the same
        is_same_lyrics_name, _ = is_same_string(key1_split[2], key2_split[2], 1)
        if not is_same_lyrics_name and not is_same_lyrics_from_vagalume:
            return False

    except Exception as e:
        print("Error comparing '%s' and '%s'. Returning False for matching." % (key1, key2))
        return False
    
    return True


def generate_count_true_and_matches(pickle_processed_dict_filename): 
    count_true = 0
    matches = set()
    
    with open(pickle_processed_dict_filename, "rb") as pickle_processed_dict_file:
        dict_lyrics = pickle.load(pickle_processed_dict_file)
        
        for key1, key2 in itertools.combinations(dict_lyrics.keys(), 2):
            if key1 == key2:
                continue
                
            if (key1, key2) not in matches:
                is_a_match = check_match(key1,
                                         key2,
                                         dict_lyrics[key1],
                                         dict_lyrics[key2])
                    
                if is_a_match:
                    matches.add((key1, key2))
                    matches.add((key2, key1))
                    count_true += 1

    return count_true, matches


def generate_matches(lyrics_dict):
    '''
    Given a dictionary of lyrics, this function searches through them and
    returns a dictionary containing the matches and a counter of how many
    matches occured.

    Arguments:
    lyrics_dict -- The lyrics dictionary in the form: {website|artist|songname: lyrics, ...}

    Returns:
    The number of matches and a list of keys that matched, e.g.
    {(key1, key2): True, (key2, key1): True, ...}
    The keys that did not match, are not returned in the dictionary.
    '''
    if not lyrics_dict or len(lyrics_dict) == 0:
        raise ValueError('Invalid lyrics dictionary')

    match_count = 0
    matches = set()

    for key1, key2 in itertools.combinations(lyrics_dict.keys(), 2):
        if key1 == key2:
            continue

        if (key1, key2) not in matches:
            is_match = check_match(key1, key2, lyrics_dict[key1], lyrics_dict[key2])
            if is_match:
                matches.add((key1, key2))
                matches.add((key2, key1))
                match_count += 1

    return match_count, matches

if __name__ == "__main__":
#def main():
    #if len(sys.argv) < 3:
    #    usage(sys.argv[0])

    pickle_processed_dict_filename = os.path.join('out', 'train_set_pickle')#sys.argv[1]
    pickle_count_true_and_matches_filename = os.path.join('out', 'train_set_pickle_ground_truth')#sys.argv[2]

    count_true = []
    matches = []
    with open(pickle_processed_dict_filename, 'rb') as file_input:
        dict_lyrics = pickle.load(file_input)

        step = int(len(dict_lyrics) / NUM_PROCESSES)
        ##dict_chunks = [dict_lyrics[i:i + step] for i in range(0, len(dict_lyrics), step)]

        pool = Pool(processes=NUM_PROCESSES)
        count, match = pool.map(generate_matches, dict_lyrics, chunksize=step)

        count_true = sum(count)
        matches.extend(match)

    with open(pickle_count_true_and_matches_filename, "wb") as pickle_count_true_and_matches_file:
        pickle.dump((count_true, matches), pickle_count_true_and_matches_file)


#if __name__ == "__main__":
#    main()
