import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
from pytz import timezone

# Konfigurasi halaman
st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")

# CSS kustom
st.markdown("""
    <style>
        .weather-icon {
            text-align: center;
            margin: 0 auto;
            display: block;
        }
        .weather-desc {
            text-align: center;
            font-size: 1.5rem;
            font-weight: bold;
            margin-top: 10px;
        }
        .metric-box {
            padding: 15px;
            border-radius: 10px;
            background: #f0f2f6;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# Konfigurasi data
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF_6ZosMvgQQAAqDtKFXluP1Ad4wMnk4jYUVHQd6bc0NRRFBd4f4uc2euorAq98ua8uDP_1hls2AtN/pub?output=csv"
LOKASI = ["Bitung", "Cikupa", "Balaraja Timur", "Balaraja Barat", "Cikande", 
          "Ciujung", "Serang Timur", "Serang Barat", "Cilegon Timur", "Cilegon Barat", "Merak"]

@st.cache_data(ttl=300)
def load_data():
    try:
        df = pd.read_csv(DATA_URL)
        df['Update Terakhir'] = pd.to_datetime(df['Update Terakhir'], format='%d/%m/%Y %H:%M:%S')
        return df
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        st.stop()

# Sidebar
with st.sidebar:
    st.image("Logo_MMS.png" if os.path.exists("Logo_MMS.png") else "", width=200)
    st.title("Pengaturan")
    
    selected_loc = st.selectbox("Pilih Lokasi", LOKASI)
    selected_period = st.selectbox("Pilih Periode", ["Hari ini", "Kemarin"])
    show_map = st.checkbox("Tampilkan Peta", True)

# Konten utama
def main_content():
    df = load_data()
    
    # Filter data
    today = pd.Timestamp.now(tz=timezone('Asia/Jakarta')).date()
    target_date = today if selected_period == "Hari ini" else today - pd.Timedelta(days=1)
    
    data = df[(df['Lokasi'] == selected_loc) & 
              (df['Update Terakhir'].dt.date == target_date)]
    
    if data.empty:
        st.warning(f"Tidak ada data untuk {selected_loc} pada {selected_period}")
        return
    
    latest = data.iloc[0]
    
    # Tampilkan ikon dan deskripsi cuaca
    st.markdown(f"""
        <div class="weather-icon">
            <img src="http://openweathermap.org/img/wn/{latest['Ikon']}@2x.png" width=100>
            <div class="weather-desc">{latest['Deskripsi Cuaca']}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Metrik cuaca
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='metric-box'>🌡️ Temperatur: {} °C</div>".format(latest.get('Temperatur', 'N/A')), unsafe_allow_html=True)
        st.markdown("<div class='metric-box'>💧 Kelembapan: {} %</div>".format(latest.get('Kelembapan', 'N/A')), unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='metric-box'>🌬️ Angin: {} m/s</div>".format(latest.get('Kecepatan Angin', 'N/A')), unsafe_allow_html=True)
        st.markdown("<div class='metric-box'>🌧️ Hujan: {} mm</div>".format(latest.get('Curah Hujan', 'N/A')), unsafe_allow_html=True)
    
    # Peta
    if show_map and pd.notna(latest.get('Koordinat')):
        try:
            lat, lon = map(float, latest['Koordinat'].split(','))
            m = folium.Map(location=[lat, lon], zoom_start=13)
            folium.Marker([lat, lon], tooltip=selected_loc).add_to(m)
            st_folium(m, width=700, height=400)
        except:
            st.warning("Format koordinat tidak valid")
    
    # Grafik histori
    if len(data) > 1:
        st.subheader(f"Tren {selected_period}")
        data = data.set_index('Update Terakhir')
        st.line_chart(data[['Temperatur', 'Kelembapan', 'Curah Hujan']])

# Jalankan aplikasi
if __name__ == "__main__":
    main_content()
    st.markdown("---")
    st.caption("© 2023 Dashboard Cuaca - esferrohman")
