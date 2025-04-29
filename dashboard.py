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
import requests
import io

# ======================== Caricamento dati ========================

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

# ======================== Dataset iniziale ========================

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
data_fascia['day_of_week'] =  [
    'Lunedì', 'Lunedì', 'Martedì', 'Mercoledì', 'Martedì', 'Giovedì', 'Venerdì', 'Venerdì',
    'Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Lunedì', 'Martedì', 'Mercoledì',
    'Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Giovedì', 'Venerdì', 'Venerdì'
]

# ======================== Titolo ========================

st.title("Dashboard Ritardi Trasporti Pubblici - Roma")

# ======================== Sidebar Filtri Ritardi ========================

st.sidebar.header("Filtri Ritardi Settimanali")
selected_week = st.sidebar.selectbox("Seleziona la settimana:", sorted(data_fascia["week_range"].unique()))
selected_hours = st.sidebar.multiselect("Seleziona le ore:", sorted(data_fascia['hour'].unique()), default=sorted(data_fascia['hour'].unique()))
selected_routes = st.sidebar.multiselect("Seleziona le linee:", sorted(data_fascia['route_id'].unique()), default=sorted(data_fascia['route_id'].unique()))

# ======================== Applicazione filtri ========================

filtered_data = data_fascia[(data_fascia['hour'].isin(selected_hours)) & (data_fascia['route_id'].isin(selected_routes)) & (data_fascia['week_range'] == selected_week)]

# ======================== Ritardi Medi ========================

st.subheader(f"Ritardi medi per linea e ora - Settimana {selected_week}")
fig1 = px.bar(filtered_data, x="route_id", y="delay", color="hour", barmode="group")
st.plotly_chart(fig1, use_container_width=True)

# ======================== Heatmap corse extra ========================

st.subheader("Heatmap delle corse extra")
pivot = filtered_data.pivot_table(index='route_id', columns='hour', values='extra_trips', fill_value=0)
fig2, ax2 = plt.subplots(figsize=(10,6))
sns.heatmap(pivot, cmap='coolwarm', annot=True, fmt='g', ax=ax2)
st.pyplot(fig2)

# ======================== Scatter Plot Ritardi ========================

st.subheader("Distribuzione dei ritardi medi")
fig3 = px.scatter(filtered_data, x="hour", y="delay", size="extra_trips", color="route_id")
st.plotly_chart(fig3, use_container_width=True)

# ======================== Tabella & Metriche ========================

st.subheader("Tabella dati filtrati")
st.dataframe(filtered_data.sort_values(by="delay", ascending=False))
media_ritardo = filtered_data['delay'].mean()
st.metric("Ritardo medio complessivo (min)", f"{media_ritardo:.2f}")

# ======================== Download CSV ========================

csv = filtered_data.to_csv(index=False).encode('utf-8')
st.download_button("Scarica CSV", data=csv, file_name="ritardi_filtrati.csv", mime="text/csv")

# ======================== Visualizza Fermate di una Linea ========================

# ======================== Sezione 7: Analisi ritardi per giorno della settimana ========================

st.subheader("Analisi dei ritardi per giorno della settimana")

# Sidebar - Filtri dedicati a questa sezione
st.sidebar.header("Filtri Ritardi Giornalieri")
giorni_disp = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì']
selected_days_settimanale = st.sidebar.multiselect(
    "Seleziona i giorni della settimana:",
    giorni_disp,
    default=giorni_disp,
    key="giorni_settimanale"
)
selected_routes_settimanale = st.sidebar.multiselect(
    "Seleziona le linee (giornaliero):",
    sorted(data_fascia['route_id'].unique()),
    default=sorted(data_fascia['route_id'].unique()),
    key="linee_settimanale"
)

# Filtro dati
data_giornaliera = data_fascia[
    (data_fascia['day_of_week'].isin(selected_days_settimanale)) &
    (data_fascia['route_id'].isin(selected_routes_settimanale)) &
    (data_fascia['week_range'] == selected_week)
]

# Line chart ritardi
fig_settimanale = px.line(
    data_giornaliera,
    x='day_of_week',
    y='delay',
    color='route_id',
    markers=True,
    labels={'day_of_week': 'Giorno della settimana', 'delay': 'Ritardo medio (min)', 'route_id': 'Linea'},
    title=f"Andamento ritardi nella settimana {selected_week}"
)
st.plotly_chart(fig_settimanale, use_container_width=True)

