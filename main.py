import json

# Ganti 'nama_file_anda.json' dengan nama file yang baru Anda unduh
input_filename = 'url.json' 
output_filename = 'daftar_url_dev.txt'

try:
    # 1. Buka dan baca file JSON
    with open(input_filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. Ambil daftar URL dari dalam key "train_urls"
    urls = data['dev_urls']

    # 3. Tulis setiap URL ke file TXT sebagai baris baru
    with open(output_filename, 'w', encoding='utf-8') as f:
        for url in urls:
            f.write(url + '\n')

    print(f"Berhasil! {len(urls)} URL telah disimpan di {output_filename}")
    print("PERINGATAN: File ini hanya berisi DAFTAR LINK, bukan data artikel/ringkasan.")

except FileNotFoundError:
    print(f"Error: File '{input_filename}' tidak ditemukan.")
except KeyError:
    print("Error: Format JSON salah. Tidak ditemukan key 'train_urls'.")