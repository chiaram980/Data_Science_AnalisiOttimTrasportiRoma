import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import io

# ================= Funzioni di caricamento con cache =================

@st.cache_data
def load_routes():
    return pd.read_csv("routes.txt", dtype=str, low_memory=False)

@st.cache_data
def load_trips():
    return pd.read_csv("trips.txt", dtype=str, low_memory=False)

@st.cache_data
def load_stops():
    return pd.read_csv("stops.txt", dtype=str, low_memory=False)

@st.cache_data
def load_stop_times():
    file_id = "1Qx7jVKObRN79CLJwIy9Jzh0VwJ2D9dWZ"
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(download_url, stream=True)
    response.raise_for_status()
    return pd.read_parquet(io.BytesIO(response.content))

@st.cache_data
def load_ottimizzazione():
    df1 = pd.read_csv("ottimizzazione_dashboard_20250325_112654.csv")
    df2 = pd.read_csv("ottimizzazione_dashboard_20250325_113839.csv")
    df1['fascia_oraria'] = "12-15"
    df2['fascia_oraria'] = "08-11"
    return pd.concat([df1, df2], ignore_index=True)

# ================= Dataset iniziale =================

data_fascia = pd.DataFrame({
    'route_id': [
        'Linea 73', 'Linea 664', 'Linea 107', 'Linea 107', 'Linea 64', 'Linea 063', 'Linea 058F', 'Linea 64',
        'Linea 990L', 'Linea 063', 'Linea 336', 'Linea 058F', 'Linea 716', 'Linea 338', 'Linea 338', 'Linea 762',
        'Linea 360', 'Linea 507', 'Linea 360', 'Linea 913', 'Linea 507', 'Linea 766', 'Linea 766', 'Linea 515'
    ],
    'hour': [
        13, 13, 14, 13, 14, 13, 14, 13, 14, 14, 13, 13, 13, 13, 14, 14,
        10, 9, 9, 9, 10, 10, 9, 10
    ],
    'delay': [
        521.16, 380.0, 346.0, 345.7, 272.2, 266.8, 261.5, 258.8, 249.4, 246.0, 237.4, 227.4, 218.0, 213.9, 207.5, 210.6,
        226.78, 221.07, 215.81, 210.61, 203.44, 202.92, 195.65, 192.29
    ],
    'extra_trips': [
        7, 5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        7, 3, 1, 1, 1, 1, 1, 1
    ]
})

data_fascia["week_range"] = data_fascia["hour"].apply(lambda x: "3-7 marzo" if x in [13, 14] else "10-14 febbraio")
data_fascia["hour"] = data_fascia["hour"].astype(str)
data_fascia['day_of_week'] = [
    'Lunedì', 'Lunedì', 'Martedì', 'Mercoledì', 'Martedì', 'Giovedì', 'Venerdì', 'Venerdì',
    'Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Lunedì', 'Martedì', 'Mercoledì',
    'Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Giovedì', 'Venerdì', 'Venerdì'
]

# ================== Titolo ==================

st.title("Dashboard Ritardi Trasporti Pubblici - Roma")

# ================== FILTRI SETTIMANALI ==================

st.sidebar.header("Filtri Ritardi Settimanali")
selected_week = st.sidebar.selectbox("Settimana:", sorted(data_fascia["week_range"].unique()))
selected_days = st.sidebar.multiselect("Giorni:", ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì'], default=['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì'])
selected_routes = st.sidebar.multiselect("Linee:", sorted(data_fascia['route_id'].unique()), default=sorted(data_fascia['route_id'].unique()))

data_settimanale = data_fascia[(data_fascia['week_range'] == selected_week) & (data_fascia['day_of_week'].isin(selected_days)) & (data_fascia['route_id'].isin(selected_routes))]

# ================== GRAFICI RITARDI ==================

st.subheader(f"Andamento dei ritardi nella settimana {selected_week}")
fig = px.line(data_settimanale, x='day_of_week', y='delay', color='route_id', markers=True)
st.plotly_chart(fig, use_container_width=True)
st.dataframe(data_settimanale.sort_values(by=['route_id', 'day_of_week']))

# ================== FILTRI OTTIMIZZAZIONE ==================

st.sidebar.header("Filtri Corse Ottimizzate")
df_opt_all = load_ottimizzazione()
df_opt_all['hour'] = df_opt_all['hour'].astype(str)
fasce = st.sidebar.multiselect("Fasce orarie:", df_opt_all['fascia_oraria'].unique(), default=list(df_opt_all['fascia_oraria'].unique()))
linee = st.sidebar.multiselect("Linee ottimizzate:", sorted(df_opt_all['route_id'].unique()), default=sorted(df_opt_all['route_id'].unique()))

ott_filt = df_opt_all[(df_opt_all['fascia_oraria'].isin(fasce)) & (df_opt_all['route_id'].isin(linee))]

st.subheader("Corse extra suggerite dal modello")
fig_opt = px.bar(ott_filt, x="route_id", y="extra_trips", color="fascia_oraria", barmode="group")
st.plotly_chart(fig_opt, use_container_width=True)
st.dataframe(ott_filt.sort_values(by="extra_trips", ascending=False))

# ================== MAPPA FERMATE RITARDI ==================

st.subheader("Mappa delle fermate associate alle corse selezionate (ritardi settimanali)")

try:
    routes = load_routes()
    trips = load_trips()
    stops = load_stops()
    stop_times = load_stop_times()

    corse = data_settimanale[['route_id', 'hour']].drop_duplicates().copy()
    corse['route_id_gtfs'] = corse['route_id'].str.replace("Linea ", "").str.strip()

    fermate_totali = pd.DataFrame()
    palette = px.colors.qualitative.Set2

    for idx, row in corse.iterrows():
        trips_match = trips[trips['route_id'] == row['route_id_gtfs']]
        if not trips_match.empty:
            trip_id = trips_match['trip_id'].iloc[0]
            stops_trip = stop_times[stop_times['trip_id'] == trip_id]
            stop_ids = stops_trip['stop_id'].unique()
            fermate_linea = stops[stops['stop_id'].isin(stop_ids)].copy()
            fermate_linea['route_id'] = row['route_id']
            colore = palette[idx % len(palette)]
            fermate_linea['color'] = colore
            fermate_totali = pd.concat([fermate_totali, fermate_linea], ignore_index=True)

    if not fermate_totali.empty:
        fermate_totali['stop_lat'] = fermate_totali['stop_lat'].astype(float)
        fermate_totali['stop_lon'] = fermate_totali['stop_lon'].astype(float)
        m = folium.Map(location=[fermate_totali['stop_lat'].mean(), fermate_totali['stop_lon'].mean()], zoom_start=12)
        for _, row in fermate_totali.iterrows():
            folium.CircleMarker(location=(row['stop_lat'], row['stop_lon']), radius=5, color=row['color'], fill=True, fill_color=row['color'], fill_opacity=0.8, tooltip=row['stop_name']).add_to(m)
        st_folium(m, width=700, height=500)
        st.dataframe(fermate_totali[['route_id', 'stop_name', 'stop_lat', 'stop_lon']].drop_duplicates().sort_values(by='route_id'))
    else:
        st.warning("Nessuna fermata trovata per le corse selezionate.")

except Exception as e:
    st.error(f"Errore nella costruzione della mappa: {e}")
