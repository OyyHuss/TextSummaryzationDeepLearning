#!/usr/bin/env python
# coding: utf-8

import sys
import os
import shutil
import json, glob
import torch
from transformers import BertTokenizer

# --- FIX 1: Install library dulu jika belum ada ---
# pip install torch transformers

SHARD_SIZE = 2000
MIN_SRC_NSENTS = 3
MAX_SRC_NSENTS = 100
MIN_SRC_NTOKENS_PER_SENT = 5
MAX_SRC_NTOKENS_PER_SENT = 200
MIN_TGT_NTOKENS = 5
MAX_TGT_NTOKENS = 500
USE_BERT_BASIC_TOKENIZER = False

# --- FIX 2: Pastikan path menggunakan separator yang benar di Windows ---
main_path = os.path.join('data', 'clean')
data_path = os.path.join('data', 'presumm')

class BertData():
    def __init__(self):
        self.tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-uncased', do_lower_case=True)
        self.sep_token = '[SEP]'
        self.cls_token = '[CLS]'
        self.pad_token = '[PAD]'
        self.tgt_bos = '[unused1]'
        self.tgt_eos = '[unused2]'
        self.tgt_sent_split = '[unused3]'
        self.sep_vid = self.tokenizer.vocab[self.sep_token]
        self.cls_vid = self.tokenizer.vocab[self.cls_token]
        self.pad_vid = self.tokenizer.vocab[self.pad_token]
    
    def preprocess(self, src, tgt, sent_labels, use_bert_basic_tokenizer=False, is_test=False):

        original_src_txt = [' '.join(s) for s in src]

        idxs = [i for i, s in enumerate(src) if (len(s) > MIN_SRC_NTOKENS_PER_SENT)]

        _sent_labels = [0] * len(src)
        for l in sent_labels:
            _sent_labels[l] = 1

        src = [src[i][:MAX_SRC_NTOKENS_PER_SENT] for i in idxs]
        sent_labels = [_sent_labels[i] for i in idxs]
        src = src[:MAX_SRC_NSENTS]
        sent_labels = sent_labels[:MAX_SRC_NSENTS]

        if len(src) < MIN_SRC_NSENTS:
            return None

        src_txt = [' '.join(sent) for sent in src]
        text = ' {} {} '.format(self.sep_token, self.cls_token).join(src_txt)

        src_subtokens = self.tokenizer.tokenize(text)

        src_subtokens = [self.cls_token] + src_subtokens + [self.sep_token]
        src_subtoken_idxs = self.tokenizer.convert_tokens_to_ids(src_subtokens)
        _segs = [-1] + [i for i, t in enumerate(src_subtoken_idxs) if t == self.sep_vid]
        segs = [_segs[i] - _segs[i - 1] for i in range(1, len(_segs))]
        segments_ids = []
        for i, s in enumerate(segs):
            if (i % 2 == 0):
                segments_ids += s * [0]
            else:
                segments_ids += s * [1]
        cls_ids = [i for i, t in enumerate(src_subtoken_idxs) if t == self.cls_vid]
        sent_labels = sent_labels[:len(cls_ids)]

        tgt_subtokens_str = '[unused1] ' + ' [unused3] '.join(
            [' '.join(self.tokenizer.tokenize(' '.join(tt))) for tt in tgt]) + ' [unused2]'
        tgt_subtoken = tgt_subtokens_str.split()[:MAX_TGT_NTOKENS]
        if len(tgt_subtoken) < MIN_TGT_NTOKENS:
            return None

        tgt_subtoken_idxs = self.tokenizer.convert_tokens_to_ids(tgt_subtoken)

        tgt_txt = '<q>'.join([' '.join(tt) for tt in tgt])
        src_txt = [original_src_txt[i] for i in idxs]

        return src_subtoken_idxs, sent_labels, tgt_subtoken_idxs, segments_ids, cls_ids, src_txt, tgt_txt

def read(fname):
    # --- FIX 3: Tambah encoding utf-8 ---
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            data = json.loads(f.readline())
        return data['clean_article'], data['clean_summary'], data['extractive_summary']
    except Exception as e:
        print(f"Error reading {fname}: {e}")
        return None, None, None

def format_to_bert(path):
    bert = BertData()
    files = glob.glob(path)
    p_ct = 0
    dataset = []
    
    print(f"Processing {len(files)} files in {path}...")

    # --- FIX 4: Ambil nama set (train/dev/test) secara aman untuk Windows/Linux ---
    # path contoh: "data/clean/train/*"
    # os.path.split akan memisahkan head ('data/clean/train') dan tail ('*')
    head, tail = os.path.split(path)
    # Lalu kita ambil nama folder terakhir dari head ('train')
    set_name = os.path.basename(head)
    
    for fname in files:
        #process
        source, tgt, sent_labels = read(fname)
        if source is None: continue

        b_data = bert.preprocess(source, tgt, sent_labels)
        if (b_data is None):
            continue
        src_subtoken_idxs, sent_labels, tgt_subtoken_idxs, segments_ids, cls_ids, src_txt, tgt_txt = b_data
        b_data_dict = {"src": src_subtoken_idxs, "tgt": tgt_subtoken_idxs,
                       "src_sent_labels": sent_labels, "segs": segments_ids, 'clss': cls_ids,
                       'src_txt': src_txt, "tgt_txt": tgt_txt}
        dataset.append(b_data_dict)
        if len(dataset) >= SHARD_SIZE:
            # --- FIX 5: Gunakan os.path.join dan set_name yang benar ---
            pt_file = os.path.join(data_path, "{:s}.{:d}.bert.pt".format(set_name, p_ct))
            print(f"Saving {pt_file}")
            torch.save(dataset, pt_file)
            dataset = []
            p_ct += 1
    if len(dataset) > 0:
        # --- FIX 6: Sama seperti di atas ---
        pt_file = os.path.join(data_path, "{:s}.{:d}.bert.pt".format(set_name, p_ct))
        print(f"Saving {pt_file}")
        torch.save(dataset, pt_file)
        dataset = []
        p_ct += 1

# --- Main Execution ---

# Cek apakah library sudah terinstall
try:
    import torch
    from transformers import BertTokenizer
except ImportError:
    print("ERROR: Library 'torch' atau 'transformers' belum terinstall.")
    print("Silakan jalankan: pip install torch transformers")
    sys.exit(1)

if os.path.exists(data_path):
    shutil.rmtree(data_path)
os.makedirs(data_path)

# Gunakan os.path.join untuk path yang aman
format_to_bert(os.path.join(main_path, 'train', '*'))
format_to_bert(os.path.join(main_path, 'dev', '*'))
format_to_bert(os.path.join(main_path, 'test', '*'))

print("\nSELESAI! File .bert.pt Anda sudah siap di folder data/presumm/")