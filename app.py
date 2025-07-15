import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import numpy as np

st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
p.deskripsi-cuaca { text-align:center; font-size:2em !important; margin:0.5em 0; }
</style>
""", unsafe_allow_html=True)

SUMMARY_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"

@st.cache_data(ttl=300)
def load_summary(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    if 'Update Terakhir (WIB)' in df.columns:
        df['Update Terakhir (WIB)'] = pd.to_datetime(
            df['Update Terakhir (WIB)'], format="%d/%m/%Y %H:%M:%S", errors='coerce'
        )
    numeric_cols = ['Temperatur (°C)', 'Kelembapan (%)', 'Kecepatan Angin (m/s)', 'Curah Hujan (mm)']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False).replace({'': np.nan})
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

@st.cache_data(ttl=300)
def get_akumulasi_harian(df):
    df = df.copy()
    df['Tanggal'] = df['Update Terakhir (WIB)'].dt.date
    return df.groupby(['Lokasi', 'Tanggal'])['Curah Hujan (mm)'].sum(min_count=1).reset_index()

@st.cache_data(ttl=300)
def get_histori_mingguan(df):
    df = df[df['Update Terakhir (WIB)'] >= pd.Timestamp.now() - pd.Timedelta(days=7)]
    df['Tanggal'] = df['Update Terakhir (WIB)'].dt.date
    return df.groupby('Tanggal')[['Curah Hujan (mm)', 'Temperatur (°C)', 'Kelembapan (%)']].mean()

try:
    df_summary = load_summary(SUMMARY_URL)
except Exception as e:
    st.error(f"Gagal mengambil data: {e}")
    st.stop()

df_summary = df_summary.sort_values(['Lokasi', 'Update Terakhir (WIB)'], ascending=[True, False])

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
        st.warning("⛔ Waktu tidak terbaca.")

# Ringkasan kondisi semua lokasi
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
                st.image(f"http://openweathermap.org/img/wn/{icon_code}@2x.png", use_container_width=True)

# Histori hari ini
if pd.notnull(data_terbaru['Update Terakhir (WIB)']):
    tanggal_terbaru = data_terbaru['Update Terakhir (WIB)'].date()
    df_hist_lokasi_hariini = df_hist_lokasi[df_hist_lokasi['Update Terakhir (WIB)'].dt.date == tanggal_terbaru]
else:
    df_hist_lokasi_hariini = df_hist_lokasi.copy()

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

# Peta lokasi
koor = data_terbaru.get('Kode Koordinat', '')
if isinstance(koor, str) and "," in koor:
    try:
        lat, lon = map(float, koor.split(","))
        m = folium.Map(location=[lat, lon], zoom_start=14)
        folium.Marker([lat, lon], tooltip=lokasi, icon=folium.Icon(color="blue", icon="cloud")).add_to(m)
        st_folium(m, width=700, height=400)
        st.markdown("<div style='margin-top:-1em;'></div>", unsafe_allow_html=True)
    except:
        st.warning("Koordinat tidak valid.")

# Grafik tren harian
if len(df_hist_lokasi_hariini) > 1:
    st.subheader(f"📈 Tren Cuaca Hari Ini di {lokasi}")
    df_plot = df_hist_lokasi_hariini.set_index('Update Terakhir (WIB)')
    for col, label in {
        "Curah Hujan (mm)": "🌧️ Curah Hujan",
        "Temperatur (°C)": "🌡️ Temperatur",
        "Kelembapan (%)": "💧 Kelembapan"
    }.items():
        if col in df_plot.columns:
            with st.expander(label):
                st.line_chart(df_plot[[col]])

# Akumulasi harian
st.subheader(f"📊 Akumulasi Curah Hujan Harian di {lokasi}")
akumulasi_df = get_akumulasi_harian(df_summary)
df_akumulasi_lokasi = akumulasi_df[akumulasi_df['Lokasi'] == lokasi]
if not df_akumulasi_lokasi.empty:
    df_akumulasi_lokasi = df_akumulasi_lokasi.set_index('Tanggal')
    st.bar_chart(df_akumulasi_lokasi['Curah Hujan (mm)'])
else:
    st.info("Tidak ada data akumulasi tersedia.")

# Rata-rata mingguan
st.subheader("📈 Rata-Rata Harian Semua Lokasi (7 Hari Terakhir)")
mingguan_df = get_histori_mingguan(df_summary)
if not mingguan_df.empty:
    st.line_chart(mingguan_df)
else:
    st.info("Data histori mingguan belum tersedia.")

st.markdown("---")
st.caption("📊 Dashboard Cuaca Real‑Time | Dibuat oleh esferrohman.")
