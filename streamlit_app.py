import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
from pytz import timezone

st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")

st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: 'Segoe UI', sans-serif;
        }
        .weather-icon-container {
            text-align: center;
            margin: 1em 0;
        }
        .weather-description {
            font-size: 1.5em !important;
            margin: 0.2em 0;
            font-weight: bold;
        }
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
        }
    </style>
""", unsafe_allow_html=True)

SUMMARY_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"

LOKASI_ORDER = [
    "Bitung", "Cikupa", "Balaraja Timur", "Balaraja Barat", "Cikande",
    "Ciujung", "Serang Timur", "Serang Barat", "Cilegon Timur", "Cilegon Barat", "Merak"
]

COLUMN_NAMES = {
    'update_terakhir': 'Update Terakhir (WIB)',
    'lokasi': 'Lokasi',
    'ikon': 'Ikon',
    'deskripsi': 'Deskripsi Cuaca',
    'temperatur': 'Temperatur (°C)',
    'kelembapan': 'Kelembapan (%)',
    'kecepatan_angin': 'Kecepatan Angin (m/s)',
    'curah_hujan': 'Curah Hujan (mm)',
    'koordinat': 'Kode Koordinat'
}

@st.cache_data(ttl=600)
def load_summary(url):
    try:
        df = pd.read_csv(url)
        df = df.rename(columns=lambda x: x.strip())
        df.columns = [COLUMN_NAMES.get(col.lower().replace(' ', '_'), col) 
                     for col in df.columns]
        
        mandatory_cols = [COLUMN_NAMES['update_terakhir'], 
                         COLUMN_NAMES['lokasi'], 
                         COLUMN_NAMES['ikon'], 
                         COLUMN_NAMES['deskripsi']]
        
        missing_cols = [col for col in mandatory_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Kolom wajib tidak ditemukan: {', '.join(missing_cols)}")
            st.stop()

        df[COLUMN_NAMES['update_terakhir']] = pd.to_datetime(
            df[COLUMN_NAMES['update_terakhir']],
            format='%d/%m/%Y %H:%M:%S',
            errors='coerce'
        )
        
        if COLUMN_NAMES['curah_hujan'] in df.columns:
            df[COLUMN_NAMES['curah_hujan']] = (
                df[COLUMN_NAMES['curah_hujan']]
                .astype(str)
                .str.replace(',', '.', regex=False)
                .replace('', pd.NA)
            )
            df[COLUMN_NAMES['curah_hujan']] = pd.to_numeric(
                df[COLUMN_NAMES['curah_hujan']], 
                errors='coerce'
            )

        return df.sort_values(COLUMN_NAMES['update_terakhir'], ascending=False)
    
    except Exception as e:
        st.error(f"Gagal memuat data: {str(e)}")
        st.stop()

def render_sidebar():
    with st.sidebar:
        st.markdown("<div style='text-align: center; margin-bottom: 20px;'>", unsafe_allow_html=True)
        if os.path.exists("Logo_MMS.png"):
            st.image("Logo_MMS.png", use_column_width=True)
        else:
            st.warning("Logo tidak ditemukan.")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.title("Pengaturan Cuaca")
        
        # Dropdown pemilihan lokasi
        selected_location = st.selectbox(
            "📍 Pilih Lokasi", 
            LOKASI_ORDER,
            key='location_selector'
        )
        
        # Dropdown pemilihan periode
        selected_period = st.selectbox(
            "📅 Pilih Periode", 
            ["Hari ini", "Kemarin"],
            key='period_selector'
        )
        
        # Checkbox untuk tampilkan peta
        show_map = st.checkbox(
            "🗺️ Tampilkan Peta Lokasi",
            value=True,
            key='map_visibility'
        )
        
        return selected_location, selected_period, show_map

def render_current_weather(data):
    """Menampilkan ikon dan deskripsi cuaca terkini"""
    icon_code = str(data.get(COLUMN_NAMES['ikon'], '') or '')
    description = data.get(COLUMN_NAMES['deskripsi'], '')
    
    st.markdown(
        f"""
        <div class="weather-icon-container">
            <img src="http://openweathermap.org/img/wn/{icon_code}@2x.png" 
                 style="height:100px; margin-bottom:0.5em;">
            <p class="weather-description">{description}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_weather_details(data, show_map=True):
    """Menampilkan detail cuaca"""
    cols = st.columns(3)
    
    with cols[0]:
        st.metric(
            "🌡️ Temperatur", 
            f"{data.get(COLUMN_NAMES['temperatur'], 'N/A')} °C"
        )
        st.metric(
            "💧 Kelembapan", 
            f"{data.get(COLUMN_NAMES['kelembapan'], 'N/A')} %"
        )
    
    with cols[1]:
        st.metric(
            "🌬️ Kecepatan Angin", 
            f"{data.get(COLUMN_NAMES['kecepatan_angin'], 'N/A')} m/s"
        )
        st.metric(
            "🌧️ Curah Hujan", 
            f"{data.get(COLUMN_NAMES['curah_hujan'], 'N/A')} mm"
        )
    
    with cols[2]:
        waktu_update = data.get(COLUMN_NAMES['update_terakhir'], None)
        if pd.notnull(waktu_update):
            st.markdown(
                f"<div style='margin-top:1em;'><b>🕒 Update Terakhir:</b><br>"
                f"{waktu_update.strftime('%d %B %Y %H:%M WIB')}</div>",
                unsafe_allow_html=True
            )
    
    # Tampilkan peta jika diaktifkan
    if show_map:
        kode_koordinat = data.get(COLUMN_NAMES['koordinat'], '')
        if isinstance(kode_koordinat, str) and "," in kode_koordinat:
            try:
                lat_str, lon_str = kode_koordinat.split(",")
                lat, lon = float(lat_str.strip()), float(lon_str.strip())
                m = folium.Map(location=[lat, lon], zoom_start=14)
                folium.Marker(
                    [lat, lon], 
                    tooltip=data.get(COLUMN_NAMES['lokasi'], ''),
                    icon=folium.Icon(color="blue", icon="cloud")
                ).add_to(m)
                st_folium(m, width=700, height=300)
            except Exception as e:
                st.warning(f"Koordinat tidak valid: {e}")

