import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import numpy as np

st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")

# ---------- Style ----------
st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
p.deskripsi-cuaca { text-align:center; font-size:2em !important; margin:0.5em 0; }
</style>
""", unsafe_allow_html=True)

# ---------- URL Data ----------
SUMMARY_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"

# ---------- Load & clean data ----------
@st.cache_data(ttl=300)
def load_summary(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    if 'Update Terakhir (WIB)' in df.columns:
        df['Update Terakhir (WIB)'] = pd.to_datetime(df['Update Terakhir (WIB)'], errors='coerce')
    numeric_cols = ['Temperatur (°C)', 'Kelembapan (%)', 'Kecepatan Angin (m/s)', 'Curah Hujan (mm)']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False).replace({'': np.nan})
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

try:
    df_summary = load_summary(SUMMARY_URL)
except Exception as e:
    st.error(f"Gagal mengambil data: {e}")
    st.stop()

df_summary = df_summary.sort_values(['Lokasi', 'Update Terakhir (WIB)'], ascending=[True, False])

# ---------- Sidebar ----------
with st.sidebar:
    st.image("Logo_MMS.png", use_container_width=True)
    st.title("Dashboard Cuaca")

    if st.button("🔄 Refresh Data Sekarang"):
        st.cache_data.clear()
        st.rerun()

    lokasi_order = ["Bitung", "Cikupa", "Balaraja Timur", "Balaraja Barat", "Cikande",
                    "Ciujung", "Serang Timur", "Serang Barat", "Cilegon Timur", "Cilegon Barat", "Merak"]

    lokasi_tersedia = df_summary['Lokasi'].dropna().unique()
    lokasi_urut = [loc for loc in lokasi_order if loc in lokasi_tersedia]

    lokasi = st.selectbox("📍 Pilih Lokasi", lokasi_urut)

    df_hist_lokasi = df_summary[df_summary['Lokasi'] == lokasi].sort_values('Update Terakhir (WIB)', ascending=False)
    data_terbaru = df_hist_lokasi.iloc[0]

    waktu_update = data_terbaru.get('Update Terakhir (WIB)')
    if pd.notnull(waktu_update):
        st.markdown(
            f"<p style='font-size:0.9em;'>🕒 Data terakhir diperbarui:<br>"
            f"<b>{waktu_update.strftime('%d %B %Y %H:%M WIB')}</b></p>",
            unsafe_allow_html=True
        )
    else:
        st.warning("⛔ Kolom waktu tidak terbaca.")

# ---------- Kondisi Lokasi Lain ----------
st.subheader("📍 Kondisi Cuaca Terkini")
data_lain = df_summary.sort_values('Update Terakhir (WIB)', ascending=False).drop_duplicates('Lokasi').set_index('Lokasi')
lokasi_lain_urut = [loc for loc in lokasi_order if loc in data_lain.index]

if lokasi_lain_urut:
    cols = st.columns(len(lokasi_lain_urut))
    for idx, loc_name in enumerate(lokasi_lain_urut):
        row = data_lain.loc[loc_name]
        curah = row.get('Curah Hujan (mm)', 0)
        bg = "background-color:#ffe6e6; padding:4px; border-radius:8px;" if pd.notnull(curah) and curah > 0 else ""
        with cols[idx]:
            st.markdown(f"<div style='text-align:center; font-size:0.9em; {bg}'>{loc_name}</div>", unsafe_allow_html=True)
            icon_code = str(row.get('Ikon', '') or '')
            if icon_code:
                st.image(f"http://openweathermap.org/img/wn/{icon_code}@2x.png", use_column_width=True)
else:
    st.info("Tidak ada data kondisi lokasi yang tersedia.")

# ---------- Filter histori hari ini ----------
if pd.notnull(data_terbaru['Update Terakhir (WIB)']):
    tanggal_terbaru = data_terbaru['Update Terakhir (WIB)'].date()
    df_hist_lokasi_hariini = df_hist_lokasi[df_hist_lokasi['Update Terakhir (WIB)'].dt.date == tanggal_terbaru]
else:
    df_hist_lokasi_hariini = df_hist_lokasi.copy()

# ---------- Metrik & Deskripsi ----------
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
        st.markdown(
            f"<div style='text-align:center;'>"
            f"<img src='http://openweathermap.org/img/wn/{icon_code}@4x.png' style='width:100%; max-width:300px;'/>"
            f"<p class='deskripsi-cuaca'>{data_terbaru.get('Deskripsi Cuaca', '')}</p>"
            f"</div>", unsafe_allow_html=True)
    else:
        st.write("Tidak ada ikon cuaca.")

# ---------- Peta Lokasi ----------
koor = data_terbaru.get('Kode Koordinat', '')
if isinstance(koor, str) and "," in koor:
    try:
        lat, lon = map(float, koor.split(","))
        if np.isfinite(lat) and np.isfinite(lon):
            m = folium.Map(location=[lat, lon], zoom_start=14)
            popup_txt = f"{lokasi}<br>{data_terbaru.get('Deskripsi Cuaca', '')}"
            folium.Marker([lat, lon], tooltip=lokasi, popup=popup_txt, icon=folium.Icon(color="blue", icon="cloud")).add_to(m)
            st_folium(m, width=700, height=400)
            st.markdown("<div style='margin-top:-1em;'></div>", unsafe_allow_html=True)
        else:
            st.warning("Koordinat tidak valid.")
    except Exception as e:
        st.warning(f"Koordinat tidak valid: {e}")
else:
    st.warning("Koordinat tidak tersedia untuk lokasi ini.")

# ---------- Grafik Tren Harian ----------
if len(df_hist_lokasi_hariini) > 1:
    st.subheader(f"📈 Tren Histori Cuaca Hari Ini di {lokasi}")
    df_plot = df_hist_lokasi_hariini.set_index('Update Terakhir (WIB)')
    param_map = {
        "Curah Hujan (mm)": "🌧️ Curah Hujan",
        "Temperatur (°C)":  "🌡️ Temperatur",
        "Kelembapan (%)":   "💧 Kelembapan"
    }
    chart_exists = False
    for col, title in param_map.items():
        if col in df_plot.columns:
            with st.expander(title):
                st.line_chart(df_plot[[col]])
                chart_exists = True
    if not chart_exists:
        st.info("Kolom tren numerik tidak ditemukan.")
    else:
        csv_bytes = df_hist_lokasi_hariini.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Download Data Histori Hari Ini (CSV)",
                           data=csv_bytes,
                           file_name=f"{lokasi}_histori_cuaca_hari_ini.csv",
                           mime="text/csv")
else:
    st.info("Belum ada cukup data histori hari ini untuk grafik tren.")

st.markdown("---")
st.caption("📊 Dashboard Cuaca Real‑Time | Dibuat oleh esferrohman.")
