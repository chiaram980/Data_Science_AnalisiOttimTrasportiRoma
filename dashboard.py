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

# ================= Dati iniziali (dataset piccolo) =================

data_fascia = pd.DataFrame({
    'route_id': ['Linea 73', 'Linea 664', 'Linea 107', 'Linea 107', 'Linea 64', 'Linea 063',
                 'Linea 058F', 'Linea 64', 'Linea 990L', 'Linea 063', 'Linea 336', 'Linea 058F',
                 'Linea 716', 'Linea 338', 'Linea 338', 'Linea 762', 'Linea 360', 'Linea 507',
                 'Linea 360', 'Linea 913', 'Linea 507', 'Linea 766', 'Linea 766', 'Linea 515'],
    'hour': [13, 13, 14, 13, 14, 13, 14, 13, 14, 14, 13, 13, 13, 13, 14, 14, 10, 9, 9, 9, 10, 10, 9, 10],
    'delay': [521.16, 380.0, 346.0, 345.7, 272.2, 266.8, 261.5, 258.8, 249.4, 246.0,
              237.4, 227.4, 218.0, 213.9, 207.5, 210.6, 226.78, 221.07, 215.81, 210.61,
              203.44, 202.92, 195.65, 192.29],
    'extra_trips': [7, 5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 7, 3, 1, 1, 1, 1, 1, 1]
})

data_fascia["week_range"] = data_fascia["hour"].apply(lambda x: "3-7 marzo" if x in [13, 14] else "10-14 febbraio")
data_fascia["hour"] = data_fascia["hour"].astype(str)

data_fascia['day_of_week'] = [
    'Lunedì', 'Lunedì', 'Martedì', 'Mercoledì', 'Martedì', 'Giovedì', 'Venerdì', 'Venerdì',
    'Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Lunedì', 'Martedì', 'Mercoledì',
    'Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Giovedì', 'Venerdì', 'Venerdì'
]

# ================= Inizio della Dashboard =================

st.title("Dashboard Ritardi Trasporti Pubblici - Roma")

# Sidebar per i filtri
st.sidebar.header("Filtri")
selected_week = st.sidebar.selectbox("Seleziona la settimana:", sorted(data_fascia["week_range"].unique()))
selected_hours = st.sidebar.multiselect("Ore:", sorted(data_fascia['hour'].unique()), default=sorted(data_fascia['hour'].unique()))
selected_routes = st.sidebar.multiselect("Linee:", sorted(data_fascia['route_id'].unique()), default=sorted(data_fascia['route_id'].unique()))

# Filtro sui dati
filtered_data = data_fascia[(data_fascia['hour'].isin(selected_hours)) &
                            (data_fascia['route_id'].isin(selected_routes)) &
                            (data_fascia['week_range'] == selected_week)]

# Grafico ritardi medi
st.subheader(f"Ritardi medi per linea e ora - Settimana {selected_week}")
fig1 = px.bar(filtered_data, x="route_id", y="delay", color="hour", barmode="group",
              labels={"delay": "Ritardo medio (min)", "route_id": "Linea"})
st.plotly_chart(fig1, use_container_width=True)

# Heatmap corse extra
st.subheader("Heatmap delle corse extra")
pivot = filtered_data.pivot_table(index='route_id', columns='hour', values='extra_trips', fill_value=0)
fig2, ax2 = plt.subplots(figsize=(10, 6))
sns.heatmap(pivot, cmap='coolwarm', annot=True, fmt='g', ax=ax2)
st.pyplot(fig2)

# Scatter plot ritardi
st.subheader("Distribuzione dei ritardi medi")
fig3 = px.scatter(filtered_data, x="hour", y="delay", size="extra_trips", color="route_id",
                  labels={"delay": "Ritardo medio (min)", "hour": "Ora", "route_id": "Linea"})
st.plotly_chart(fig3, use_container_width=True)

# ================= Sezioni che caricano dati solo su richiesta =================

if st.checkbox("Visualizza fermate di una linea specifica"):
    try:
        routes = load_routes()
        trips = load_trips()
        stops = load_stops()
        stop_times = load_stop_times()

        route_ids = sorted(routes[(routes['agency_id'] == 'OP1') & (routes['route_type'] == '3')]['route_id'].unique())
        route_id_selezionato = st.selectbox("Seleziona route_id:", route_ids)

        trips_linea = trips[trips["route_id"] == route_id_selezionato]
        trip_ids = trips_linea["trip_id"].unique()

        stop_ids_set = set(stop_times[stop_times['trip_id'].isin(trip_ids)]['stop_id'].unique())
        fermate_linea = stops[stops["stop_id"].isin(stop_ids_set)].drop_duplicates()

        mappa = folium.Map(location=[fermate_linea["stop_lat"].astype(float).mean(), fermate_linea["stop_lon"].astype(float).mean()], zoom_start=13)
        for _, stop in fermate_linea.iterrows():
            folium.CircleMarker(location=(float(stop['stop_lat']), float(stop['stop_lon'])), radius=5, color='blue', fill=True).add_to(mappa)
        st_folium(mappa, width=700, height=500)

    except Exception as e:
        st.error(f"Errore nel caricamento dati fermate: {e}")

if st.checkbox("Visualizza output del modello prescrittivo"):
    try:
        df_opt_all = load_ottimizzazione()
        selected_fascia = st.multiselect("Fasce orarie:", df_opt_all['fascia_oraria'].unique(), default=df_opt_all['fascia_oraria'].unique())
        selected_linee = st.multiselect("Linee:", sorted(df_opt_all['route_id'].unique()), default=sorted(df_opt_all['route_id'].unique()))

        df_filtered = df_opt_all[(df_opt_all['fascia_oraria'].isin(selected_fascia)) & (df_opt_all['route_id'].isin(selected_linee))]

        fig_opt = px.bar(df_filtered, x="route_id", y="extra_trips", color="fascia_oraria", barmode="group",
                         labels={"extra_trips": "Corse extra", "route_id": "Linea"})
        st.plotly_chart(fig_opt, use_container_width=True)
        st.dataframe(df_filtered)

    except Exception as e:
        st.error(f"Errore nel caricamento output ottimizzazione: {e}")
