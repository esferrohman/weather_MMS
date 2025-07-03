import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Cuaca Tol Tangerang-Merak", layout="wide")

sheet_url = "https://docs.google.com/spreadsheets/d/1pFMn_7LRET1x3vqKbGsBrFBrNjl3GQl_cDxvXyVTIHs/export?format=csv&gid=0"

st.title("Dashboard Cuaca Tol Tangerang-Merak")

try:
    df = pd.read_csv(sheet_url)
except Exception as e:
    st.error(f"Gagal mengambil data: {e}")
    st.stop()

st.subheader("Data Cuaca Terbaru")
st.dataframe(df)

lokasi = st.selectbox("Pilih Lokasi", df['Lokasi'].unique())
lokasi_data = df[df['Lokasi'] == lokasi].iloc[0]

st.write(f"**Lokasi:** {lokasi}")
st.metric("Temperatur (°C)", lokasi_data["Temperatur (°C)"])
st.metric("Kelembapan (%)", lokasi_data["Kelembapan (%)"])
st.metric("Kecepatan Angin (m/s)", lokasi_data["Kecepatan Angin (m/s)"])
st.metric("Curah Hujan (mm)", lokasi_data["Curah Hujan (mm)"])
st.write(f"**Deskripsi Cuaca:** {lokasi_data['Deskripsi Cuaca']}")

st.subheader("Grafik Temperatur Semua Lokasi")
st.bar_chart(df.set_index("Lokasi")["Temperatur (°C)"])

st.subheader("Grafik Curah Hujan Semua Lokasi")
st.bar_chart(df.set_index("Lokasi")["Curah Hujan (mm)"])