st.dataframe(data_giornaliera.sort_values(by=['route_id', 'day_of_week']))

# ======================== Sezione 8: Output Modello Prescrittivo (Ottimizzazione) ========================

st.subheader("Output del modello prescrittivo: ottimizzazione delle corse (fasce orarie multiple)")

# Caricamento dati ottimizzazione già fatto sopra (df_opt_all)

# Ricarico qui i filtri per sicurezza
selected_fasce_finale = st.sidebar.multiselect(
    "Fasce orarie (finale):",
    df_opt_all['fascia_oraria'].unique(),
    default=list(df_opt_all['fascia_oraria'].unique()),
    key="fasce_finale"
)
selected_routes_finale = st.sidebar.multiselect(
    "Linee ottimizzate (finale):",
    sorted(df_opt_all['route_id'].unique()),
    default=sorted(df_opt_all['route_id'].unique()),
    key="linee_finale"
)

# Filtro finale
df_finale = df_opt_all[
    (df_opt_all['fascia_oraria'].isin(selected_fasce_finale)) &
    (df_opt_all['route_id'].isin(selected_routes_finale))
]

# Barplot ottimizzazione finale
fig_finale = px.bar(
    df_finale,
    x="route_id",
    y="extra_trips",
    color="fascia_oraria",
    barmode="group",
    labels={"extra_trips": "Corse extra", "route_id": "Linea"},
    title="Distribuzione finale delle corse extra"
)
st.plotly_chart(fig_finale, use_container_width=True)

st.dataframe(df_finale.sort_values(by="extra_trips", ascending=False))

# ======================== Sezione 9: Mappa delle corse ottimizzate ========================

st.subheader("Mappa delle fermate associate alle corse ottimizzate")

try:
    # Se non caricate prima
    if 'routes' not in locals():
        routes = pd.read_csv("routes.txt", dtype=str, low_memory=False)
    if 'trips' not in locals():
        trips = pd.read_csv("trips.txt", dtype=str, low_memory=False)
    if 'stops' not in locals():
        stops = pd.read_csv("stops.txt", dtype=str, low_memory=False)

    # Preparo corse
    corse_finali = df_finale[['route_id', 'hour']].drop_duplicates().copy()
    corse_finali['route_id_gtfs'] = corse_finali['route_id'].str.replace("Linea ", "").str.strip()

    fermate_finali = pd.DataFrame()
    palette_finale = px.colors.qualitative.Set1

    for idx, row in corse_finali.iterrows():
        trips_match = trips[trips['route_id'] == row['route_id_gtfs']]
        if not trips_match.empty:
            trip_id = trips_match['trip_id'].iloc[0]
            stops_trip = stop_times[stop_times['trip_id'] == trip_id]
            stop_ids = stops_trip['stop_id'].unique()
            fermate_linea = stops[stops['stop_id'].isin(stop_ids)].copy()
            fermate_linea['route_id'] = row['route_id']
            colore = palette_finale[idx % len(palette_finale)]
            fermate_linea['color'] = colore
            fermate_finali = pd.concat([fermate_finali, fermate_linea], ignore_index=True)

    if fermate_finali.empty:
        st.warning("Nessuna fermata trovata per le corse ottimizzate.")
    else:
        fermate_finali['stop_lat'] = fermate_finali['stop_lat'].astype(float)
        fermate_finali['stop_lon'] = fermate_finali['stop_lon'].astype(float)

        m_finale = folium.Map(
            location=[fermate_finali['stop_lat'].mean(), fermate_finali['stop_lon'].mean()],
            zoom_start=12
        )

        for _, row in fermate_finali.iterrows():
            folium.CircleMarker(
                location=(row['stop_lat'], row['stop_lon']),
                radius=5,
                color=row['color'],
                fill=True,
                fill_color=row['color'],
                fill_opacity=0.8,
                tooltip=row['stop_name']
            ).add_to(m_finale)

        st_folium(m_finale, width=700, height=500)
        st.markdown("**Figura:** Mappa interattiva delle fermate associate alle corse ottimizzate.")

        # Tabella fermate
        st.subheader("Fermate coinvolte nelle corse ottimizzate")
        st.dataframe(fermate_finali[['route_id', 'stop_name', 'stop_lat', 'stop_lon']].drop_duplicates().sort_values(by='route_id'))

except FileNotFoundError as e:
    st.error(f"File mancante: {e.filename}")
except Exception as e:
    st.error(f"Errore nella creazione della mappa ottimizzata: {e}")

