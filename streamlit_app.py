import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")
st.title("🌦️ Dashboard Cuaca Tol Tangerang-Merak")

# Link CSV Google Sheets
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"

try:
    df = pd.read_csv(csv_url)
except Exception as e:
    st.error(f"Gagal mengambil data dari Google Sheets CSV: {e}")
    st.stop()

# Pastikan kolom Lokasi & Update Terakhir ada
if "Lokasi" not in df.columns or "Update Terakhir (WIB)" not in df.columns:
    st.error("Kolom 'Lokasi' dan/atau 'Update Terakhir (WIB)' tidak ditemukan di data CSV!")
    st.dataframe(df)
    st.stop()

# Konversi kolom update ke datetime
df["Update Terakhir (WIB)"] = pd.to_datetime(df["Update Terakhir (WIB)"], errors="coerce")
today = datetime.now().date()

# Filter hanya data hari ini
df_today = df[df["Update Terakhir (WIB)"].dt.date == today]
if df_today.empty:
    st.warning("Belum ada data cuaca terbaru untuk hari ini.")
    st.stop()

lokasi = st.selectbox("📍 Pilih Lokasi", df_today["Lokasi"].unique())
lokasi_data = df_today[df_today["Lokasi"] == lokasi].iloc[0]

col1, col2 = st.columns([2, 1])

with col1:
    st.header(f"📊 Data Cuaca di {lokasi}")
    st.metric("🌡️ Temperatur (°C)", lokasi_data.get('Temperatur (°C)', 'N/A'))
    st.metric("💧 Kelembapan (%)", lokasi_data.get('Kelembapan (%)', 'N/A'))
    st.metric("🌬️ Kecepatan Angin (m/s)", lokasi_data.get('Kecepatan Angin (m/s)', 'N/A'))
    st.metric("🌧️ Curah Hujan (mm)", lokasi_data.get('Curah Hujan (mm)', '0'))

with col2:
    icon_code = lokasi_data.get('Ikon', '')
    if isinstance(icon_code, str) and icon_code != '':
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
        st.image(icon_url, use_container_width=True)
    deskripsi = lokasi_data.get('Deskripsi Cuaca', '').capitalize()
    if deskripsi:
        st.write(f"**{deskripsi}**")
    else:
        st.write("Tidak ada deskripsi cuaca tersedia.")

st.markdown("---")
st.header("🗺️ Peta Lokasi Gerbang")

# Buat peta folium
m = folium.Map(location=[-6.2, 106.5], zoom_start=10)
for _, row in df_today.iterrows():
    # Pastikan ada koordinat
    latlon = str(row.get('Kode Koordinat', ''))
    if latlon and "," in latlon:
        lat, lon = map(float, latlon.split(","))
        popup_html = f"""
        <b>{row['Lokasi']}</b><br>
        📝 {row.get('Deskripsi Cuaca', '')}<br>
        🌡️ {row.get('Temperatur (°C)', 'N/A')}°C<br>
        💧 {row.get('Kelembapan (%)', 'N/A')}%<br>
        🌬️ {row.get('Kecepatan Angin (m/s)', 'N/A')} m/s<br>
        🌧️ {row.get('Curah Hujan (mm)', '0')} mm
        """
        folium.Marker(
            location=[lat, lon],
            popup=popup_html,
            tooltip=row['Lokasi'],
            icon=folium.Icon(color="blue", icon="cloud")
        ).add_to(m)

st_data = st_folium(m, width=1200, height=600)

st.markdown("---")
st.caption("Data cuaca real-time berdasarkan OpenWeather API. Dibuat oleh [esferrohman].")
