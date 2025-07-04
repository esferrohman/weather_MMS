import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
from PIL import Image

st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")

# Tampilkan logo di header
logo = Image.open("Logo_MMS.png")
st.image(logo, width=300)

st.title("🌦️ Dashboard Cuaca Tol Tangerang-Merak")

# Link Summary dan Archive CSV dari Google Sheets
csv_url_summary = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"
csv_url_archive = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"

try:
    df_summary = pd.read_csv(csv_url_summary)
    df_archive = pd.read_csv(csv_url_archive, parse_dates=["Update Terakhir (WIB)"])
except Exception as e:
    st.error(f"Gagal mengambil data dari Google Sheets CSV: {e}")
    st.stop()

# Pilih lokasi
kolom_lokasi = "Lokasi"
lokasi = st.selectbox("📍 Pilih Lokasi", df_summary[kolom_lokasi].unique())
lokasi_data = df_summary[df_summary[kolom_lokasi] == lokasi].iloc[0]

# Layout 2 kolom
col1, col2 = st.columns([2, 1])

with col1:
    st.header(f"📊 Data Cuaca di {lokasi}")
    st.metric("🌡️ Temperatur (°C)", lokasi_data.get('Temperatur (°C)', 'N/A'))
    st.metric("💧 Kelembapan (%)", lokasi_data.get('Kelembapan (%)', 'N/A'))
    st.metric("🌬️ Kecepatan Angin (m/s)", lokasi_data.get('Kecepatan Angin (m/s)', 'N/A'))
    st.metric("🌧️ Curah Hujan (mm)", lokasi_data.get('Curah Hujan (mm)', 'N/A'))

with col2:
    icon_code = lokasi_data.get('Ikon', '')
    if isinstance(icon_code, str) and icon_code != '':
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
        st.image(icon_url, use_container_width=True)
    description = lokasi_data.get('Deskripsi Cuaca', '')
    if description:
        st.markdown(f"<div style='text-align:center; font-size:1.2em;'>{description.capitalize()}</div>", unsafe_allow_html=True)

# Tambahkan peta interaktif
st.subheader("🗺️ Lokasi di Peta")

kode_koordinat = lokasi_data.get("Kode Koordinat", "")
if kode_koordinat and isinstance(kode_koordinat, str) and "," in kode_koordinat:
    lat, lon = map(float, kode_koordinat.split(","))
    m = folium.Map(location=[lat, lon], zoom_start=13)
    folium.Marker([lat, lon], popup=f"Lokasi: {lokasi}").add_to(m)
    st_folium(m, width=700, height=500)
else:
    st.warning("Koordinat tidak ditemukan atau format salah.")

# Tampilkan tren cuaca untuk lokasi terpilih
st.subheader(f"📈 Tren Data Cuaca Hari Ini di {lokasi}")

today = pd.Timestamp.now().normalize()
lokasi_archive = df_archive[(df_archive[kolom_lokasi] == lokasi) & (df_archive["Update Terakhir (WIB)"].dt.normalize() == today)]

if not lokasi_archive.empty:
    lokasi_archive_sorted = lokasi_archive.sort_values("Update Terakhir (WIB)")
    st.line_chart(
        lokasi_archive_sorted.set_index("Update Terakhir (WIB)")[["Temperatur (°C)", "Kelembapan (%)", "Kecepatan Angin (m/s)", "Curah Hujan (mm)"]]
    )
else:
    st.info("Belum ada data cuaca hari ini untuk lokasi ini.")

# Tampilkan info waktu update terakhir
update_terakhir = lokasi_data.get("Update Terakhir (WIB)")
if isinstance(update_terakhir, str) and update_terakhir:
    st.caption(f"🕒 Data terakhir diperbarui pada: {update_terakhir} WIB")
else:
    st.caption("🕒 Data terakhir diperbarui: Tidak diketahui")

st.markdown("---")
st.caption("Data cuaca real-time berdasarkan OpenWeather API. Dibuat oleh [esferrohman].")
