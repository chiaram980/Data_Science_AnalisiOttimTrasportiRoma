import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import io
import os
import gdown

# ======================== Caricamento dati iniziali ========================

# Dataset base

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

# Aggiunta colonne

data_fascia["week_range"] = data_fascia["hour"].apply(lambda x: "3-7 marzo" if x in [13, 14] else "10-14 febbraio")
data_fascia["hour"] = data_fascia["hour"].astype(str)
data_fascia['day_of_week'] = [
    'Luned\u00ec', 'Luned\u00ec', 'Marted\u00ec', 'Mercoled\u00ec', 'Marted\u00ec', 'Gioved\u00ec', 'Venerd\u00ec', 'Venerd\u00ec',
    'Luned\u00ec', 'Marted\u00ec', 'Mercoled\u00ec', 'Gioved\u00ec', 'Venerd\u00ec', 'Luned\u00ec', 'Marted\u00ec', 'Mercoled\u00ec',
    'Luned\u00ec', 'Marted\u00ec', 'Mercoled\u00ec', 'Gioved\u00ec', 'Venerd\u00ec', 'Gioved\u00ec', 'Venerd\u00ec', 'Venerd\u00ec'
]

# ======================== Titolo ========================

st.title("\ud83d\udcc5 Dashboard Ritardi Trasporti Pubblici - Roma")

# ======================== Sidebar - Filtri Iniziali ========================

st.sidebar.header("\ud83d\udcc5 Filtri Ritardi Settimanali")

selected_week = st.sidebar.selectbox("Seleziona la settimana:", sorted(data_fascia["week_range"].unique()))
selected_hours = st.sidebar.multiselect("Seleziona le ore:", sorted(data_fascia['hour'].unique()), default=sorted(data_fascia['hour'].unique()))
selected_routes = st.sidebar.multiselect("Seleziona le linee:", sorted(data_fascia['route_id'].unique()), default=sorted(data_fascia['route_id'].unique()))

# ======================== Applicazione filtri ========================

filtered_data = data_fascia[(data_fascia['hour'].isin(selected_hours)) & (data_fascia['route_id'].isin(selected_routes)) & (data_fascia['week_range'] == selected_week)]

# ======================== Sezione 1: Ritardi Medi ========================

st.subheader(f"\ud83d\udcca Ritardi medi per linea e ora - Settimana {selected_week}")

fig1 = px.bar(filtered_data, x="route_id", y="delay", color="hour", barmode="group")
st.plotly_chart(fig1, use_container_width=True)

st.markdown("**Figura 1:** Il grafico mostra i ritardi medi delle linee selezionate, suddivisi per ora della giornata.")

# ======================== Sezione 2: Heatmap Corse Extra ========================

st.subheader("\ud83c\udf21\ufe0f Heatmap delle corse extra")

pivot = filtered_data.pivot_table(index='route_id', columns='hour', values='extra_trips', fill_value=0)
fig2, ax2 = plt.subplots(figsize=(10,6))
sns.heatmap(pivot, cmap='coolwarm', annot=True, fmt='g', ax=ax2)
st.pyplot(fig2)

st.markdown("**Figura 2:** Heatmap delle corse extra suggerite dal modello.")

# ======================== Sezione 3: Scatter Plot Ritardi ========================

st.subheader("\ud83d\udcc8 Distribuzione dei ritardi medi")

fig3 = px.scatter(filtered_data, x="hour", y="delay", size="extra_trips", color="route_id")
st.plotly_chart(fig3, use_container_width=True)

st.markdown("**Figura 3:** Ogni punto rappresenta una linea in una determinata ora.")

# ======================== Sezione 4: Tabella & Metriche ========================

st.subheader("\ud83d\udcca Tabella dati filtrati")
st.dataframe(filtered_data.sort_values(by="delay", ascending=False))

media_ritardo = filtered_data['delay'].mean()
st.metric("Ritardo medio complessivo (min)", f"{media_ritardo:.2f}")

# ======================== Sezione 5: Esportazione ========================

csv = filtered_data.to_csv(index=False).encode('utf-8')
st.download_button("\ud83d\udce5 Scarica CSV", data=csv, file_name="ritardi_filtrati.csv", mime="text/csv")

# ======================== Sezione 6: Fermate per Linea ========================

st.subheader("\ud83d\udccd Visualizza fermate di una linea specifica")

try:
    routes = pd.read_csv("routes.txt", dtype=str, low_memory=False)
    trips = pd.read_csv("trips.txt", dtype=str, low_memory=False)
    stops = pd.read_csv("stops.txt", dtype=str, low_memory=False)

    routes = routes[(routes['agency_id'] == 'OP1') & (routes['route_type'] == '3')]
    route_ids = sorted(routes['route_id'].unique())

    route_id_selezionato = st.selectbox("Seleziona una linea (route_id):", route_ids)

    nome_linea = routes[routes["route_id"] == route_id_selezionato]["route_long_name"].iloc[0]
    st.markdown(f"**Linea selezionata:** `{route_id_selezionato}`")

    trips_linea = trips[trips["route_id"] == route_id_selezionato]
    trip_ids = trips_linea["trip_id"].unique()

    # Caricamento stop_times dal file parquet su Google Drive
    file_id = "1Qx7jVKObRN79CLJwIy9Jzh0VwJ2D9dWZ"
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(download_url, stream=True)
    response.raise_for_status()
    stop_times = pd.read_parquet(io.BytesIO(response.content))

    stop_ids_set = set(stop_times[stop_times['trip_id'].isin(trip_ids)]['stop_id'].unique())

    if stop_ids_set:
        fermate_linea = stops[stops["stop_id"].isin(stop_ids_set)].drop_duplicates(subset="stop_id")
        fermate_linea["stop_lat"] = fermate_linea["stop_lat"].astype(float)
        fermate_linea["stop_lon"] = fermate_linea["stop_lon"].astype(float)

        st.markdown(f"**Numero di fermate trovate:** {len(fermate_linea)}")
        st.dataframe(fermate_linea[["stop_name", "stop_lat", "stop_lon"]].sort_values(by="stop_name"))

        m = folium.Map(location=[fermate_linea["stop_lat"].mean(), fermate_linea["stop_lon"].mean()], zoom_start=13)
        for _, stop in fermate_linea.iterrows():
            folium.CircleMarker(location=(stop['stop_lat'], stop['stop_lon']), radius=4, color='blue', fill=True, fill_opacity=0.7, tooltip=stop['stop_name']).add_to(m)

        st_folium(m, width=700, height=500)
    else:
        st.warning("Nessuna fermata trovata.")

except FileNotFoundError as e:
    st.error(f"File mancante: {e.filename}")
except Exception as e:
    st.error(f"Errore nella costruzione della mappa: {e}")
