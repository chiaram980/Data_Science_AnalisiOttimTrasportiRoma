import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from io import BytesIO
import zipfile
import matplotlib.pyplot as plt
import seaborn as sns
import os
import gdown



#Caricamento dei dati

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


#Aggiunta della colonna settimana

data_fascia["week_range"] = data_fascia["hour"].apply(
    lambda x: "3-7 marzo" if x in [13, 14] else "10-14 febbraio"
)

#Conversione per il filtro
data_fascia["hour"] = data_fascia["hour"].astype(str)

#Titolo della dashboard
st.title(" Dashboard Ritardi Trasporti Pubblici - Roma")

# Sidebar - Filtri
st.sidebar.header(" Filtri")

selected_week = st.sidebar.selectbox(
    "Seleziona la settimana:",
    options=sorted(data_fascia["week_range"].unique())
)

selected_hours = st.sidebar.multiselect(
    "Seleziona le ore:",
    options=sorted(data_fascia['hour'].unique()),
    default=sorted(data_fascia['hour'].unique())
)

selected_routes = st.sidebar.multiselect(
    "Seleziona le linee:",
    options=sorted(data_fascia['route_id'].unique()),
    default=sorted(data_fascia['route_id'].unique())
)

#Filtri meteo se presenti
if {"prcp", "wspd"}.issubset(data_fascia.columns):
    filtro_pioggia = st.sidebar.checkbox("Solo linee con pioggia", value=False)
    filtro_vento = st.sidebar.checkbox("Solo linee con vento > 10 km/h", value=False)

    if filtro_pioggia:
        data_fascia = data_fascia[data_fascia["prcp"] > 0]
    if filtro_vento:
        data_fascia = data_fascia[data_fascia["wspd"] > 10]

#Applicazione dei filtri

filtered_data = data_fascia[
    (data_fascia['hour'].isin(selected_hours)) &
    (data_fascia['route_id'].isin(selected_routes)) &
    (data_fascia['week_range'] == selected_week)
]


#Sezione 1: Ritardi medi

st.subheader(f"Ritardi medi per linea e ora - Settimana {selected_week}")

fig1 = px.bar(
    filtered_data,
    x="route_id",
    y="delay",
    color="hour",
    barmode="group",
    labels={"delay": "Ritardo medio (min)", "route_id": "Linea"},
    title=f"Ritardi medi per linea e ora - Settimana {selected_week}"
)
st.plotly_chart(fig1, use_container_width=True)

st.markdown("**Figura 1:** Il grafico mostra i ritardi medi delle linee selezionate, suddivisi per ora della giornata. Le linee con barre più alte sono quelle con i ritardi più consistenti.")


#Sezione 2: Heatmap corse extra

st.subheader(" Heatmap delle corse extra")

pivot = filtered_data.pivot_table(
    index='route_id',
    columns='hour',
    values='extra_trips',
    fill_value=0
)

fig2, ax2 = plt.subplots(figsize=(10, 6))
sns.heatmap(pivot, cmap='coolwarm', annot=True, fmt='g', ax=ax2)
plt.title("Corse extra per linea e ora")
plt.xlabel("Ora")
plt.ylabel("Linea")

st.pyplot(fig2)
st.markdown("**Figura 2:** Heatmap delle corse extra suggerite dal modello prescrittivo. Le celle colorate indicano dove sono state allocate più risorse.")


#Sezione 3: Scatter Plot ritardi

st.subheader("Distribuzione dei ritardi medi")

fig3 = px.scatter(
    filtered_data,
    x="hour",
    y="delay",
    size="extra_trips",
    color="route_id",
    labels={"delay": "Ritardo medio (min)", "hour": "Ora", "route_id": "Linea"},
    title=f"Distribuzione dei ritardi medi - Settimana {selected_week}"
)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("**Figura 3:** Ogni punto rappresenta una linea in una determinata ora. Il diametro del punto rappresenta il numero di corse extra assegnate.")


