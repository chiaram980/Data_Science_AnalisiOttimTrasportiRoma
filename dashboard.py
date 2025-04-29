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
    'Lunedì', 'Lunedì', 'Martedì', 'Mercoledì', 'Martedì', 'Giovedì', 'Venerdì', 'Venerdì',
    'Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Lunedì', 'Martedì', 'Mercoledì',
    'Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Giovedì', 'Venerdì', 'Venerdì'
]

# ======================== Titolo ========================

st.title("Dashboard Ritardi Trasporti Pubblici - Roma")

# ======================== Sidebar - Filtri Iniziali ========================

st.sidebar.header("Filtri Ritardi Settimanali")

selected_week = st.sidebar.selectbox("Seleziona la settimana:", sorted(data_fascia["week_range"].unique()))
selected_hours = st.sidebar.multiselect("Seleziona le ore:", sorted(data_fascia['hour'].unique()), default=sorted(data_fascia['hour'].unique()))
selected_routes = st.sidebar.multiselect("Seleziona le linee:", sorted(data_fascia['route_id'].unique()), default=sorted(data_fascia['route_id'].unique()))

# ======================== Applicazione filtri ========================

filtered_data = data_fascia[(data_fascia['hour'].isin(selected_hours)) & (data_fascia['route_id'].isin(selected_routes)) & (data_fascia['week_range'] == selected_week)]

# ======================== Sezione 1: Ritardi Medi ========================

st.subheader(f"Ritardi medi per linea e ora - Settimana {selected_week}")

fig1 = px.bar(filtered_data, x="route_id", y="delay", color="hour", barmode="group")
st.plotly_chart(fig1, use_container_width=True)

st.markdown("**Figura 1:** Il grafico mostra i ritardi medi delle linee selezionate, suddivisi per ora della giornata.")

# ======================== Sezione 2: Heatmap Corse Extra ========================

st.subheader("Heatmap delle corse extra")

pivot = filtered_data.pivot_table(index='route_id', columns='hour', values='extra_trips', fill_value=0)
fig2, ax2 = plt.subplots(figsize=(10,6))
sns.heatmap(pivot, cmap='coolwarm', annot=True, fmt='g', ax=ax2)
st.pyplot(fig2)

st.markdown("**Figura 2:** Heatmap delle corse extra suggerite dal modello.")

# ======================== Sezione 3: Scatter Plot Ritardi ========================

st.subheader("Distribuzione dei ritardi medi")

fig3 = px.scatter(filtered_data, x="hour", y="delay", size="extra_trips", color="route_id")
st.plotly_chart(fig3, use_container_width=True)

st.markdown("**Figura 3:** Ogni punto rappresenta una linea in una determinata ora.")

# ======================== Sezione 4: Tabella & Metriche ========================

st.subheader("Tabella dati filtrati")
st.dataframe(filtered_data.sort_values(by="delay", ascending=False))

media_ritardo = filtered_data['delay'].mean()
st.metric("Ritardo medio complessivo (min)", f"{media_ritardo:.2f}")

# ======================== Sezione 5: Esportazione ========================

csv = filtered_data.to_csv(index=False).encode('utf-8')
st.download_button("Scarica CSV", data=csv, file_name="ritardi_filtrati.csv", mime="text/csv")

# ======================== Sezione 6: Fermate per Linea ========================

st.subheader("Visualizza fermate di una linea specifica")

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

# =================== Output del modello prescrittivo: ottimizzazione delle corse ===================

st.subheader("Output del modello prescrittivo: ottimizzazione delle corse (fasce orarie multiple)")

# Percorsi fissi dei due file
file1 = "ottimizzazione_dashboard_20250325_112654.csv"
file2 = "ottimizzazione_dashboard_20250325_113839.csv"

