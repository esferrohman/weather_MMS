import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")

st.title("🌦️ Dashboard Cuaca Tol Tangerang-Merak")

# Link CSV Google Sheets (jangan ubah kalau sudah benar)
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"

try:
    df = pd.read_csv(csv_url)
except Exception as e:
    st.error(f"Gagal mengambil data dari Google Sheets CSV: {e}")
    st.stop()

st.write("Kolom yang ditemukan di data:", df.columns.tolist())

# Deteksi kolom lokasi otomatis
kolom_lokasi = None
for kandidat in ["Lokasi", "Gerbang"]:
    if kandidat in df.columns:
        kolom_lokasi = kandidat
        break

if kolom_lokasi is None:
    st.error("Kolom 'Lokasi' atau 'Gerbang' tidak ditemukan di data CSV!")
    st.dataframe(df)
    st.stop()

lokasi = st.selectbox("📍 Pilih Lokasi", df[kolom_lokasi].unique())
lokasi_data = df[df[kolom_lokasi] == lokasi].iloc[0]

col1, col2 = st.columns([2, 1])

with col1:
    st.header(f"📊 Data Cuaca di {lokasi}")
    st.metric("🌡️ Temperatur (°C)", lokasi_data.get('Temperatur (°C)', 'N/A'))
    st.metric("💧 Kelembapan (%)", lokasi_data.get('Kelembapan (%)', 'N/A'))
    st.metric("🌬️ Kecepatan Angin (m/s)", lokasi_data.get('Kecepatan Angin (m/s)', 'N/A'))
    st.metric("🌧️ Curah Hujan (mm)", lokasi_data.get('Curah Hujan (mm)', 'N/A'))
    st.write(f"**📝 Deskripsi Cuaca:** {lokasi_data.get('Deskripsi Cuaca', 'N/A')}")

with col2:
    icon_code = lokasi_data.get('Ikon', '')
    if isinstance(icon_code, str) and icon_code != '':
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
        st.image(icon_url, caption="Ikon Cuaca dari OpenWeather", use_column_width=True)
    else:
        st.write("Tidak ada ikon cuaca tersedia.")

st.markdown("---")
st.caption("Data cuaca real-time berdasarkan OpenWeather API. Dibuat oleh [esferrohman].")
