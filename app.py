import streamlit as st
from loader import load_summary
from utils import format_waktu_update
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")

# Styling
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

# Load Data
SUMMARY_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"

try:
    df_summary = load_summary(SUMMARY_URL)
except Exception as e:
    st.error(f"Gagal memuat data: {e}")
    st.stop()

# Urutkan data
df_summary = df_summary.sort_values(['Lokasi', 'Update Terakhir (WIB)'], ascending=[True, False])

# Sidebar
with st.sidebar:
    st.image("Logo_MMS.png", use_container_width=True)
    st.title("Dashboard Cuaca")
    
    lokasi_order = [
        "Bitung", "Cikupa", "Balaraja Timur", "Balaraja Barat", "Cikande",
        "Ciujung", "Serang Timur", "Serang Barat", "Cilegon Timur", "Cilegon Barat", "Merak"
    ]
    
    lokasi_tersedia = df_summary['Lokasi'].dropna().unique()
    lokasi_urut = [loc for loc in lokasi_order if loc in lokasi_tersedia]
    
    lokasi = st.selectbox("📍 Pilih Lokasi", lokasi_urut)

# Data lokasi terpilih
df_hist_lokasi = df_summary[df_summary['Lokasi'] == lokasi].sort_values('Update Terakhir (WIB)', ascending=False)
data_terbaru = df_hist_lokasi.iloc[0]

# Tampilkan waktu update
waktu_update = data_terbaru.get('Update Terakhir (WIB)', None)
if pd.notnull(waktu_update):
    st.sidebar.markdown(
        f"<p style='font-size:0.9em; color:#333;'>🕒 Update terakhir:<br><b>{format_waktu_update(waktu_update)}</b></p>",
        unsafe_allow_html=True
    )

# Cuaca terkini semua lokasi
st.subheader("📍 Kondisi Cuaca Terkini")
data_lainnya_df = df_summary.sort_values('Update Terakhir (WIB)', ascending=False).drop_duplicates('Lokasi').set_index('Lokasi')
lokasi_lain_urut = [loc for loc in lokasi_order if loc in data_lainnya_df.index]

cols = st.columns(len(lokasi_lain_urut))
for idx, loc_name in enumerate(lokasi_lain_urut):
    row = data_lainnya_df.loc[loc_name]
    icon_code = str(row.get('Ikon', '') or '')
    curah_hujan = row.get('Curah Hujan (mm)', 0)
    bg_style = "background-color:#ffe6e6; padding:4px; border-radius:8px;" if pd.notnull(curah_hujan) and curah_hujan > 0 else ""

    with cols[idx]:
        st.markdown(f"<div style='text-align:center; font-size:0.9em; {bg_style}'>{loc_name}</div>", unsafe_allow_html=True)
        if icon_code:
            icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
            st.image(icon_url, use_column_width=True)

# Detail lokasi terpilih
st.header(f"📊 Cuaca Terkini di {lokasi}")
col1, col2 = st.columns([2, 1])
with col1:
    st.metric("🌡️ Temperatur (°C)", data_terbaru.get('Temperatur (°C)', 'N/A'))
    st.metric("💧 Kelembapan (%)", data_terbaru.get('Kelembapan (%)', 'N/A'))
    st.metric("🌬️ Angin (m/s)", data_terbaru.get('Kecepatan Angin (m/s)', 'N/A'))
    st.metric("🌧️ Curah Hujan (mm)", data_terbaru.get('Curah Hujan (mm)', 'N/A'))

with col2:
    icon_code = str(data_terbaru.get('Ikon', '') or '')
    if icon_code:
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
        st.markdown(
            f"""
            <div style='text-align:center;'>
                <img src="{icon_url}" style="width:100%; max-width:300px; margin-bottom:0.2em;" />
                <p class='deskripsi-cuaca'>{data_terbaru.get('Deskripsi Cuaca', '')}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

# Peta
kode_koordinat = data_terbaru.get('Kode Koordinat', '')
if isinstance(kode_koordinat, str) and "," in kode_koordinat:
    try:
        lat_str, lon_str = kode_koordinat.split(",")
        lat, lon = float(lat_str.strip()), float(lon_str.strip())
        m = folium.Map(location=[lat, lon], zoom_start=13)
        folium.Marker([lat, lon], tooltip=lokasi, icon=folium.Icon(color="blue", icon="cloud")).add_to(m)
        st_folium(m, width=700, height=400)
    except Exception as e:
        st.warning(f"Koordinat tidak valid: {e}")
else:
    st.warning("Koordinat tidak valid untuk lokasi ini.")

# Grafik tren historis (pakai expander untuk lazy load)
df_hist_lokasi = df_hist_lokasi[df_hist_lokasi['Update Terakhir (WIB)'].dt.date == data_terbaru['Update Terakhir (WIB)'].date()]
if len(df_hist_lokasi) > 1:
    with st.expander(f"📈 Tren Cuaca Hari Ini di {lokasi}"):
        df_plot = df_hist_lokasi.set_index('Update Terakhir (WIB)')
        for col, label in [
            ("Curah Hujan (mm)", "🌧️ Curah Hujan"),
            ("Temperatur (°C)", "🌡️ Temperatur"),
            ("Kelembapan (%)", "💧 Kelembapan")
        ]:
            if col in df_plot.columns:
                st.write(label)
                st.line_chart(df_plot[[col]])
        st.download_button(
            "💾 Download Data Hari Ini (CSV)",
            df_hist_lokasi.to_csv(index=False).encode('utf-8'),
            file_name=f"{lokasi}_cuaca_hari_ini.csv",
            mime="text/csv"
        )
else:
    st.info("Belum ada cukup data histori untuk hari ini.")

st.markdown("---")
st.caption("📊 Dashboard Cuaca Real-Time | Dibuat oleh [esferrohman].")