# Caricamento dati
try:
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    # Aggiunta colonna 'fascia_oraria' per distinguere
    df1['fascia_oraria'] = "12-15"
    df2['fascia_oraria'] = "08-11"

    df_opt_all = pd.concat([df1, df2], ignore_index=True)
    df_opt_all['hour'] = df_opt_all['hour'].astype(str)

    # Sidebar - Filtri ottimizzazione
    st.sidebar.header("Filtri corse ottimizzate")

    selected_fasce = st.sidebar.multiselect(
        "Seleziona la fascia oraria:",
        df_opt_all['fascia_oraria'].unique(),
        default=df_opt_all['fascia_oraria'].unique(),
        key="fasce_ottimizzazione"
    )

    selected_routes_opt = st.sidebar.multiselect(
        "Seleziona le linee:",
        sorted(df_opt_all['route_id'].unique()),
        default=sorted(df_opt_all['route_id'].unique()),
        key="linee_ottimizzazione"
    )

    # Applicazione filtri
    df_ottimizzato = df_opt_all[
        (df_opt_all['fascia_oraria'].isin(selected_fasce)) &
        (df_opt_all['route_id'].isin(selected_routes_opt))
    ]

    # Barplot corse extra
    st.subheader("Corse extra suggerite per linea e fascia oraria")
    fig_ott = px.bar(
        df_ottimizzato,
        x="route_id",
        y="extra_trips",
        color="fascia_oraria",
        barmode="group",
        labels={"extra_trips": "Corse extra", "route_id": "Linea"},
        title="Distribuzione delle corse extra suggerite dal modello"
    )
    st.plotly_chart(fig_ott, use_container_width=True)

    # Tabella dati ottimizzati
    st.subheader("Tabella corse ottimizzate")
    st.dataframe(df_ottimizzato.sort_values(by="extra_trips", ascending=False))

    # Metriche
    st.metric("Totale corse extra", int(df_ottimizzato['extra_trips'].sum()))
    st.metric("Riduzione stimata complessiva (minuti)", f"{df_ottimizzato['estimated_impact'].sum():.2f}")

except FileNotFoundError as e:
    st.error(f"File non trovato: {e.filename}")

# =================== Mappa fermate delle corse selezionate (ottimizzate) ===================
st.subheader("Mappa delle fermate associate alle corse ottimizzate")

if 'df_ottimizzato' in locals():
    try:
        if 'routes' not in locals():
            routes = pd.read_csv("routes.txt", dtype=str, low_memory=False)
        if 'trips' not in locals():
            trips = pd.read_csv("trips.txt", dtype=str, low_memory=False)
        if 'stops' not in locals():
            stops = pd.read_csv("stops.txt", dtype=str, low_memory=False)

        # Normalizzazione ID linea
        corse_ottimizzate = df_ottimizzato[['route_id', 'hour']].drop_duplicates().copy()
        corse_ottimizzate['route_id_gtfs'] = corse_ottimizzate['route_id'].str.replace("Linea ", "").str.strip()

        fermate_ottimizzate = pd.DataFrame()
        palette_opt = px.colors.qualitative.Set3

        for idx, row in corse_ottimizzate.iterrows():
            trips_match = trips[trips['route_id'] == row['route_id_gtfs']]
            if not trips_match.empty:
                trip_id = trips_match['trip_id'].iloc[0]
                stops_trip = stop_times[stop_times['trip_id'] == trip_id]
                stop_ids = stops_trip['stop_id'].unique()
                fermate_linea = stops[stops['stop_id'].isin(stop_ids)].copy()
                fermate_linea['route_id'] = row['route_id']
                colore = palette_opt[idx % len(palette_opt)]
                fermate_linea['color'] = colore
                fermate_ottimizzate = pd.concat([fermate_ottimizzate, fermate_linea], ignore_index=True)

        if fermate_ottimizzate.empty:
            st.warning("Nessuna fermata trovata per le corse ottimizzate selezionate.")
        else:
            fermate_ottimizzate['stop_lat'] = fermate_ottimizzate['stop_lat'].astype(float)
            fermate_ottimizzate['stop_lon'] = fermate_ottimizzate['stop_lon'].astype(float)

            m_opt = folium.Map(
                location=[fermate_ottimizzate['stop_lat'].mean(), fermate_ottimizzate['stop_lon'].mean()],
                zoom_start=12
            )

            for _, row in fermate_ottimizzate.iterrows():
                folium.CircleMarker(
                    location=(row['stop_lat'], row['stop_lon']),
                    radius=5,
                    color=row['color'],
                    fill=True,
                    fill_color=row['color'],
                    fill_opacity=0.8,
                    tooltip=row['stop_name']
                ).add_to(m_opt)

            st_folium(m_opt, width=700, height=500)
            st.markdown("**Figura:** Mappa interattiva delle fermate associate alle corse ottimizzate.")

            # Tabella fermate ottimizzate
            st.subheader("Fermate coinvolte nelle corse ottimizzate")
            st.dataframe(fermate_ottimizzate[['route_id', 'stop_name', 'stop_lat', 'stop_lon']].drop_duplicates().sort_values(by='route_id'))

    except FileNotFoundError as e:
        st.error(f"File mancante: {e.filename}")
else:
    st.warning("Dati delle corse ottimizzate non caricati. Impossibile creare la mappa.")