def main():
    try:
        df_summary = load_summary(SUMMARY_URL)
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        st.stop()

    # Render sidebar dan dapatkan parameter
    selected_location, selected_period, show_map = render_sidebar()
    
    # Filter data berdasarkan pilihan
    wib_tz = timezone('Asia/Jakarta')
    today_wib = pd.Timestamp.now(tz=wib_tz).date()
    filter_date = today_wib if selected_period == "Hari ini" else today_wib - pd.Timedelta(days=1)
    
    df_filtered = df_summary[
        (df_summary[COLUMN_NAMES['lokasi']] == selected_location) &
        (df_summary[COLUMN_NAMES['update_terakhir']].dt.date == filter_date)
    ]
    
    if df_filtered.empty:
        st.warning(f"Tidak ada data untuk lokasi '{selected_location}' pada periode {selected_period}.")
        return
    
    data_terbaru = df_filtered.iloc[0]
    
    # Tampilan utama
    st.header(f"Kondisi Cuaca di {selected_location}")
    
    # 1. Tampilkan ikon dan deskripsi cuaca
    render_current_weather(data_terbaru)
    
    # 2. Tampilkan detail cuaca
    render_weather_details(data_terbaru, show_map)
    
    # 3. Tampilkan grafik histori jika ada data cukup
    if len(df_filtered) > 1:
        st.subheader(f"📈 Tren Historis {selected_period}")
        df_plot = df_filtered.set_index(COLUMN_NAMES['update_terakhir'])
        
        param_list = [
            (COLUMN_NAMES['curah_hujan'], "Curah Hujan (mm)"),
            (COLUMN_NAMES['temperatur'], "Temperatur (°C)"),
            (COLUMN_NAMES['kelembapan'], "Kelembapan (%)")
        ]
        
        for col, title in param_list:
            if col in df_plot.columns:
                st.line_chart(df_plot[[col]].rename(columns={col: title}))
    
    # Footer
    st.markdown("---")
    st.caption("📊 Dashboard Cuaca Real-Time | © 2023 esferrohman")

if __name__ == "__main__":
    main()
