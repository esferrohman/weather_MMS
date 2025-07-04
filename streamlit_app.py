import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")

# Logo
st.image("Logo_MMS.png", width=200)

st.title("🌦️ Dashboard Cuaca Tol Tangerang-Merak")

# Data summary
summary_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"

try:
    df = pd.read_csv(summary_csv)
except Exception as e:
    st.error(f"Gagal mengambil data dari Summary CSV: {e}")
    st.stop()

# Pastikan kolom penting ada
expected_cols = ["Lokasi", "Temperatur (°C)", "Kelembapan (%)", "Kecepatan Angin (m/s)", "Curah Hujan (mm)", "Deskripsi Cuaca", "Ikon", "Kode Koordinat"]
missing_cols = [col for col in expected_cols if col not in df.columns]
if missing_cols:
    st.error(f"Kolom berikut tidak ditemukan di data: {missing_cols}")
    st.dataframe(df)
    st.stop()

# Dropdown lokasi
lokasi = st.selectbox("📍 Pilih Lokasi", df["Lokasi"].unique())
lokasi_data = df[df["Lokasi"] == lokasi].iloc[0]

col1, col2 = st.columns([2, 1])
with col1:
    st.metric("🌡️ Temperatur (°C)", lokasi_data["Temperatur (°C)"])
    st.metric("💧 Kelembapan (%)", lokasi_data["Kelembapan (%)"])
    st.metric("🌬️ Kecepatan Angin (m/s)", lokasi_data["Kecepatan Angin (m/s)"])
    st.metric("🌧️ Curah Hujan (mm)", lokasi_data["Curah Hujan (mm)"])

with col2:
    icon_code = lokasi_data["Ikon"]
    if pd.notna(icon_code) and icon_code != '':
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
        st.image(icon_url, use_container_width=True)
        st.caption(lokasi_data["Deskripsi Cuaca"].capitalize())
    else:
        st.write("Tidak ada ikon cuaca tersedia.")

# Peta interaktif
st.subheader("🗺️ Peta Lokasi")
koordinat_str = lokasi_data["Kode Koordinat"]
try:
    lat, lon = map(float, koordinat_str.split(","))
    m = folium.Map(location=[lat, lon], zoom_start=12)
    folium.Marker([lat, lon], tooltip=lokasi, popup=lokasi).add_to(m)
    st_folium(m, width=700, height=500)
except Exception as e:
    st.error(f"Gagal membuat peta: {e}")

# Terakhir update
update_terakhir = df["Update Terakhir (WIB)"].max()
st.caption(f"📅 Data terakhir diperbarui: {update_terakhir}")

st.markdown("---")
st.caption("Data cuaca real-time berdasarkan OpenWeather API. Dibuat oleh [esferrohman].")
