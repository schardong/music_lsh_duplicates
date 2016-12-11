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

LSH_PARAMETERS = [(0.01, 10,  64),  ## P = 0.066009708219382, R = 0.943741209563994
                  (0.50,  5, 128),  ## P = 0.085720778021916, R = 0.848925055254169
                  (0.30,  7,  64),  ## P = 0.079245407983045, R = 0.865461121157324
                  (0.10,  5, 128),  ## P = 0.086354372135589, R = 0.951758087201125
                  (0.50,  5,  64)]  ## P = 0.085093935514376, R = 0.853365481213582



def usage():
    print('./{} validation_dataset validation_ground_truth_dataset'.format(sys.argv[0]))


def run(validation_set, validation_gt_set, parameter_tuple):
    lsh_threshold = parameter_tuple[0]
    lsh_shingle_size = parameter_tuple[1]
    lsh_num_hash = parameter_tuple[2]

    lsh = MinHashLSH(threshold=lsh_threshold,
                     num_perm=lsh_num_hash)

    for key, lyrics in validation_set.items():
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
    match_set = validation_gt_set[1]

    for key_pair in lsh_key_set:
        if key_pair in match_set:
            num_actual_matches += 1
        if key_pair[::-1] in match_set:
            num_actual_matches += 1

    precision = (num_actual_matches // 2) / num_matches_lsh
    recall = (num_actual_matches // 2) / validation_gt_set[0]

    print('(thresh = {}, num_hashes = {}, shingle_size = {}) => P = {}; R = {}'.format(lsh_threshold,
                                                                                       lsh_num_hash,
                                                                                       lsh_shingle_size,
                                                                                       precision,
                                                                                       recall))

def main():
    if len(sys.argv) != 3:
        usage()
        exit(1)

    validation_set = {}
    with open(sys.argv[1], 'rb') as validation_set_in:
        validation_set = pickle.load(validation_set_in)

    validation_gt = set()
    with open(sys.argv[2], 'rb') as validation_gt_in:
        validation_gt = pickle.load(validation_gt_in)

    process_pool = []
    for param_tuple in LSH_PARAMETERS:
        p = Process(target=run, args=(validation_set, validation_gt, param_tuple))
        process_pool.append(p)
        p.start()

    for p in process_pool:
        p.join()


if __name__ == '__main__':
    main()
