#!/usr/bin/env python
# coding: utf-8
#
# Ini adalah GABUNGAN dari 0_download.py dengan modifikasi
# untuk mengambil jumlah data yang lebih sedikit (1500 train, 250 dev, 250 test)
#

import requests
import time
import json, os
import glob
from bs4 import BeautifulSoup
import threading

# --- FUNGSI-FUNGSI DARI 0_DOWNLOAD.PY ---
# (Kita salin semua fungsinya ke sini)

def get_id(url):
    """Mengambil ID unik dari URL Liputan6"""
    try:
        return url.split('/')[-2]
    except Exception as e:
        print(f"Error get_id {url}: {e}")
        return f"error_{int(time.time())}" # Beri ID unik jika error

def get_summary(text):
    """Mengekstrak ringkasan (shortDescription) dari HTML"""
    target = ''
    for line in text.split('\n'):
        if 'window.kmklabs.article = ' in line:
            target = line
            break
    if not target:
        return "" # Tidak menemukan ringkasan
        
    try:
        temp=target.split('window.kmklabs.article = ')[1]
        temp=temp.split(';')[0]
        data = json.loads(temp)
        return data.get('shortDescription', "") # Pakai .get() agar aman jika key tidak ada
    except Exception as e:
        print(f"Error get_summary: {e}")
        return ""

def extract_data(text):
    """Mengekstrak Judul, Tanggal, dan Isi Artikel dari HTML"""
    soup = BeautifulSoup(text, 'html.parser') # Tambahkan 'html.parser'
    
    try:
        title = soup.findAll('title')[0].getText().replace(' - News Liputan6.com', '')
    except Exception:
        title = "" # Gagal dapat title
        
    try:
        date = soup.findAll('time', {'class': 'read-page--header--author__datetime updated'})[0].getText()
    except Exception:
        date = "" # Gagal dapat tanggal
        
    article = []
    try:
        contents = soup.findAll('div', {'class': 'article-content-body__item-content'})
        for content in contents:
            article.append(content.getText())
    except Exception:
        pass # Gagal dapat artikel
        
    summary = get_summary(text)
    return title, date, article, summary

def write_file(id, url, title, date, content, summary, target_path):
    """Menyimpan 1 artikel sebagai 1 file JSON"""
    json_dict = {}
    json_dict['id']=id
    json_dict['url']=url
    json_dict['title']=title
    json_dict['date']=date
    json_dict['content']='\n'.join(content)
    json_dict['summary']=summary

    with open(f"{target_path}/{id}.json", 'w', encoding='utf-8') as json_file:
        # Menambahkan indent=4 agar filenya mudah dibaca manusia (opsional)
        json.dump(json_dict, json_file, indent=4, ensure_ascii=False) 

def proceed_one(url, path):
    """Logika utama: download 1 URL, ekstrak, dan simpan"""
    try:
        # Menambahkan headers agar terlihat seperti browser biasa
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10) # Tambah timeout
        
        if response.status_code != 200:
            print(f"Gagal download {url}, Status Code: {response.status_code}")
            return

        url = response.url # Dapatkan URL final (jika ada redirect)
        id = get_id(url)
        title, date, article, summary = extract_data(response.text)
        
        # Hanya simpan jika ada isi artikel DAN ringkasan
        if article and summary:
            write_file(id, url, title, date, article, summary, path)
        else:
            print(f"Data tidak lengkap, dilewati: {url}")
            
    except requests.exceptions.RequestException as e:
        print(f"Gagal koneksi ke {url}: {e}")
    except Exception as e:
        print(f"Gagal memproses {url}: {e}")

def proceed(urls, path):
    """Loop untuk memproses daftar URL"""
    total = len(urls)
    for i, url in enumerate(urls):
        print(f"Memproses [{path}] {i+1}/{total}: {url}")
        proceed_one(url, path)
        time.sleep(0.1) # Beri jeda sedikit agar tidak membebani server
    
def thread_func(urls, path, num_thread=1):
    """Fungsi untuk membagi tugas ke beberapa thread"""
    os.makedirs(path,exist_ok=True)
    threads = []
    chunk_size = len(urls) // num_thread + (len(urls) % num_thread > 0)
    
    for i in range(num_thread):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, len(urls))
        cur_urls = urls[start_idx:end_idx]
        
        if not cur_urls: # Lewati jika tidak ada URL di chunk ini
            continue
            
        t = threading.Thread(target=proceed, args=(cur_urls, path,))
        threads.append(t)
        t.start()
        
    # Tunggu semua thread selesai
    for t in threads:
        t.join()

# --- BAGIAN UTAMA YANG DIMODIFIKASI ---

print("--- Skrip Modifikasi untuk Scraping 2000 Data ---")

# 1. Tentukan jumlah data
JUMLAH_TRAIN = 1500
JUMLAH_DEV = 250
JUMLAH_TEST = 250

# 2. Tentukan jumlah thread (biar cepat)
# 10 thread adalah standar yang bagus
THREAD = 10 

try:
    # 3. Muat file url.json yang ASLI
    print("Membaca 'url.json'...")
    with open('url.json', 'r', encoding='utf-8') as f:
        urls = json.load(f)

    # 4. Ambil SEBAGIAN URL (Slicing)
    print(f"Mengambil {JUMLAH_TRAIN} URL train...")
    urls_train_kecil = urls['train_urls'][:JUMLAH_TRAIN]
    
    print(f"Mengambil {JUMLAH_DEV} URL dev...")
    urls_dev_kecil = urls['dev_urls'][:JUMLAH_DEV]
    
    print(f"Mengambil {JUMLAH_TEST} URL test...")
    urls_test_kecil = urls['test_urls'][:JUMLAH_TEST]
    
    print("\n--- Mulai Proses Scraping (Downloading) ---")
    print(f"Ini akan memakan waktu (estimasi 20-40 menit tergantung internet)...")
    start_time = time.time()

    # 5. Jalankan fungsi thread_func dengan data yang sudah dipotong
    # Ini akan membuat folder 'data/raw/dev', 'data/raw/test', 'data/raw/train'
    
    print(f"\nMemproses {JUMLAH_DEV} data 'dev'...")
    thread_func(urls_dev_kecil, 'data/raw/dev', THREAD)
    
    print(f"\nMemproses {JUMLAH_TEST} data 'test'...")
    thread_func(urls_test_kecil, 'data/raw/test', THREAD)
    
    print(f"\nMemproses {JUMLAH_TRAIN} data 'train'...")
    thread_func(urls_train_kecil, 'data/raw/train', THREAD)
    
    end_time = time.time()
    print("\n--- SELESAI! ---")
    print(f"Total waktu: {int(end_time - start_time)} detik.")
    print(f"Proses scraping selesai. Total {JUMLAH_TRAIN + JUMLAH_DEV + JUMLAH_TEST} artikel (target) telah coba diunduh.")
    print("File-file JSON individual sekarang ada di dalam folder 'data/raw/'.")

except FileNotFoundError:
    print("ERROR: File 'url.json' tidak ditemukan.")
    print("Pastikan file 'url.json' (dari Google Drive penulis) ada di folder yang sama dengan skrip ini.")
except KeyError as e:
    print(f"ERROR: Format 'url.json' salah. Tidak ditemukan key: {e}")
except Exception as e:
    print(f"Terjadi error: {e}")
    print("Pastikan Anda sudah menginstal library yang dibutuhkan: pip install requests beautifulsoup4")