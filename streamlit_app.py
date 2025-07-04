import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")
st.title("🌦️ Dashboard Cuaca Tol Tangerang-Merak")

csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"

try:
    df = pd.read_csv(csv_url)
except Exception as e:
    st.error(f"Gagal mengambil data dari Google Sheets CSV: {e}")
    st.stop()

# Deteksi kolom lokasi dan kode koordinat
if "Lokasi" not in df.columns or "Kode Koordinat" not in df.columns:
    st.error("Kolom 'Lokasi' dan 'Kode Koordinat' tidak ditemukan di data CSV!")
    st.dataframe(df)
    st.stop()

lokasi_pilihan = st.selectbox("📍 Pilih Lokasi", df["Lokasi"].unique())
lokasi_data = df[df["Lokasi"] == lokasi_pilihan].iloc[0]

col1, col2 = st.columns([2, 1])

with col1:
    st.header(f"📊 Data Cuaca di {lokasi_pilihan}")
    st.metric("🌡️ Temperatur (°C)", lokasi_data.get('Temperatur (°C)', 'N/A'))
    st.metric("💧 Kelembapan (%)", lokasi_data.get('Kelembapan (%)', 'N/A'))
    st.metric("🌬️ Kecepatan Angin (m/s)", lokasi_data.get('Kecepatan Angin (m/s)', 'N/A'))
    st.metric("🌧️ Curah Hujan (mm)", lokasi_data.get('Curah Hujan (mm)', 'N/A'))
    st.write(f"**📝 Deskripsi Cuaca:** {lokasi_data.get('Deskripsi Cuaca', 'N/A')}")

with col2:
    icon_code = lokasi_data.get('Ikon', '')
    if isinstance(icon_code, str) and icon_code != '':
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
        st.image(icon_url, caption="Ikon Cuaca dari OpenWeather", use_container_width=True)
    else:
        st.write("Tidak ada ikon cuaca tersedia.")

# Peta interaktif dengan folium
try:
    latlon = lokasi_data["Kode Koordinat"].split(",")
    lat, lon = float(latlon[0]), float(latlon[1])

    st.header("🗺️ Peta Lokasi")

    m = folium.Map(location=[lat, lon], zoom_start=12)
    folium.Marker(
        [lat, lon],
        tooltip=f"{lokasi_pilihan}: {lokasi_data.get('Deskripsi Cuaca', 'N/A')}",
        icon=folium.Icon(color="blue", icon="cloud")
    ).add_to(m)

    st_data = st_folium(m, width=700, height=500)

except Exception as e:
    st.warning(f"Tidak dapat menampilkan peta: {e}")

st.markdown("---")
st.caption("Data cuaca real-time berdasarkan OpenWeather API. Dibuat oleh [esferrohman].")
