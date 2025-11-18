#!/usr/bin/env python
# coding: utf-8

import os
import hashlib
import struct
import subprocess
import collections
# import tensorflow as tf # TF seringkali tidak dipakai di sini, tapi jika error module not found, uncomment lagi
import json, glob, math
import numpy as np
from multiprocessing import Process
import argparse
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

MAX_SENTENCE = 100

def get_string(sentences):
    all_sentence = []
    for sentence in sentences:
        all_sentence.append(' '.join(sentence))
    return ' '.join(all_sentence).lower()

def harmonic_mean(precision, recall):
    if precision == 0 and recall == 0:
        return 0
    return 2 * precision * recall / (precision + recall)

def compute_dictionary (string):
    unigram = {}
    for word in string.split():
        unigram[word] = unigram.get(word, 0) + 1
    return unigram

def rouge1 (summary, reference):
    overlap = 0
    denominator = 0
    for key in reference.keys():
        denominator += reference[key]
        overlap += min(summary.get(key, 0), reference[key])
    return overlap / denominator

def get_score(cur_range, article, unigram_summary):
    cur_article = article[cur_range]
    unigram_article = compute_dictionary(get_string(cur_article).lower())
    precision = rouge1(unigram_summary, unigram_article)
    recall = rouge1(unigram_article, unigram_summary)
    return harmonic_mean(precision, recall)

def get_list(cur_list, size):
    arrays = np.arange(size)
    next_array = set(arrays) - set(cur_list)
    return list(next_array)

def find_label(fname):
    # Tambah encoding utf-8
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            data = json.loads(f.readline())
    except Exception as e:
        print(f"Error reading {fname}: {e}")
        return None

    article = np.array(data['clean_article'][:MAX_SENTENCE], dtype=object) # dtype object untuk keamanan numpy baru
    summary = get_string(data['clean_summary']).lower()
    unigram_summary = compute_dictionary(summary)
    temp_result = []
    for idx in range(len(article)):
        cur_id = idx
        global_best = None
        ids = [cur_id]
        while (True):
            cur_score = {}
            next_list = get_list(ids, len(article))
            if len(next_list) == 0:
                if global_best is not None and len(temp_result) == 0:
                    temp_result.append(global_best)
                break
            for idy in next_list:
                cur_range = np.array(ids + [idy])
                score = get_score(cur_range, article, unigram_summary)
                # cur_range.tostring() deprecated, ganti tobytes()
                cur_score[cur_range.tobytes()] = score 
            
            # sort by value 
            if not cur_score:
                break

            cur_best = sorted(cur_score, key=cur_score.get, reverse=True)[0]
            cur_best_array = np.frombuffer(cur_best, dtype=int) # ganti fromstring jadi frombuffer
            
            if global_best is None:
                global_best = (cur_best_array, cur_score[cur_best])
                ids = list(cur_best_array)
            else:
                if global_best[1] > cur_score[cur_best]: #stop
                    temp_result.append(global_best)
                    break
                else:
                    global_best = (cur_best_array, cur_score[cur_best])
                    ids = list(cur_best_array)
    try:
        if temp_result:
            data['extractive_summary'] = sorted(temp_result, key=lambda tup: tup[1], reverse=True)[0][0].tolist()
        else:
            data['extractive_summary'] = [0]
    except:
        # assert (len(article) == 1)
        data['extractive_summary'] = [0]
    return data

# --- PERUBAHAN 1: Fungsi run_thread dipindah ke Global ---
def run_thread(files, target_path):
    for f in files:
        data = find_label(f)
        if data is not None:
            # Tambah encoding utf-8 saat menulis
            filename = os.path.basename(f) # Ambil nama file saja agar aman
            with open(os.path.join(target_path, filename), 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file)

def proceed(source_path, num_thread):
    # Fix path replacement logic agar aman di Windows
    target_path = source_path.replace('*', '')
    files = glob.glob(source_path)

    if not files:
        print(f"Warning: No files found in {source_path}")
        return

    size = int(math.ceil(1.0*len(files)/num_thread))
    processes = list()
    
    for i in range(num_thread):
        start = i * size
        end = start + size
        if end > len(files):
            end = len(files)
        p = files[start:end]
        
        if not p: continue

        # Kirim target_path sebagai argumen juga
        process = Process(target=run_thread, args=(p, target_path))
        process.start()
        processes.append(process)
        if end == len(files):
            break
    for process in processes:
        process.join()

# --- PERUBAHAN 2: Entry point guard untuk Windows ---
if __name__ == '__main__':
    # Saya kurangi threads jadi 4-8 agar laptop tidak hang
    # Jika CPU Anda kuat (misal i7/Ryzen 7 terbaru), bisa naikkan ke 8 atau 10
    THREADS = 4 
    source_path = 'data/clean/' # Pastikan slash sesuai folder Anda
    
    print("Working on All Files... (Ini akan memakan waktu, jangan di-close)")
    
    print("Processing Train Data...")
    proceed(os.path.join(source_path, 'train', '*'), THREADS)
    
    print("Processing Test Data...")
    proceed(os.path.join(source_path, 'test', '*'), THREADS)
    
    print("Processing Dev Data...")
    proceed(os.path.join(source_path, 'dev', '*'), THREADS)

    print("SELESAI! Silakan cek file JSON Anda, key 'extractive_summary' seharusnya sudah ada.")