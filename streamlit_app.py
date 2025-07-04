import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")
st.title("🌦️ Dashboard Cuaca Tol Tangerang-Merak")

csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"

try:
    df = pd.read_csv(csv_url)
except Exception as e:
    st.error(f"Gagal mengambil data dari Google Sheets CSV: {e}")
    st.stop()

# Validasi kolom minimal
wajib = ["Lokasi", "Temperatur (°C)", "Kelembapan (%)", "Kecepatan Angin (m/s)", "Curah Hujan (mm)", "Deskripsi Cuaca", "Ikon", "Kode Koordinat"]
missing = [k for k in wajib if k not in df.columns]
if missing:
    st.error(f"Kolom berikut tidak ditemukan di data CSV: {', '.join(missing)}")
    st.dataframe(df)
    st.stop()

lokasi = st.selectbox("📍 Pilih Lokasi", df['Lokasi'].unique())
lokasi_data = df[df['Lokasi'] == lokasi].iloc[0]

col1, col2 = st.columns([2, 1])

with col1:
    st.header(f"📊 Data Cuaca di {lokasi}")
    st.metric("🌡️ Temperatur (°C)", lokasi_data.get('Temperatur (°C)', 0))
    st.metric("💧 Kelembapan (%)", lokasi_data.get('Kelembapan (%)', 0))
    st.metric("🌬️ Kecepatan Angin (m/s)", lokasi_data.get('Kecepatan Angin (m/s)', 0))
    st.metric("🌧️ Curah Hujan (mm)", lokasi_data.get('Curah Hujan (mm)', 0))

with col2:
    icon_code = str(lokasi_data.get('Ikon', ''))
    if icon_code:
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
        st.image(icon_url, use_container_width=True)
    st.caption(lokasi_data.get('Deskripsi Cuaca', ''))

# Peta interaktif
st.header(f"🗺️ Lokasi: {lokasi}")
koordinat_str = str(lokasi_data.get('Kode Koordinat', ''))
if "," in koordinat_str:
    try:
        lat_str, lon_str = koordinat_str.split(',')
        lat, lon = float(lat_str.strip()), float(lon_str.strip())
        st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))
    except Exception as e:
        st.warning(f"Koordinat tidak valid: {koordinat_str} ({e})")
else:
    st.warning("Koordinat tidak ditemukan atau format tidak sesuai.")

st.markdown("---")
st.caption("Data cuaca real-time berdasarkan OpenWeather API. Dibuat oleh [esferrohman].")
