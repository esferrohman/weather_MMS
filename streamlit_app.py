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
        p.deskripsi-cuaca {
            text-align: center;
            font-size: 2em !important;
            margin: 0.5em 0;
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

# Standardisasi nama kolom
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
        
        # Standardisasi nama kolom
        df = df.rename(columns=lambda x: x.strip())  # Hilangkan spasi di nama kolom
        df.columns = [COLUMN_NAMES.get(col.lower().replace(' ', '_'), col) 
                    for col in df.columns]
        
        # Validasi kolom wajib
        mandatory_cols = [COLUMN_NAMES['update_terakhir'], 
                         COLUMN_NAMES['lokasi'], 
                         COLUMN_NAMES['ikon'], 
                         COLUMN_NAMES['deskripsi']]
        
        missing_cols = [col for col in mandatory_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Kolom wajib tidak ditemukan: {', '.join(missing_cols)}")
            st.stop()

        # Konversi tipe data
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

def render_sidebar(lokasi_urut):
    with st.sidebar:
        st.markdown("<div style='text-align: center; margin-bottom: 20px;'>", unsafe_allow_html=True)
        if os.path.exists("Logo_MMS.png"):
            st.image("Logo_MMS.png", use_column_width=True)
        else:
            st.warning("Logo tidak ditemukan.")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.title("Dashboard Cuaca")
        selected_location = st.selectbox(
            "Pilih Lokasi", 
            lokasi_urut,
            key='location_selector'
        )
        selected_period = st.selectbox(
            "Pilih Periode Data", 
            ["Hari ini", "Kemarin"],
            key='period_selector'
        )
    return selected_location, selected_period

def render_summary_chart(df_summary, selected_period):
    st.subheader(f"📈 Tren Curah Hujan ({selected_period}) - Gabungan Seluruh Lokasi")
    wib_tz = timezone('Asia/Jakarta')
    today_wib = pd.Timestamp.now(tz=wib_tz).date()
    filter_date = today_wib if selected_period == "Hari ini" else today_wib - pd.Timedelta(days=1)

    df_filtered = df_summary[
        df_summary[COLUMN_NAMES['update_terakhir']].dt.date == filter_date
    ]

    if not df_filtered.empty:
        df_filtered = df_filtered.copy()
        df_filtered['Jam'] = df_filtered[COLUMN_NAMES['update_terakhir']].dt.floor('H')
        
        if COLUMN_NAMES['curah_hujan'] in df_filtered.columns:
            df_tren = df_filtered.groupby('Jam')[COLUMN_NAMES['curah_hujan']].sum().dropna()
            
            if not df_tren.empty:
                st.line_chart(df_tren)
                
                # Download data tren gabungan
                csv_tren = df_tren.reset_index().rename(
                    columns={"Jam": "Jam WIB", 
                            COLUMN_NAMES['curah_hujan']: "Total Curah Hujan (mm)"}
                ).to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="💾 Download Data Tren Gabungan (CSV)",
                    data=csv_tren,
                    file_name=f"tren_gabungan_{selected_period.replace(' ', '_').lower()}.csv",
                    mime="text/csv",
                    key='download_summary'
                )
            else:
                st.info("Tidak ada data curah hujan pada periode ini.")
        else:
            st.info("Kolom curah hujan tidak tersedia.")
    else:
        st.info("Belum ada data cuaca pada periode ini dari semua lokasi.")

def render_selected_location(df_summary, selected_period, selected_location):
    wib_tz = timezone('Asia/Jakarta')
    today_wib = pd.Timestamp.now(tz=wib_tz).date()
    filter_date = today_wib if selected_period == "Hari ini" else today_wib - pd.Timedelta(days=1)

    df_hist_lokasi = df_summary[
        (df_summary[COLUMN_NAMES['lokasi']] == selected_location) &
        (df_summary[COLUMN_NAMES['update_terakhir']].dt.date == filter_date)
    ]

    if df_hist_lokasi.empty:
        st.error(f"Tidak ada data untuk lokasi '{selected_location}' pada periode {selected_period}.")
        return

    data_terbaru = df_hist_lokasi.iloc[0]

    # Tampilkan informasi update terakhir
    waktu_update = data_terbaru.get(COLUMN_NAMES['update_terakhir'], None)
    if pd.notnull(waktu_update):
        st.markdown(
            f"<p style='font-size:0.9em; color:#333;'>🕒 Data terakhir diperbarui: "
            f"<br><b>{waktu_update.strftime('%d %B %Y %H:%M WIB')}</b></p>",
            unsafe_allow_html=True
        )

    st.header(f"📊 Cuaca {selected_period} di {selected_location}")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        # Tampilkan metrics cuaca
        st.metric(
            "🌡️ Temperatur (°C)", 
            data_terbaru.get(COLUMN_NAMES['temperatur'], 'N/A')
        )
        st.metric(
            "💧 Kelembapan (%)", 
            data_terbaru.get(COLUMN_NAMES['kelembapan'], 'N/A')
        )
        st.metric(
            "🌬️ Kecepatan Angin (m/s)", 
            data_terbaru.get(COLUMN_NAMES['kecepatan_angin'], 'N/A')
        )
        st.metric(
            "🌧️ Curah Hujan (mm)", 
            data_terbaru.get(COLUMN_NAMES['curah_hujan'], 'N/A')
        )

    with col2:
        # Tampilkan ikon cuaca
        icon_code = str(data_terbaru.get(COLUMN_NAMES['ikon'], '') or ''
        if len(icon_code) >= 2:
            icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
            st.markdown(
                f"""
                <div style='text-align:center;'>
                    <img src="{icon_url}" style="width:100%; max-width:300px; margin-bottom:0.2em;" />
                    <p class='deskripsi-cuaca'>{data_terbaru.get(COLUMN_NAMES['deskripsi'], '')}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.write("Tidak ada ikon cuaca tersedia.")

    # Tampilkan peta lokasi
    kode_koordinat = data_terbaru.get(COLUMN_NAMES['koordinat'], '')
    if isinstance(kode_koordinat, str) and "," in kode_koordinat:
        try:
            lat_str, lon_str = kode_koordinat.split(",")
            lat, lon = float(lat_str.strip()), float(lon_str.strip())
            m = folium.Map(location=[lat, lon], zoom_start=14)
            folium.Marker(
                [lat, lon], 
                tooltip=selected_location, 
                icon=folium.Icon(color="blue", icon="cloud")
            ).add_to(m)
            st_folium(m, width=700, height=400)
        except Exception as e:
            st.warning(f"Koordinat tidak valid: {e}")
    else:
        st.warning("Koordinat tidak valid untuk lokasi ini.")

    # Tampilkan tren histori jika ada data cukup
    if len(df_hist_lokasi) > 1:
        st.subheader(f"📈 Tren Histori Cuaca {selected_period} di {selected_location}")
        df_plot = df_hist_lokasi.set_index(COLUMN_NAMES['update_terakhir'])
        
        param_list = [
            (COLUMN_NAMES['curah_hujan'], "🌧️ Curah Hujan"),
            (COLUMN_NAMES['temperatur'], "🌡️ Temperatur"),
            (COLUMN_NAMES['kelembapan'], "💧 Kelembapan")
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
                file_name=f"{selected_location}_histori_cuaca_{selected_period.replace(' ', '_').lower()}.csv",
                mime="text/csv",
                key=f'download_{selected_location}'
            )
        else:
            st.info("Kolom tren tidak ditemukan.")
    else:
        st.info("Belum ada cukup data histori untuk periode ini.")

def render_footer():
    st.markdown("---")
    st.caption("📊 Dashboard Cuaca Real-Time | Dibuat oleh [esferrohman]")

# ======= MAIN ========
def main():
    try:
        df_summary = load_summary(SUMMARY_URL)
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        st.stop()

    lokasi_tersedia = df_summary[COLUMN_NAMES['lokasi']].dropna().unique()
    lokasi_urut = [loc for loc in LOKASI_ORDER if loc in lokasi_tersedia]

    selected_location, selected_period = render_sidebar(lokasi_urut)
    render_summary_chart(df_summary, selected_period)
    render_selected_location(df_summary, selected_period, selected_location)
    render_footer()

if __name__ == "__main__":
    main()
