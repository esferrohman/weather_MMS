import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
from PIL import Image

st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")

# Tambahkan custom CSS agar tampilan lebih elegan
st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: 'Segoe UI', sans-serif;
        }
        h1, h2, h3, h4 {
            color: #333333;
            font-weight: 600;
        }
        div[data-testid="metric-container"] {
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 12px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            margin-bottom: 10px;
        }
        section[data-testid="stSidebar"] {
            background-color: #e6f2ff;
        }
        section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
            color: #004080;
        }
        iframe {
            border-radius: 12px;
        }
    </style>
""", unsafe_allow_html=True)

# Tampilkan logo di sidebar
with st.sidebar:
    st.image("Logo_MMS.png", caption="PT MMS", use_container_width=True)
    st.title("Dashboard Cuaca")

# Load data Summary
summary_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"
try:
    df_summary = pd.read_csv(summary_url)
except Exception as e:
    st.error(f"Gagal mengambil data Summary dari Google Sheets CSV: {e}")
    st.stop()

# Validasi kolom
if 'Lokasi' not in df_summary.columns or 'Kode Koordinat' not in df_summary.columns:
    st.error("Kolom 'Lokasi' dan 'Kode Koordinat' tidak ditemukan di data CSV!")
    st.dataframe(df_summary)
    st.stop()

# Pilih lokasi
lokasi = st.selectbox("📍 Pilih Lokasi", df_summary['Lokasi'].unique())
data_lokasi = df_summary[df_summary['Lokasi'] == lokasi].iloc[0]

col1, col2 = st.columns([2, 1])
with col1:
    st.header(f"📊 Cuaca di {lokasi}")
    st.metric("🌡️ Temperatur (°C)", data_lokasi.get('Temperatur (°C)', 'N/A'))
    st.metric("💧 Kelembapan (%)", data_lokasi.get('Kelembapan (%)', 'N/A'))
    st.metric("🌬️ Kecepatan Angin (m/s)", data_lokasi.get('Kecepatan Angin (m/s)', 'N/A'))
    st.metric("🌧️ Curah Hujan (mm)", data_lokasi.get('Curah Hujan (mm)', 'N/A'))

with col2:
    icon_code = data_lokasi.get('Ikon', '')
    if isinstance(icon_code, str) and icon_code != '':
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
        st.image(icon_url, use_container_width=True)
        st.markdown(f"<p style='text-align: center; font-size: 1.2em;'>{data_lokasi.get('Deskripsi Cuaca', '')}</p>", unsafe_allow_html=True)
    else:
        st.write("Tidak ada ikon cuaca tersedia.")

# Tampilkan peta interaktif
if 'Kode Koordinat' in data_lokasi:
    lat_str, lon_str = data_lokasi['Kode Koordinat'].split(",")
    lat, lon = float(lat_str), float(lon_str)
    m = folium.Map(location=[lat, lon], zoom_start=14)
    folium.Marker([lat, lon], tooltip=f"{lokasi}", icon=folium.Icon(color="blue", icon="cloud")).add_to(m)
    st_folium(m, width=700, height=400)

# Informasi waktu update
if 'Update Terakhir (WIB)' in data_lokasi:
    waktu_update = data_lokasi['Update Terakhir (WIB)']
    st.info(f"🕒 Data terakhir diperbarui: {waktu_update}")

st.markdown("---")
st.caption("📊 Dashboard Cuaca Real-Time | Dibuat oleh [esferrohman].")
