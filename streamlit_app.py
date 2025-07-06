import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
from pytz import timezone, UTC, FixedOffset

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

SUMMARY_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"

LOKASI_ORDER = [
    "Bitung", "Cikupa", "Balaraja Timur", "Balaraja Barat", "Cikande",
    "Ciujung", "Serang Timur", "Serang Barat", "Cilegon Timur", "Cilegon Barat", "Merak"
]

@st.cache_data(ttl=600)
def load_summary(url):
    df = pd.read_csv(url)

    mandatory_cols = ['Update Terakhir (WIB)', 'Lokasi', 'Ikon', 'Deskripsi Cuaca']
    for col in mandatory_cols:
        if col not in df.columns:
            st.error(f"Kolom wajib '{col}' tidak ditemukan di data!")
            st.stop()

    df['Update Terakhir (WIB)'] = pd.to_datetime(
        df['Update Terakhir (WIB)'],
        format='%d/%m/%Y %H:%M:%S',
        errors='coerce'
    )

    if 'Curah Hujan (mm)' in df.columns:
        df['Curah Hujan (mm)'] = df['Curah Hujan (mm)'].astype(str).str.replace(',', '.', regex=False)
        df['Curah Hujan (mm)'] = pd.to_numeric(df['Curah Hujan (mm)'], errors='coerce')

    return df.sort_values('Update Terakhir (WIB)', ascending=False)

def render_sidebar(lokasi_urut):
    with st.sidebar:
        if os.path.exists("Logo_MMS.png"):
            st.image("Logo_MMS.png", use_container_width=True)
        else:
            st.warning("Logo tidak ditemukan.")
        st.title("Dashboard Cuaca")
        selected_location = st.selectbox("Pilih Lokasi", lokasi_urut)
        selected_period = st.selectbox("Pilih Periode Data", ["Hari ini", "Kemarin"])
    return selected_location, selected_period

def render_summary_chart(df_summary, selected_period):
    st.subheader(f"📈 Tren Curah Hujan ({selected_period}) - Gabungan Seluruh Lokasi")
    wib_tz = timezone('Asia/Jakarta')
    today_wib = pd.Timestamp.now(tz=wib_tz).date()
    if selected_period == "Hari ini":
        filter_date = today_wib
    else:  # Kemarin
        filter_date = today_wib - pd.Timedelta(days=1)

    df_filtered = df_summary[df_summary['Update Terakhir (WIB)'].dt.date == filter_date]

    if not df_filtered.empty:
        df_filtered = df_filtered.copy()
        df_filtered['Jam'] = df_filtered['Update Terakhir (WIB)'].dt.floor('H')
        df_tren = df_filtered.groupby('Jam')['Curah Hujan (mm)'].sum().dropna()
        if not df_tren.empty:
            st.line_chart(df_tren)
        else:
            st.info("Tidak ada data curah hujan pada periode ini.")
    else:
        st.info("Belum ada data cuaca pada periode ini dari semua lokasi.")

def render_selected_location(df_summary, lokasi, selected_period):
    wib_tz = timezone('Asia/Jakarta')
    today_wib = pd.Timestamp.now(tz=wib_tz).date()
    if selected_period == "Hari ini":
        filter_date = today_wib
    else:
        filter_date = today_wib - pd.Timedelta(days=1)

    df_hist_lokasi = df_summary[
        (df_summary['Lokasi'] == lokasi) &
        (df_summary['Update Terakhir (WIB)'].dt.date == filter_date)
    ]

    if df_hist_lokasi.empty:
        st.error(f"Tidak ada data untuk lokasi '{lokasi}' pada periode {selected_period}.")
        return

    data_terbaru = df_hist_lokasi.iloc[0]

    waktu_update = data_terbaru.get('Update Terakhir (WIB)', None)
    if pd.notnull(waktu_update):
        st.markdown(
            f"<p style='font-size:0.9em; color:#333;'>🕒 Data terakhir diperbarui:<br><b>{waktu_update.strftime('%d %B %Y %H:%M WIB')}</b></p>",
            unsafe_allow_html=True
        )

    st.header(f"📊 Cuaca {selected_period} di {lokasi}")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.metric("🌡️ Temperatur (°C)", data_terbaru.get('Temperatur (°C)', 'N/A'))
        st.metric("💧 Kelembapan (%)", data_terbaru.get('Kelembapan (%)', 'N/A'))
        st.metric("🌬️ Kecepatan Angin (m/s)", data_terbaru.get('Kecepatan Angin (m/s)', 'N/A'))
        st.metric("🌧️ Curah Hujan (mm)", data_terbaru.get('Curah Hujan (mm)', 'N/A'))

    with col2:
        icon_code = str(data_terbaru.get('Ikon', '') or '')
        if len(icon_code) >= 2:
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
        st.subheader(f"📈 Tren Histori Cuaca {selected_period} di {lokasi}")
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
                label="💾 Download Data Histori (CSV)",
                data=csv_data,
                file_name=f"{lokasi}_histori_cuaca_{selected_period.replace(' ', '_').lower()}.csv",
                mime="text/csv"
            )
        else:
            st.info("Kolom tren tidak ditemukan.")
    else:
        st.info("Belum ada cukup data histori untuk periode ini.")

def render_footer():
    st.markdown("---")
    st.caption("📊 Dashboard Cuaca Real-Time | Dibuat oleh [esferrohman].")

# ======= MAIN ========
try:
    df_summary = load_summary(SUMMARY_URL)
except Exception as e:
    st.error(f"Gagal memuat data: {e}")
    st.stop()

lokasi_tersedia = df_summary['Lokasi'].dropna().unique()
lokasi_urut = [loc for loc in LOKASI_ORDER if loc in lokasi_tersedia]

selected_location, selected_period = render_sidebar(lokasi_urut)
render_summary_chart(df_summary, selected_period)
render_selected_location(df_summary, selected_location, selected_period)
render_footer()