#Sezione 4: Tabella & Metriche

st.subheader("Tabella dati filtrati")

st.dataframe(filtered_data.sort_values(by="delay", ascending=False))

media_ritardo = filtered_data['delay'].mean()
st.metric("Ritardo medio complessivo (min)", f"{media_ritardo:.2f}")


#Sezione 5: Esportazione dati
csv = filtered_data.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Scarica CSV",
    data=csv,
    file_name="ritardi_filtrati.csv",
    mime="text/csv"
)



###

#Fermate per ogni route_id
st.subheader("Visualizza fermate di una linea specifica")




#Carica dati principali
try:
    routes = pd.read_csv("routes.txt", dtype=str, low_memory=False)
    trips = pd.read_csv("trips.txt", dtype=str, low_memory=False)
    stops = pd.read_csv("stops.txt", dtype=str, low_memory=False)
except FileNotFoundError as e:
    st.error(f"File mancante: {e.filename}")
else:
    #Filtra solo bus OP1
    routes = routes[(routes['agency_id'] == 'OP1') & (routes['route_type'] == '3')]
    route_ids = sorted(routes['route_id'].unique())

    #Selezione linea
    route_id_selezionato = st.selectbox("Seleziona una linea (route_id):", route_ids)

    #Mostra anche il nome linea
    nome_linea = routes[routes["route_id"] == route_id_selezionato]["route_long_name"].iloc[0]
    st.markdown(f"**Linea selezionata:** `{route_id_selezionato}`")

    #Recupera tutti i trip della linea
    trips_linea = trips[trips["route_id"] == route_id_selezionato]
    trip_ids = trips_linea["trip_id"].unique()


    stop_ids_set = set()
    

####

import streamlit as st
import pandas as pd
import requests
import io

# === Link diretto Google Drive ===
file_id = "1Qx7jVKObRN79CLJwIy9Jzh0VwJ2D9dWZ"
download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

st.markdown("### Caricamento del file stop_times da Google Drive...")

try:
    with requests.get(download_url, stream=True) as response:
        response.raise_for_status()
        file_stream = io.BytesIO(response.content)

        # Caricamento del Parquet
        stop_times = pd.read_parquet(file_stream)
        st.success("File caricato correttamente da Google Drive.")
except requests.exceptions.RequestException as e:
    st.error(f"Errore durante il download da Google Drive: {e}")
except Exception as e:
    st.error(f"Errore durante la lettura del file Parquet: {e}")


# Supponiamo che `stop_ids_set` sia stato definito in precedenza con stop_id delle corse
# Ad esempio:
stop_ids_set = set(stop_times[stop_times['trip_id'].isin(trip_ids)]['stop_id'].unique())

if stop_ids_set:
    # Filtra fermate
    fermate_linea = stops[stops["stop_id"].isin(stop_ids_set)].drop_duplicates(subset="stop_id")
    fermate_linea["stop_lat"] = fermate_linea["stop_lat"].astype(float)
    fermate_linea["stop_lon"] = fermate_linea["stop_lon"].astype(float)

    st.markdown(f"**Numero di fermate trovate:** {len(fermate_linea)}")

    # Tabella fermate
    st.dataframe(fermate_linea[["stop_name", "stop_lat", "stop_lon"]].sort_values(by="stop_name"))

    # Mappa con fermate
    m = folium.Map(
        location=[fermate_linea["stop_lat"].mean(), fermate_linea["stop_lon"].mean()],
        zoom_start=13
    )

    for _, stop in fermate_linea.iterrows():
        folium.CircleMarker(
            location=(stop['stop_lat'], stop['stop_lon']),
            radius=4,
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.7,
            tooltip=stop['stop_name']
        ).add_to(m)

    st_folium(m, width=700, height=500)
    st.markdown("**Mappa delle fermate della linea selezionata.**")
else:
    st.warning("Nessuna fermata trovata per questa linea.")







