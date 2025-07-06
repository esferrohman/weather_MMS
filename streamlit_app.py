import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from pytz import timezone

# Konfigurasi halaman
st.set_page_config(
    page_title="Cuaca Tol Tangerang-Merak",
    layout="centered",  # Layout lebih compact
    initial_sidebar_state="expanded"
)

# CSS kustom untuk tampilan minimalis
st.markdown("""
    <style>
        /* Hapus padding yang tidak perlu */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Pusatkan ikon cuaca */
        .weather-header {
            text-align: center;
            margin-bottom: 1.5rem;
        }
        
        /* Style untuk sidebar */
        [data-testid="stSidebar"] {
            background: #f8f9fa;
            padding: 2rem 1rem;
        }
        
        /* Style untuk metrik cuaca */
        .weather-metric {
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        }
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
        df['Waktu'] = pd.to_datetime(df['Update Terakhir'], format='%d/%m/%Y %H:%M:%S')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

# Sidebar controls
with st.sidebar:
    st.title("Pengaturan Cuaca")
    
    # Pilih lokasi
    location = st.selectbox(
        "📍 Lokasi Stasiun Cuaca",
        LOCATIONS,
        index=0,
        key="loc_select"
    )
    
    # Pilih periode
    period = st.radio(
        "📅 Periode Data",
        ["Hari Ini", "Kemarin"],
        index=0,
        key="period_select"
    )
    
    # Toggle peta
    show_map = st.toggle(
        "🗺️ Tampilkan Peta Lokasi",
        value=True,
        key="map_toggle"
    )

# Main content
def display_weather():
    df = load_weather_data()
    
    # Filter data
    today = pd.Timestamp.now(tz=timezone('Asia/Jakarta')).date()
    target_date = today if period == "Hari Ini" else today - pd.Timedelta(days=1)
    
    station_data = df[(df['Lokasi'] == location) & 
                     (df['Waktu'].dt.date == target_date)]
    
    if station_data.empty:
        st.warning(f"Data tidak tersedia untuk {location} pada {period.lower()}")
        return
    
    latest = station_data.iloc[0]
    
    # Tampilan utama - hanya ikon dan deskripsi
    st.markdown(f"""
        <div class="weather-header">
            <img src="http://openweathermap.org/img/wn/{latest['Ikon']}@2x.png" width=120>
            <h3>{latest['Deskripsi Cuaca']}</h3>
            <p><small>Terakhir update: {latest['Waktu'].strftime('%H:%M WIB')}</small></p>
        </div>
    """, unsafe_allow_html=True)
    
    # Grid metrik cuaca
    cols = st.columns(2)
    metrics = [
        ("🌡️ Temperatur", f"{latest.get('Temperatur', 'N/A')}°C"),
        ("💧 Kelembapan", f"{latest.get('Kelembapan', 'N/A')}%"),
        ("🌬️ Kecepatan Angin", f"{latest.get('Kecepatan Angin', 'N/A')} m/s"),
        ("🌧️ Curah Hujan", f"{latest.get('Curah Hujan', 'N/A')} mm")
    ]
    
    for i, (icon, value) in enumerate(metrics):
        cols[i%2].markdown(f"""
            <div class="weather-metric">
                {icon} {value}
            </div>
        """, unsafe_allow_html=True)
    
    # Tampilkan peta jika diaktifkan
    if show_map and pd.notna(latest.get('Koordinat')):
        try:
            lat, lon = map(float, latest['Koordinat'].split(','))
            m = folium.Map(location=[lat, lon], zoom_start=13)
            folium.Marker([lat, lon], tooltip=location).add_to(m)
            st_folium(m, width=400, height=300)
        except:
            st.warning("Format koordinat tidak valid")

# Run the app
if __name__ == "__main__":
    display_weather()
