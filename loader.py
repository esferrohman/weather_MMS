import pandas as pd
import streamlit as st

@st.cache_data(ttl=600, show_spinner="📥 Mengambil data cuaca...")
def load_summary(url):
    df = pd.read_csv(url)
    
    if 'Update Terakhir (WIB)' in df.columns:
        df['Update Terakhir (WIB)'] = pd.to_datetime(df['Update Terakhir (WIB)'], errors='coerce')
    if 'Curah Hujan (mm)' in df.columns:
        df['Curah Hujan (mm)'] = pd.to_numeric(
            df['Curah Hujan (mm)'].astype(str).str.replace(',', '.', regex=False),
            errors='coerce',
            downcast='float'
        )
    return df
