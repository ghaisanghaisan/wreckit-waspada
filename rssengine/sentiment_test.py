from transformers import pipeline

# 1. Load model Zero-Shot multibahasa (mendukung Bahasa Indonesia)
print("Loading model...")
classifier = pipeline(
    "zero-shot-classification",
    model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
)

# 2. Teks berita yang ingin dianalisis
teks_berita = "Polisi Bubarkan Remaja Hendak Tawuran di Jakbar, Celurit hingga Sinte Disita   "

# 3. Masukkan aturan Anda di sini!
aturan_positif = "prestasi, keberhasilan, penghargaan, kerja sama, pembangunan, situasi aman, informasi netral, kondusif"
aturan_negatif = "serangan siber, kebocoran data, ransomware, korupsi, kritik, kelalaian, konflik, ancaman"

# Kita gabungkan menjadi kandidat label
candidate_labels = [aturan_positif, aturan_negatif]

# 4. Analisis teks berdasarkan aturan tersebut
hasil = classifier(teks_berita, candidate_labels)

# 5. Konversi hasil kembali ke format yang Anda inginkan (POSITIF / NEGATIF)
label_terpilih = hasil['labels'][0] # Mengambil skor kecocokan tertinggi

if label_terpilih == aturan_positif:
    print("SENTIMEN: POSITIF")
else:
    print("SENTIMEN: NEGATIF")
