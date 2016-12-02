#!/usr/bin/python3
# -*- coding: utf-8 -*-


import sys
import pickle


def usage(scriptname):
    print("Usage: %s pickle_processed_dict_filename pickle_count_true_and_matches_filename" % scriptname)
    exit(1)


def check_match(instance1, instance2):
    # 'instance[12]' is a tuple with the following: 
    # (website_name, artist_name, lyrics_name, lyrics)
    
    # Checks whether artist name is the same
    if not is_same_string(instance1[1], instance2[1], 1):
        return False
    
    # Checks whether lyrics name is the same
    if not is_same_string(instance1[2], instance2[2], 1):
        return False
    
    # Checks whether lyrics is the same
    if not is_same_string(instance1[3], instance2[3], 0.1):
        return False
    
    return True


def generate_count_true_and_matches(pickle_processed_dict_filename): 
    count_true = 0
    matches = {}
    
    with open(pickle_processed_dict_filename, "rb") as pickle_processed_dict_file:
        dataset = pickle.load(pickle_processed_dict_file)
        
        # 'instance[12]' is a tuple with the following: 
        # (website_name, artist_name, lyrics_name, lyrics)
        for instance1 in dataset:
            instance1_key = '%s|%s|%s' % (instance1[0], instance1[1], instance1[2])
            
            for instance2 in dataset:
                instance2_key = '%s|%s|%s' % (instance2[0], instance2[1], instance2[2])
                
                if (instance1_key, instance2_key) not in matches and \
                   (instance2_key, instance1_key) not in matches:
                    is_a_match = check_match(instance1, instance2)
                    
                    if is_a_match:
                        matches[(instance1_key, instance2_key)] = True
                        count_true += 1
                    else:
                        matches[(instance1_key, instance2_key)] = False
    
    return count_true, matches


if __name__ == "__main__":
    if (len(sys.argv) < 3):
        usage(sys.argv[0])
    
    pickle_processed_dict_filename = sys.argv[1]
    pickle_count_true_and_matches_filename = sys.argv[2]
    
    count_true, matches = generate_count_true_and_matches(pickle_processed_dict_filename)
    
    with open(pickle_count_true_and_matches_filename, "wb") as pickle_count_true_and_matches_file:
        pickle.dump((count_true, matches), pickle_count_true_and_matches_file)
