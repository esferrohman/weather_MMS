import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")
st.title("🌦️ Dashboard Cuaca Tol Tangerang-Merak")

# CSV Summary (untuk select lokasi)
csv_url_summary = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"
# CSV Archive (untuk tren cuaca)
csv_url_archive = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"

try:
    df_summary = pd.read_csv(csv_url_summary)
except Exception as e:
    st.error(f"Gagal mengambil data Summary dari Google Sheets CSV: {e}")
    st.stop()

# Debug: tampilkan kolom yang terbaca dari summary
st.write("✅ Kolom Summary CSV:", df_summary.columns.tolist())

# Pilih kolom lokasi secara otomatis
kolom_lokasi = None
for kandidat in ["Lokasi", "Gerbang"]:
    if kandidat in df_summary.columns:
        kolom_lokasi = kandidat
        break

if kolom_lokasi is None:
    st.error("Kolom 'Lokasi' atau 'Gerbang' tidak ditemukan di data Summary!")
    st.dataframe(df_summary)
    st.stop()

lokasi = st.selectbox("📍 Pilih Lokasi", df_summary[kolom_lokasi].unique())
lokasi_data = df_summary[df_summary[kolom_lokasi] == lokasi].iloc[0]

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
        st.image(icon_url, caption=lokasi_data.get('Deskripsi Cuaca', ''), use_container_width=True)
    else:
        st.write(lokasi_data.get('Deskripsi Cuaca', ''))

st.markdown("---")

# Ambil data Archive untuk tren
try:
    df_archive = pd.read_csv(csv_url_archive, parse_dates=["Update Terakhir (WIB)"])
    st.write("✅ Kolom Archive CSV:", df_archive.columns.tolist())
except Exception as e:
    st.error(f"Gagal mengambil data Archive dari Google Sheets CSV: {e}")
    st.stop()

# Filter data archive untuk lokasi terpilih
df_lokasi = df_archive[df_archive['Lokasi'] == lokasi]

if df_lokasi.empty:
    st.warning("Belum ada data arsip untuk lokasi ini.")
else:
    # Plot tren temperatur
    fig = px.line(df_lokasi, x="Update Terakhir (WIB)", y="Temperatur (°C)",
                  title=f"📈 Tren Temperatur di {lokasi}", markers=True)
    st.plotly_chart(fig, use_container_width=True)
    # Keterangan waktu update terakhir
    last_update = df_lokasi["Update Terakhir (WIB)"].max()
    st.info(f"⏰ Data terakhir diperbarui: {last_update.strftime('%d-%m-%Y %H:%M:%S')} WIB")

st.caption("Data cuaca real-time berdasarkan OpenWeather API. Dibuat oleh [esferrohman].")
