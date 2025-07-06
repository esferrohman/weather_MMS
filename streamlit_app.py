import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from pytz import timezone

# Konfigurasi halaman
st.set_page_config(
    page_title="Cuaca Tol Tangerang-Merak",
    layout="centered",
    initial_sidebar_state="expanded"
)

# CSS kustom
st.markdown("""
    <style>
        .block-container {padding-top: 2rem; padding-bottom: 2rem;}
        .weather-header {text-align: center; margin-bottom: 1.5rem;}
        [data-testid="stSidebar"] {background: #f8f9fa; padding: 2rem 1rem;}
        .weather-metric {font-size: 1.1rem; margin-bottom: 0.5rem;}
    </style>
""", unsafe_allow_html=True)

# Data configuration
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"
LOCATIONS = ["Bitung", "Cikupa", "Balaraja Timur", "Balaraja Barat", "Cikande",
             "Ciujung", "Serang Timur", "Serang Barat", "Cilegon Timur", "Cilegon Barat", "Merak"]

@st.cache_data(ttl=300)
def load_weather_data():
    try:
        df = pd.read_csv(DATA_URL)
        required_cols = ['Lokasi', 'Update Terakhir', 'Ikon', 'Deskripsi Cuaca', 'Koordinat']
        for col in required_cols:
            if col not in df.columns:
                st.error(f"Kolom '{col}' tidak ditemukan di data sumber.")
                st.stop()
        df['Waktu'] = pd.to_datetime(df['Update Terakhir'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        return df.dropna(subset=['Waktu'])
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

# Sidebar controls
with st.sidebar:
    st.title("Pengaturan Cuaca")
    location = st.selectbox("📍 Lokasi Stasiun Cuaca", LOCATIONS, index=0, key="loc_select")
    period = st.radio("📅 Periode Data", ["Hari Ini", "Kemarin"], index=0, key="period_select")
    show_map = st.toggle("🗺️ Tampilkan Peta Lokasi", value=True, key="map_toggle")

# Main content
def display_weather():
    df = load_weather_data()
    
    today = pd.Timestamp.now(tz=timezone('Asia/Jakarta')).date()
    target_date = today if period == "Hari Ini" else today - pd.Timedelta(days=1)
    
    station_data = df[(df['Lokasi'] == location) & (df['Waktu'].dt.date == target_date)]
    
    if station_data.empty:
        st.warning(f"Data tidak tersedia untuk {location} pada {period.lower()}.")
        return
    
    # Urutkan agar data terbaru di atas
    station_data = station_data.sort_values('Waktu', ascending=False)
    latest = station_data.iloc[0]
    
    # Gunakan ikon default jika kosong
    icon_code = latest['Ikon'] if pd.notna(latest['Ikon']) and latest['Ikon'].strip() else '01d'
    
    st.markdown(f"""
        <div class="weather-header">
            <img src="http://openweathermap.org/img/wn/{icon_code}@2x.png" width=120>
            <h3>{latest.get('Deskripsi Cuaca', 'N/A')}</h3>
            <p><small>Terakhir update: {latest['Waktu'].strftime('%H:%M WIB')}</small></p>
        </div>
    """, unsafe_allow_html=True)
    
    cols = st.columns(2)
    metrics = [
        ("🌡️ Temperatur", f"{latest.get('Temperatur', 'N/A')}°C"),
        ("💧 Kelembapan", f"{latest.get('Kelembapan', 'N/A')}%"),
        ("🌬️ Kecepatan Angin", f"{latest.get('Kecepatan Angin', 'N/A')} m/s"),
        ("🌧️ Curah Hujan", f"{latest.get('Curah Hujan', 'N/A')} mm")
    ]
    
    for i, (label, value) in enumerate(metrics):
        cols[i % 2].markdown(f"<div class='weather-metric'>{label} {value}</div>", unsafe_allow_html=True)
    
    coords = latest.get('Koordinat')
    if show_map and coords and isinstance(coords, str) and coords.strip():
        try:
            lat, lon = map(float, coords.strip().split(','))
            m = folium.Map(location=[lat, lon], zoom_start=13)
            folium.Marker([lat, lon], tooltip=location).add_to(m)
            st_folium(m, width=400, height=300)
        except Exception as e:
            st.warning(f"Format koordinat tidak valid: {e}")

if __name__ == "__main__":
    display_weather()
