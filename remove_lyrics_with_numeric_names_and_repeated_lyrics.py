#!/usr/bin/python3
# -*- coding: utf-8 -*-


import sys
import pickle


def usage(scriptname):
    print("Usage: %s pickle_filename pickle_processed_dict_filename" % scriptname)
    exit(1)


def remove_lyrics_with_numeric_names_and_repeated_lyrics(pickle_filename):
    dict_lyrics = {}
    
    with open(pickle_filename, "rb") as pickle_file:
        dataset = pickle.load(pickle_file)
        
        for instance in dataset:
            # 'instance' is a tuple with the following: 
            # (website_name, artist_name, lyrics_name, lyrics)
            dict_lyrics_key = '%s|%s|%s' % (instance[0], instance[1], instance[2])
            
            if str.isdigit(instance[2]):
                print("Lyrics name is only numbers. Discarding instance '%s'" % (dict_lyrics_key))
                continue
            
            if dict_lyrics_key in dict_lyrics:
                print("Found repeated key. Discarding instance '%s'" % (dict_lyrics_key))
                continue
            
            dict_lyrics[dict_lyrics_key] = instance[3]
    
    return dict_lyrics


if __name__ == "__main__":
    if (len(sys.argv) < 3):
        usage(sys.argv[0])
    
    pickle_filename = sys.argv[1]
    pickle_processed_dict_filename = sys.argv[2]
    
    dict_lyrics = remove_lyrics_with_numeric_names_and_repeated_lyrics(pickle_filename)
    
    with open(pickle_processed_dict_filename, "wb") as pickle_processed_dict_file:
        pickle.dump(dict_lyrics, pickle_processed_dict_file)
