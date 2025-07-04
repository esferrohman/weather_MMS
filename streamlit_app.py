import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")
st.title("🌦️ Dashboard Cuaca Tol Tangerang-Merak")

# URL CSV Summary (data terkini per lokasi)
csv_summary_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"

try:
    df = pd.read_csv(csv_summary_url)
except Exception as e:
    st.error(f"Gagal mengambil data Summary dari Google Sheets CSV: {e}")
    st.stop()

# Otomatis deteksi kolom lokasi
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

with col2:
    icon_code = lokasi_data.get('Ikon', '')
    if isinstance(icon_code, str) and icon_code != '':
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
        st.image(icon_url, use_container_width=True)
        # Letakkan deskripsi cuaca di bawah ikon, tanpa teks "Deskripsi Cuaca"
        deskripsi = lokasi_data.get('Deskripsi Cuaca', 'N/A')
        st.markdown(f"### {deskripsi.capitalize()}")
    else:
        st.write("Tidak ada ikon cuaca tersedia.")

# ======== BAGIAN TREN CUACA ========
# URL CSV Archive (riwayat data sepanjang hari)
csv_archive_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?gid=0&single=true&output=csv"

try:
    df_archive = pd.read_csv(csv_archive_url, parse_dates=["Update Terakhir (WIB)"])
except Exception as e:
    st.error(f"Gagal mengambil data Archive dari Google Sheets CSV: {e}")
    st.stop()

df_lokasi = df_archive[df_archive["Lokasi"] == lokasi]

if df_lokasi.empty:
    st.warning("Tidak ada data historis untuk lokasi ini.")
else:
    st.subheader(f"📈 Tren Cuaca Hari Ini di {lokasi}")
    
    chart_temp = alt.Chart(df_lokasi).mark_line(point=True).encode(
        x=alt.X('Update Terakhir (WIB):T', title='Waktu'),
        y=alt.Y('Temperatur (°C):Q', title='Temperatur (°C)'),
        tooltip=['Update Terakhir (WIB):T', 'Temperatur (°C):Q']
    ).properties(title='Perubahan Temperatur')

    st.altair_chart(chart_temp, use_container_width=True)
    
    chart_humidity = alt.Chart(df_lokasi).mark_line(point=True, color='green').encode(
        x=alt.X('Update Terakhir (WIB):T', title='Waktu'),
        y=alt.Y('Kelembapan (%):Q', title='Kelembapan (%)'),
        tooltip=['Update Terakhir (WIB):T', 'Kelembapan (%):Q']
    ).properties(title='Perubahan Kelembapan')

    st.altair_chart(chart_humidity, use_container_width=True)

    # Keterangan waktu update terakhir
    last_update = df_lokasi["Update Terakhir (WIB)"].max()
    st.info(f"📅 Data terakhir diperbarui pada: **{last_update} WIB**")

st.markdown("---")
st.caption("Data cuaca real-time berdasarkan OpenWeather API. Dibuat oleh [esferrohman].")
