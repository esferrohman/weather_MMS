import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")
st.title("🌦️ Dashboard Cuaca Tol Tangerang-Merak")

# Link CSV dari Google Sheets
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"

# Baca data
try:
    df = pd.read_csv(csv_url)
except Exception as e:
    st.error(f"❌ Gagal mengambil data dari Google Sheets: {e}")
    st.stop()

# Deteksi kolom lokasi
kolom_lokasi = None
for kandidat in ["Lokasi", "Gerbang"]:
    if kandidat in df.columns:
        kolom_lokasi = kandidat
        break

if kolom_lokasi is None or "Kode Koordinat" not in df.columns:
    st.error("❌ Kolom 'Lokasi' (atau 'Gerbang') dan 'Kode Koordinat' harus ada di data CSV!")
    st.dataframe(df)
    st.stop()

# Pilih lokasi
lokasi = st.selectbox("📍 Pilih Lokasi", df[kolom_lokasi].unique())
lokasi_data = df[df[kolom_lokasi] == lokasi].iloc[0]

# Layout dua kolom
col1, col2 = st.columns([2, 1])

with col1:
    st.header(f"📊 Data Cuaca: {lokasi}")
    st.metric("🌡️ Temperatur (°C)", lokasi_data.get('Temperatur (°C)', 'N/A'))
    st.metric("💧 Kelembapan (%)", lokasi_data.get('Kelembapan (%)', 'N/A'))
    st.metric("🌬️ Kecepatan Angin (m/s)", lokasi_data.get('Kecepatan Angin (m/s)', 'N/A'))
    st.metric("🌧️ Curah Hujan (mm)", lokasi_data.get('Curah Hujan (mm)', 'N/A'))

with col2:
    icon_code = lokasi_data.get('Ikon', '')
    description = lokasi_data.get('Deskripsi Cuaca', 'N/A')
    if isinstance(icon_code, str) and icon_code != '':
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
        st.image(icon_url, use_container_width=True)
        st.markdown(f"<p style='text-align: center; font-size: 18px;'>{description.capitalize()}</p>", unsafe_allow_html=True)
    else:
        st.write("Tidak ada ikon cuaca tersedia.")

# Peta interaktif
st.header(f"🗺️ Lokasi: {lokasi}")
try:
    koordinat_str = lokasi_data.get('Kode Koordinat', '')
    lat_str, lon_str = koordinat_str.split(',')
    lat, lon = float(lat_str), float(lon_str)
    st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))
except Exception as e:
    st.warning(f"📍 Koordinat tidak valid atau tidak ditemukan: {e}")

# Footer
st.markdown("---")
st.caption("Data cuaca real-time berdasarkan OpenWeather API. Dibuat oleh [esferrohman].")
