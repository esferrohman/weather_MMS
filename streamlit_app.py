import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Test", layout="wide")

st.write("🚨 Ini kode terbaru berjalan 🚨")

# Dummy data
data = {
    "Lokasi": ["A", "B", "A", "B"],
    "Update Terakhir (WIB)": ["2025-07-01 12:00", "2025-07-01 12:00", "2025-07-02 08:00", "2025-07-02 08:00"],
    "Temperatur (°C)": [25, 26, 27, 28],
    "Deskripsi Cuaca": ["cerah", "berawan", "hujan", "kabut"]
}
df = pd.DataFrame(data)
df["Update Terakhir (WIB)"] = pd.to_datetime(df["Update Terakhir (WIB)"])
df = df.sort_values(["Lokasi", "Update Terakhir (WIB)"], ascending=[True, False])

with st.sidebar:
    lokasi_unik = df["Lokasi"].unique()
    lokasi = st.selectbox("📍 Pilih Lokasi", lokasi_unik)

df_hist = df[df["Lokasi"] == lokasi]
data_terbaru = df_hist.iloc[0]

st.header(f"📊 Cuaca Terbaru di {lokasi}")
st.metric("🌡️ Temperatur (°C)", data_terbaru["Temperatur (°C)"])
st.markdown(
    f"<p style='text-align: center; font-size: 2em; font-weight: bold;'>{data_terbaru['Deskripsi Cuaca']}</p>",
    unsafe_allow_html=True
)
st.info(f"🕒 Data terakhir diperbarui: {data_terbaru['Update Terakhir (WIB)']}")
