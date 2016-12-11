#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import pickle
from datasketch import MinHash, MinHashLSH
from multiprocessing import Process
from build_hash_index import build_shingle_list
from build_hash_index import build_minhash
from build_hash_index import get_possible_duplicates
from find_duplicates import build_lsh_keypair_set

LSH_PARAMETERS = (0.10,  5, 128)

def usage():
    print('./{} test_dataset test_ground_truth_dataset'.format(sys.argv[0]))


def run(test_set, test_gt_set, parameter_tuple):
    lsh_threshold = parameter_tuple[0]
    lsh_shingle_size = parameter_tuple[1]
    lsh_num_hash = parameter_tuple[2]

    lsh = MinHashLSH(threshold=lsh_threshold,
                     num_perm=lsh_num_hash)

    for key, lyrics in test_set.items():
        if len(lyrics) == 0:
            continue
        shingle_list = build_shingle_list(lyrics, ngram_size=lsh_shingle_size)
        if len(shingle_list) == 0:
            continue

        mhash = build_minhash(shingle_list, num_perm=lsh_num_hash)
        try:
            lsh.insert(key, mhash)
        except ValueError:
            print('Repeated Key = {}'.format(key))

    lsh_key_set = build_lsh_keypair_set(get_possible_duplicates(lsh))
    num_matches_lsh = len(lsh_key_set)
    num_actual_matches = 0
    match_set = test_gt_set[1]

    for key_pair in lsh_key_set:
        if key_pair in match_set:
            num_actual_matches += 1
        if key_pair[::-1] in match_set:
            num_actual_matches += 1

    precision = (num_actual_matches // 2) / num_matches_lsh
    recall = (num_actual_matches // 2) / test_gt_set[0]

    print('(thresh = {}, num_hashes = {}, shingle_size = {}) => P = {}; R = {}'.format(lsh_threshold,
                                                                                       lsh_num_hash,
                                                                                       lsh_shingle_size,
                                                                                       precision,
                                                                                       recall))

def main():
    if len(sys.argv) != 3:
        usage()
        exit(1)

    test_set = {}
    with open(sys.argv[1], 'rb') as test_set_in:
        test_set = pickle.load(test_set_in)

    test_gt = set()
    with open(sys.argv[2], 'rb') as test_gt_in:
        test_gt = pickle.load(test_gt_in)

    run(test_set, test_gt, LSH_PARAMETERS)

if __name__ == '__main__':
    main()
