#!/usr/bin/env python
# coding: utf-8
#
# LANGKAH 2: Preprocessing (Menggabungkan Data)
#
# Skrip ini akan membaca SEMUA file .json individual
# dari folder 'data/raw/' dan menggabungkannya
# menjadi 3 file .jsonl (JSON Lines) yang bersih.
#

import json
import glob
import os
import re

def clean_text(text):
    """Fungsi sederhana untuk membersihkan teks"""
    if not text:
        return ""
    # Ganti beberapa spasi/newline berlebih menjadi satu spasi
    text = re.sub(r'\s+', ' ', text)
    # Hapus spasi di awal/akhir
    text = text.strip()
    return text

def process_folder(input_dir, output_file_path):
    """
    Membaca semua file .json di input_dir, membersihkan,
    dan menyimpannya sebagai satu file .jsonl.
    """
    print(f"Memproses folder: {input_dir}")
    
    # Dapatkan daftar semua file .json di dalam folder
    # Gunakan os.path.join untuk menggabungkan path agar aman
    json_files = glob.glob(os.path.join(input_dir, '*.json'))
    
    if not json_files:
        print(f"Peringatan: Tidak ada file .json ditemukan di {input_dir}")
        return 0

    count = 0
    # Buka file output untuk ditulis
    with open(output_file_path, 'w', encoding='utf-8') as f_out:
        # Loop untuk setiap file .json yang ditemukan
        for file_path in json_files:
            try:
                # Buka file .json individual
                with open(file_path, 'r', encoding='utf-8') as f_in:
                    data = json.load(f_in)
                
                # Ekstrak data yang kita butuhkan
                article_id = data.get('id', '')
                article_content = data.get('content', '')
                article_summary = data.get('summary', '')

                # Hanya proses jika ada content dan summary
                if article_content and article_summary:
                    # Buat format data baru yang bersih
                    clean_data = {
                        'id': article_id,
                        'clean_article': clean_text(article_content),
                        'clean_summary': clean_text(article_summary)
                    }
                    
                    # Tulis data sebagai satu baris JSON string ke file .jsonl
                    f_out.write(json.dumps(clean_data, ensure_ascii=False) + '\n')
                    count += 1
                    
            except Exception as e:
                print(f"Gagal memproses file {file_path}: {e}")
                
    print(f"Selesai! {count} artikel dari {len(json_files)} file telah digabung ke {output_file_path}")
    return count

# --- BAGIAN UTAMA ---

print("--- Skrip LANGKAH 2: Menggabungkan Data (Preprocessing) ---")

# Tentukan path input (hasil dari skrip pertama)
RAW_DIR = 'data/raw'
TRAIN_INPUT_DIR = os.path.join(RAW_DIR, 'train')
DEV_INPUT_DIR = os.path.join(RAW_DIR, 'dev')
TEST_INPUT_DIR = os.path.join(RAW_DIR, 'test')

# Tentukan path output (dataset bersih)
CLEANED_DIR = 'data/cleaned'
os.makedirs(CLEANED_DIR, exist_ok=True) # Buat folder output jika belum ada

TRAIN_OUTPUT_FILE = os.path.join(CLEANED_DIR, 'train.jsonl')
DEV_OUTPUT_FILE = os.path.join(CLEANED_DIR, 'dev.jsonl')
TEST_OUTPUT_FILE = os.path.join(CLEANED_DIR, 'test.jsonl')

# start_time = time.time()

# Proses setiap folder (train, dev, test)
total_processed = 0
total_processed += process_folder(TRAIN_INPUT_DIR, TRAIN_OUTPUT_FILE)
total_processed += process_folder(DEV_INPUT_DIR, DEV_OUTPUT_FILE)
total_processed += process_folder(TEST_INPUT_DIR, TEST_OUTPUT_FILE)

# end_time = time.time()

print("\n--- SELESAI SEMUA! ---")
# print(f"Total waktu: {int(end_time - start_time)} detik.")
print(f"Total {total_processed} artikel telah diproses dan digabung.")
print(f"Dataset bersih Anda sekarang ada di folder '{CLEANED_DIR}'")
print(f"File-filenya adalah: train.jsonl, dev.jsonl, test.jsonl")