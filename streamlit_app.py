import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")

# Tambahkan custom CSS
st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: 'Segoe UI', sans-serif;
        }
        p.deskripsi-cuaca {
            text-align: center;
            font-size: 2em !important;
            font-weight: bold;
            margin: 0.5em 0;
        }
    </style>
""", unsafe_allow_html=True)

# Load data
summary_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"

@st.cache_data(ttl=600)
def load_summary(url):
    return pd.read_csv(url)

try:
    df_summary = load_summary(summary_url)
except Exception as e:
    st.error(f"Gagal mengambil data Summary: {e}")
    st.stop()

# Pastikan kolom waktu bertipe datetime
df_summary['Update Terakhir (WIB)'] = pd.to_datetime(df_summary['Update Terakhir (WIB)'], errors='coerce')

# Urutkan data terbaru ke atas
df_summary = df_summary.sort_values(['Lokasi', 'Update Terakhir (WIB)'], ascending=[True, False])

# Tampilkan logo & dropdown di sidebar
with st.sidebar:
    st.image("Logo_MMS.png", caption="PT MMS", use_container_width=True)
    st.title("Dashboard Cuaca")
    lokasi_unik = df_summary['Lokasi'].dropna().unique()
    lokasi = st.selectbox("📍 Pilih Lokasi", lokasi_unik)

# Filter histori untuk lokasi terpilih
df_lokasi_hist = df_summary[df_summary['Lokasi'] == lokasi].sort_values('Update Terakhir (WIB)', ascending=False)

# Ambil baris terbaru untuk lokasi
data_lokasi = df_lokasi_hist.iloc[0]

st.header(f"📊 Cuaca di {lokasi}")
col1, col2 = st.columns([2, 1])
with col1:
    st.metric("🌡️ Temperatur (°C)", data_lokasi.get('Temperatur (°C)', 'N/A'))
    st.metric("💧 Kelembapan (%)", data_lokasi.get('Kelembapan (%)', 'N/A'))
    st.metric("🌬️ Kecepatan Angin (m/s)", data_lokasi.get('Kecepatan Angin (m/s)', 'N/A'))
    st.metric("🌧️ Curah Hujan (mm)", data_lokasi.get('Curah Hujan (mm)', 'N/A'))

with col2:
    icon_code = str(data_lokasi.get('Ikon', '') or '')
    if icon_code != '':
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
        st.image(icon_url, use_container_width=True)
        st.markdown(
            f"<p class='deskripsi-cuaca'>{data_lokasi.get('Deskripsi Cuaca', '')}</p>",
            unsafe_allow_html=True
        )
    else:
        st.write("Tidak ada ikon cuaca tersedia.")

# Tampilkan peta interaktif
kode_koordinat = data_lokasi.get('Kode Koordinat', '')
if isinstance(kode_koordinat, str) and "," in kode_koordinat:
    try:
        lat_str, lon_str = kode_koordinat.split(",")
        lat, lon = float(lat_str.strip()), float(lon_str.strip())
        m = folium.Map(location=[lat, lon], zoom_start=14)
        folium.Marker([lat, lon], tooltip=f"{lokasi}", icon=folium.Icon(color="blue", icon="cloud")).add_to(m)
        st_folium(m, width=700, height=400)
    except Exception as e:
        st.warning(f"Koordinat tidak valid: {e}")
else:
    st.warning("Koordinat tidak valid untuk lokasi ini.")

# Info update terakhir
waktu_update = data_lokasi.get('Update Terakhir (WIB)', None)
if pd.notnull(waktu_update):
    st.info(f"🕒 Data terakhir diperbarui: {waktu_update}")

# Grafik histori tren
if len(df_lokasi_hist) > 1:
    st.subheader(f"📈 Tren Histori Cuaca di {lokasi}")
    df_plot = df_lokasi_hist.set_index('Update Terakhir (WIB)')
    cols_trend = ['Temperatur (°C)', 'Kelembapan (%)', 'Kecepatan Angin (m/s)', 'Curah Hujan (mm)']
    cols_trend = [col for col in cols_trend if col in df_plot.columns]
    if cols_trend:
        st.line_chart(df_plot[cols_trend])
    else:
        st.info("Kolom tren numerik tidak ditemukan.")
else:
    st.info("Belum ada data histori yang cukup untuk menampilkan grafik tren.")

st.markdown("---")
st.caption("📊 Dashboard Cuaca Real-Time | Dibuat oleh [esferrohman].")
