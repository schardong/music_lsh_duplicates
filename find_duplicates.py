#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import pickle
import itertools
from datasketch import MinHash, MinHashLSH

TRAIN_GT_FILE = os.path.join('out', 'train_set_ground_truth_pickle')
TRAIN_LSH_PATH = os.path.join('out', 'lsh_trainset_tests')
OUTPUT_BENCHMARK_FILE = os.path.join('out', 'train_lsh_parameters.csv')

def build_lsh_keypair_set(lsh_index_list):
    '''
    Given the LSH index, this function iterates through it's buckets (sublists)
    and returns all the pairs of possible duplicates keys in a set.
    '''
    if not lsh_index_list or len(lsh_index_list) == 0:
        raise ValueError('Invalid LSH index.')

    key_set = set()
    for sublist in lsh_index_list:
        key_set |= set(itertools.combinations(sublist, 2))

    return key_set


def get_lsh_parameters(lsh_filename):
    '''
    Given a single filename of an LSH index, this function processes it and
    returns the parameters used to build that index.

    Arguments:
    lsh_filename -- The index filename

    Returns:
    A dictionary with the parameters used to build the LSH.
    '''
    if not lsh_filename or len(lsh_filename) == 0:
        raise ValueError('Invalid LSH filename')

    first_split = lsh_filename.split('_')
    if len(first_split) != 5:
        raise ValueError('')

    param_dict = {}
    for key_item in first_split:
        key, item = key_item.split('-')
        param_dict[key] = item

    return param_dict


def calc_precision_recall(lsh_filename, ground_truth):
    '''
    Given the filename of the LSH index in the filesystem and a ground truth
    set, this function calculates the precision and recall statistics for the
    duplicates indicated by the LSH index.

    Arguments:
    lsh_filename -- The full path to the LSH index file.
    ground_truth -- A set in the form (key1, key2), (key2, key1), ... containing
    the actual duplicates.

    Returns:
    Two floating point numbers, the precision and recall.
    '''
    lsh_index = []
    with open(lsh_filename, 'rb') as file_in:
        lsh_index = pickle.load(file_in)

    if not lsh_index or len(lsh_index) == 0:
        raise ValueError('Invalid LSH, empty list.')
    
    lsh_key_set = build_lsh_keypair_set(lsh_index)
    del lsh_index
    num_matches_lsh = len(lsh_key_set)
    num_actual_matches = 0
    match_set = ground_truth[1]

    for key_pair in lsh_key_set:
        if key_pair in match_set:
            num_actual_matches += 1
        if key_pair[::-1] in match_set:
            num_actual_matches += 1

    precision = (num_actual_matches // 2) / num_matches_lsh
    recall = (num_actual_matches // 2) / ground_truth[0]

    return precision, recall


def main():
    file_list = []
    for (_, _, filenames) in os.walk(TRAIN_LSH_PATH):
        file_list.extend(filenames)
        break

    train_gt = []
    with open(TRAIN_GT_FILE, 'rb') as file_in:
        train_gt = pickle.load(file_in)

    if not train_gt or len(train_gt) == 0:
        print('INVALID GROUND TRUTH FILE')
        exit(1)

    if not os.path.exists(OUTPUT_BENCHMARK_FILE):
        with open(OUTPUT_BENCHMARK_FILE, 'w+') as benchmark_out:
            print('Num.Bands, Rows.Per.Band, Lsh.Threshold, Shingle.Size, Num.Hashes, Precision, Recall',
                  file=benchmark_out)

    with open(OUTPUT_BENCHMARK_FILE, 'a') as benchmark_out:
        for lsh_filename in file_list:
            print('Processing file: {}'.format(lsh_filename))
            
            precision, recall = calc_precision_recall(os.path.join(TRAIN_LSH_PATH, lsh_filename),
                                                      train_gt)
            param_dict = get_lsh_parameters(lsh_filename)

            num_bands = param_dict['b']
            rows_per_band = param_dict['r']
            lsh_thresh = param_dict['thresh']
            shingle_size = param_dict['shinglesize']
            num_hashes = param_dict['numperp']

            line_data = '{}, {}, {}, {}, {}, {}, {}'.format(num_bands,
                                                            rows_per_band,
                                                            lsh_thresh,
                                                            shingle_size,
                                                            num_hashes,
                                                            precision,
                                                            recall)
            print(line_data, file=benchmark_out)


if __name__ == '__main__':
    main()


