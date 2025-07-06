import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")

# CSS untuk deskripsi cuaca besar
st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: 'Segoe UI', sans-serif;
        }
        p.deskripsi-cuaca {
            text-align: center;
            font-size: 2em !important;
            margin: 0.5em 0;
        }
    </style>
""", unsafe_allow_html=True)

# Load data dari Google Sheets
summary_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"

@st.cache_data(ttl=600)
def load_summary(url):
    return pd.read_csv(url)

try:
    df_summary = load_summary(summary_url)
except Exception as e:
    st.error(f"Gagal mengambil data Summary: {e}")
    st.stop()

# Konversi kolom update ke datetime
df_summary['Update Terakhir (WIB)'] = pd.to_datetime(df_summary['Update Terakhir (WIB)'], errors='coerce')

# Urutkan supaya baris terbaru di atas
df_summary = df_summary.sort_values(['Lokasi', 'Update Terakhir (WIB)'], ascending=[True, False])

# Sidebar: logo, dropdown urut manual, info waktu update
with st.sidebar:
    st.image("Logo_MMS.png", use_container_width=True)
    st.title("Dashboard Cuaca")
    
    # Urutan lokasi sesuai permintaan
    lokasi_order = [
        "Bitung", "Cikupa", "Balaraja Timur", "Balaraja Barat", "Cikande",
        "Ciujung", "Serang Timur", "Serang Barat", "Cilegon Timur", "Cilegon Barat", "Merak"
    ]
    
    # Ambil lokasi unik dari data
    lokasi_tersedia = df_summary['Lokasi'].dropna().unique()
    
    # Susun sesuai urutan permintaan, hanya lokasi yang ada di data
    lokasi_urut = [loc for loc in lokasi_order if loc in lokasi_tersedia]
    
    lokasi = st.selectbox("📍 Pilih Lokasi", lokasi_urut)
    
    # Ambil histori & data terbaru lokasi terpilih
    df_hist_lokasi = df_summary[df_summary['Lokasi'] == lokasi].sort_values('Update Terakhir (WIB)', ascending=False)
    data_terbaru = df_hist_lokasi.iloc[0]
    
    # Info update di bawah dropdown
    waktu_update = data_terbaru.get('Update Terakhir (WIB)', None)
    if pd.notnull(waktu_update):
        st.markdown(
            f"<p style='font-size:0.9em; color:#333;'>🕒 Data terakhir diperbarui:<br><b>{waktu_update.strftime('%d %B %Y %H:%M WIB')}</b></p>",
            unsafe_allow_html=True
        )

# Filter histori hanya untuk tanggal yang sama dengan data terbaru
if pd.notnull(data_terbaru['Update Terakhir (WIB)']):
    tanggal_terbaru = data_terbaru['Update Terakhir (WIB)'].date()
    df_hist_lokasi = df_hist_lokasi[df_hist_lokasi['Update Terakhir (WIB)'].dt.date == tanggal_terbaru]

# Header & metrik utama
st.header(f"📊 Cuaca Terkini di {lokasi}")
col1, col2 = st.columns([2, 1])
with col1:
    st.metric("🌡️ Temperatur (°C)", data_terbaru.get('Temperatur (°C)', 'N/A'))
    st.metric("💧 Kelembapan (%)", data_terbaru.get('Kelembapan (%)', 'N/A'))
    st.metric("🌬️ Kecepatan Angin (m/s)", data_terbaru.get('Kecepatan Angin (m/s)', 'N/A'))
    st.metric("🌧️ Curah Hujan (mm)", data_terbaru.get('Curah Hujan (mm)', 'N/A'))

with col2:
    icon_code = str(data_terbaru.get('Ikon', '') or '')
    if icon_code:
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
        st.image(icon_url, use_container_width=True)
        st.markdown(
            f"<p class='deskripsi-cuaca'>{data_terbaru.get('Deskripsi Cuaca', '')}</p>",
            unsafe_allow_html=True
        )
    else:
        st.write("Tidak ada ikon cuaca tersedia.")

# Peta interaktif
kode_koordinat = data_terbaru.get('Kode Koordinat', '')
if isinstance(kode_koordinat, str) and "," in kode_koordinat:
    try:
        lat_str, lon_str = kode_koordinat.split(",")
        lat, lon = float(lat_str.strip()), float(lon_str.strip())
        m = folium.Map(location=[lat, lon], zoom_start=14)
        folium.Marker([lat, lon], tooltip=lokasi, icon=folium.Icon(color="blue", icon="cloud")).add_to(m)
        st_folium(m, width=700, height=400)
    except Exception as e:
        st.warning(f"Koordinat tidak valid: {e}")
else:
    st.warning("Koordinat tidak valid untuk lokasi ini.")

# Kondisi cuaca lokasi lainnya
st.subheader("📍 Kondisi Cuaca Lokasi Lainnya")

# Ambil data terbaru per lokasi lain dan buat dict {lokasi: row}
data_lainnya_df = (
    df_summary[df_summary['Lokasi'] != lokasi]
    .sort_values('Update Terakhir (WIB)', ascending=False)
    .drop_duplicates('Lokasi')
    .set_index('Lokasi')
)

# Susun data lainnya sesuai urutan dropdown
lokasi_lain_urut = [loc for loc in lokasi_order if loc != lokasi and loc in data_lainnya_df.index]

if lokasi_lain_urut:
    cols = st.columns(len(lokasi_lain_urut))
    for idx, loc_name in enumerate(lokasi_lain_urut):
        row = data_lainnya_df.loc[loc_name]
        icon_code = str(row.get('Ikon', '') or '')
        curah_hujan = row.get('Curah Hujan (mm)', 0)

        # Highlight jika ada hujan
        bg_style = "background-color:#ffe6e6; padding:4px; border-radius:8px;" if pd.notnull(curah_hujan) and curah_hujan > 0 else ""

        with cols[idx]:
            st.markdown(
                f"<div style='text-align:center; font-size:0.9em; {bg_style}'>{loc_name}</div>",
                unsafe_allow_html=True
            )
            if icon_code:
                icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
                st.image(icon_url, use_container_width=True)
else:
    st.info("Tidak ada data kondisi lokasi lainnya yang tersedia.")

# Grafik histori tren per parameter + satu tombol download CSV
if len(df_hist_lokasi) > 1:
    st.subheader(f"📈 Tren Histori Cuaca Hari Ini di {lokasi}")
    df_plot = df_hist_lokasi.set_index('Update Terakhir (WIB)')
    
    param_list = [
        ("Curah Hujan (mm)", "🌧️ Curah Hujan"),
        ("Temperatur (°C)", "🌡️ Temperatur"),
        ("Kelembapan (%)", "💧 Kelembapan")
    ]
    
    any_chart = False
    for col, title in param_list:
        if col in df_plot.columns:
            st.write(title)
            st.line_chart(df_plot[[col]])
            any_chart = True
            
    if not any_chart:
        st.info("Kolom tren numerik yang dipilih tidak ditemukan.")
    else:
        # Tombol download CSV semua histori hari ini
        csv_data = df_hist_lokasi.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Download Data Histori Hari Ini (CSV)",
            data=csv_data,
            file_name=f"{lokasi}_histori_cuaca_hari_ini.csv",
            mime="text/csv"
        )
else:
    st.info("Belum ada cukup data histori untuk hari ini untuk menampilkan grafik tren.")

st.markdown("---")
st.caption("📊 Dashboard Cuaca Real-Time | Dibuat oleh [esferrohman].")
