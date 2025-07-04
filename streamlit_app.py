import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")

# Logo di sidebar
with st.sidebar:
    st.image("Logo_MMS.png", use_container_width=True)
    st.title("🌦️ Dashboard Cuaca")
    st.markdown("### Tol Tangerang-Merak")

# Ambil data summary CSV
summary_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"

try:
    df = pd.read_csv(summary_csv)
except Exception as e:
    st.error(f"Gagal mengambil data Summary CSV: {e}")
    st.stop()

expected_cols = [
    "Update Terakhir (WIB)", "Lokasi", "Temperatur (°C)", "Kelembapan (%)",
    "Kecepatan Angin (m/s)", "Curah Hujan (mm)", "Deskripsi Cuaca", "Ikon", "Kode Koordinat"
]
missing_cols = [col for col in expected_cols if col not in df.columns]
if missing_cols:
    st.error(f"Kolom hilang: {missing_cols}")
    st.dataframe(df)
    st.stop()

# Pilih lokasi di sidebar
lokasi = st.sidebar.selectbox("📍 Pilih Lokasi", df["Lokasi"].unique())
lokasi_data = df[df["Lokasi"] == lokasi].iloc[0]

# Judul halaman utama
st.header(f"📍 {lokasi}")

# Metrix & ikon
col1, col2 = st.columns([3, 1])
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
        st.markdown(f"<h4 style='text-align:center'>{lokasi_data['Deskripsi Cuaca'].capitalize()}</h4>", unsafe_allow_html=True)
    else:
        st.write("Tidak ada ikon cuaca.")

# Peta
st.subheader("🗺️ Peta Lokasi")
koordinat_str = lokasi_data["Kode Koordinat"]
try:
    lat, lon = map(float, koordinat_str.split(","))
    m = folium.Map(location=[lat, lon], zoom_start=12, control_scale=True)
    folium.Marker([lat, lon], tooltip=lokasi, popup=lokasi).add_to(m)
    st_folium(m, width="100%", height=500)
except Exception as e:
    st.error(f"Gagal membuat peta: {e}")

# Info update terakhir
update_terakhir = df["Update Terakhir (WIB)"].max()
st.info(f"📅 Data terakhir diperbarui: {update_terakhir}")

st.markdown("---")
st.caption("Data cuaca real-time berdasarkan OpenWeather API. Dibuat oleh [esferrohman].")
