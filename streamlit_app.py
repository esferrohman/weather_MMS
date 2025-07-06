import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")

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

summary_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"

@st.cache_data(ttl=600)
def load_summary(url):
    df = pd.read_csv(url)

    if 'Update Terakhir (WIB)' in df.columns:
        df['Update Terakhir (WIB)'] = pd.to_datetime(
            df['Update Terakhir (WIB)'],
            format='%d/%m/%Y %H:%M:%S',
            errors='coerce'
        )
    else:
        st.error("Kolom 'Update Terakhir (WIB)' tidak ditemukan!")
        st.stop()

    if 'Curah Hujan (mm)' in df.columns:
        df['Curah Hujan (mm)'] = df['Curah Hujan (mm)'].astype(str).str.replace(',', '.', regex=False)
        df['Curah Hujan (mm)'] = pd.to_numeric(df['Curah Hujan (mm)'], errors='coerce')

    return df

try:
    df_summary = load_summary(summary_url)
except Exception as e:
    st.error(f"Gagal memuat data: {e}")
    st.stop()

df_summary = df_summary.sort_values('Update Terakhir (WIB)', ascending=False)

lokasi_order = [
    "Bitung", "Cikupa", "Balaraja Timur", "Balaraja Barat", "Cikande",
    "Ciujung", "Serang Timur", "Serang Barat", "Cilegon Timur", "Cilegon Barat", "Merak"
]

lokasi_tersedia = df_summary['Lokasi'].dropna().unique()
lokasi_urut = [loc for loc in lokasi_order if loc in lokasi_tersedia]

with st.sidebar:
    st.image("Logo_MMS.png", use_container_width=True)
    st.title("Dashboard Cuaca")

st.subheader("Kondisi Cuaca Terkini")
data_lainnya_df = df_summary.drop_duplicates('Lokasi').set_index('Lokasi')
selected_location = None
cols = st.columns(len(lokasi_urut))
for idx, loc_name in enumerate(lokasi_urut):
    if loc_name in data_lainnya_df.index:
        row = data_lainnya_df.loc[loc_name]
        icon_code = str(row.get('Ikon', '') or '')
        loc_label = loc_name.replace(" ", "\n")
        with cols[idx]:
            if icon_code:
                icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
                st.image(icon_url, use_container_width=True)
            # Hanya tombol sebagai teks, tidak ada keterangan lain
            if st.button(loc_label, key=f"btn-{loc_name}"):
                selected_location = loc_name

# Tren gabungan curah hujan semua lokasi
st.subheader("📈 Tren Curah Hujan Hari Ini (Gabungan Seluruh Lokasi)")
df_hari_ini = df_summary[df_summary['Update Terakhir (WIB)'].dt.date == pd.Timestamp.now().date()]
if not df_hari_ini.empty:
    df_hari_ini = df_hari_ini.copy()
    df_hari_ini['Jam'] = df_hari_ini['Update Terakhir (WIB)'].dt.floor('H')
    df_hari_ini['Curah Hujan (mm)'] = pd.to_numeric(df_hari_ini['Curah Hujan (mm)'], errors='coerce')
    if df_hari_ini['Curah Hujan (mm)'].notna().any():
        df_tren = df_hari_ini.groupby('Jam')['Curah Hujan (mm)'].sum().dropna()
        if not df_tren.empty:
            st.line_chart(df_tren)
        else:
            st.info("Belum ada data curah hujan hari ini.")
    else:
        st.info("Data curah hujan tidak tersedia.")
else:
    st.info("Belum ada data cuaca untuk hari ini dari semua lokasi.")

lokasi = selected_location if selected_location else lokasi_urut[0]

df_hist_lokasi = df_summary[df_summary['Lokasi'] == lokasi]
data_terbaru = df_hist_lokasi.iloc[0]

waktu_update = data_terbaru.get('Update Terakhir (WIB)', None)
if pd.notnull(waktu_update):
    st.markdown(
        f"<p style='font-size:0.9em; color:#333;'>🕒 Data terakhir diperbarui:<br><b>{waktu_update.strftime('%d %B %Y %H:%M WIB')}</b></p>",
        unsafe_allow_html=True
    )

if pd.notnull(data_terbaru['Update Terakhir (WIB)']):
    tanggal_terbaru = data_terbaru['Update Terakhir (WIB)'].date()
    df_hist_lokasi = df_hist_lokasi[df_hist_lokasi['Update Terakhir (WIB)'].dt.date == tanggal_terbaru]

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
        st.markdown(
            f"""
            <div style='text-align:center;'>
                <img src="{icon_url}" style="width:100%; max-width:300px; margin-bottom:0.2em;" />
                <p class='deskripsi-cuaca'>{data_terbaru.get('Deskripsi Cuaca', '')}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.write("Tidak ada ikon cuaca tersedia.")

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
    if any_chart:
        csv_data = df_hist_lokasi.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Download Data Histori Hari Ini (CSV)",
            data=csv_data,
            file_name=f"{lokasi}_histori_cuaca_hari_ini.csv",
            mime="text/csv"
        )
    else:
        st.info("Kolom tren tidak ditemukan.")
else:
    st.info("Belum ada cukup data histori untuk hari ini.")

st.markdown("---")
st.caption("📊 Dashboard Cuaca Real-Time | Dibuat oleh [esferrohman].")
