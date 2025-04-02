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

# Scaricamento automatico del file stop_times da Google Drive se non presente
stop_times_path = "stop_times.txt"
drive_file_id = "1VP9h8S5hE15vog2DlLjJuoRIxf4uJhJW"

def scarica_stop_times():
    if not os.path.exists(stop_times_path):
        url = f"https://drive.google.com/uc?id={drive_file_id}"
        gdown.download(url, stop_times_path, quiet=False)

scarica_stop_times()


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
    


# Scarica il file stop_times da Google Drive
url = "https://drive.google.com/uc?id=1VP9h8S5hE15vog2DlLjJuoRIxf4uJhJW"
output = "stop_times_temp.txt"

try:
    gdown.download(url, output, quiet=False)

    # Legge il file scaricato a blocchi
    for chunk in pd.read_csv(output, dtype=str, chunksize=100000, low_memory=False):
        stop_ids_set.update(chunk[chunk["trip_id"].isin(trip_ids)]["stop_id"].unique())

except FileNotFoundError:
    st.warning("File stop_times.txt non trovato.")
    stop_ids_set = set()


    if stop_ids_set:
        #Filtra fermate
        fermate_linea = stops[stops["stop_id"].isin(stop_ids_set)].drop_duplicates(subset="stop_id")
        fermate_linea["stop_lat"] = fermate_linea["stop_lat"].astype(float)
        fermate_linea["stop_lon"] = fermate_linea["stop_lon"].astype(float)

        st.markdown(f"**Numero di fermate trovate:** {len(fermate_linea)}")

        #Tabella fermate
        st.dataframe(fermate_linea[["stop_name", "stop_lat", "stop_lon"]].sort_values(by="stop_name"))

        #Mappa con fermate
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


# Dashboard Ritardi per Giorno della Settimana

st.subheader("Analisi dei ritardi per giorno della settimana")


data_fascia['day_of_week'] = [
    'Lunedì', 'Lunedì', 'Martedì', 'Mercoledì', 'Martedì', 'Giovedì', 'Venerdì', 'Venerdì',
    'Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Lunedì', 'Martedì', 'Mercoledì',
    'Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Giovedì', 'Venerdì', 'Venerdì'
]

#Sidebar per filtri
st.sidebar.header("Filtri settimanali")
settimane_disp = sorted(data_fascia['week_range'].unique())
giorni_disp = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì']
linee_disp = sorted(data_fascia['route_id'].unique())

#Aggiunta delle chiavi per evitare conflitti
selected_week = st.sidebar.selectbox("Seleziona la settimana:", settimane_disp, key="selectbox_settimana")
selected_days = st.sidebar.multiselect("Giorni della settimana:", giorni_disp, default=giorni_disp, key="multiselect_giorni")
selected_routes = st.sidebar.multiselect("Linee:", linee_disp, default=linee_disp, key="multiselect_linee")

#Filtro dati
data_settimanale = data_fascia[
    (data_fascia['week_range'] == selected_week) &
    (data_fascia['day_of_week'].isin(selected_days)) &
    (data_fascia['route_id'].isin(selected_routes))
]

#Line chart dei ritardi
fig_sett = px.line(
    data_settimanale,
    x='day_of_week',
    y='delay',
    color='route_id',
    markers=True,
    labels={'day_of_week': 'Giorno della settimana', 'delay': 'Ritardo medio (min)', 'route_id': 'Linea'},
    title=f"Andamento dei ritardi nella settimana {selected_week}"
)
st.plotly_chart(fig_sett, use_container_width=True)

#Tabella riassuntiva
st.subheader("Dati ritardi settimanali filtrati")
st.dataframe(data_settimanale.sort_values(by=['route_id', 'day_of_week']))




#Visualizzazione dei due file output del modello prescrittivo

st.subheader("Output del modello prescrittivo: ottimizzazione delle corse (fasce orarie multiple)")

# Percorsi fissi dei due file
file1 = "ottimizzazione_20250325_112654.csv"
file2 = "ottimizzazione_20250325_113839.csv"

#Caricamento dati
try:
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    #Aggiunta colonna 'fascia' per distinguerli
    df1['fascia_oraria'] = "12-15"
    df2['fascia_oraria'] = "08-11"


    df_opt_all = pd.concat([df1, df2], ignore_index=True)
    df_opt_all['hour'] = df_opt_all['hour'].astype(str)

    #Filtri interattivi
    st.sidebar.header("Filtri corse ottimizzate")
    selected_fascia = st.sidebar.multiselect(
        "Seleziona la fascia oraria:",
        df_opt_all['fascia_oraria'].unique(),
        default=df_opt_all['fascia_oraria'].unique(),
        key="fasce_orarie_opt"
    )

    selected_linee = st.sidebar.multiselect(
        "Seleziona le linee:",
        sorted(df_opt_all['route_id'].unique()),
        default=sorted(df_opt_all['route_id'].unique()),
        key="linee_opt"
    )

    #Filtro
    df_filtered = df_opt_all[
        (df_opt_all['fascia_oraria'].isin(selected_fascia)) &
        (df_opt_all['route_id'].isin(selected_linee))
    ]

    #Barplot
    st.subheader("Corse extra suggerite per linea e ora")
    fig_opt = px.bar(
        df_filtered,
        x="route_id",
        y="extra_trips",
        color="fascia_oraria",
        barmode="group",
        labels={"extra_trips": "Corse extra", "route_id": "Linea"},
        title="Distribuzione corse extra per fascia oraria"
    )
    st.plotly_chart(fig_opt, use_container_width=True)

    #Tabella
    st.subheader("Tabella corse ottimizzate")
    st.dataframe(df_filtered.sort_values(by="extra_trips", ascending=False))


    st.metric("Totale corse extra", int(df_filtered['extra_trips'].sum()))
    st.metric("Riduzione stimata complessiva (minuti)", f"{df_filtered['estimated_impact'].sum():.2f}")

except FileNotFoundError as e:
    st.error(f"File non trovato: {e.filename}")

# Mappa fermate delle corse selezionate

st.subheader("Mappa delle fermate associate alle corse selezionate")


try:
     
    if 'routes' not in locals():
        routes = pd.read_csv( "routes.txt", dtype=str, low_memory=False)
    if 'trips' not in locals():
        trips = pd.read_csv("trips.txt", dtype=str, low_memory=False)
    if 'stop_times' not in locals():
        stop_times = pd.read_csv(r"https://drive.google.com/file/d/1VP9h8S5hE15vog2DlLjJuoRIxf4uJhJW/view?usp=drive_link", dtype=str, low_memory=False)
    if 'stops' not in locals():
        stops = pd.read_csv("stops.txt", dtype=str, low_memory=False)

    #Filtro settimana/ora già applicato su data_settimanale
    corse_filtrate = data_settimanale[['route_id', 'hour']].drop_duplicates().copy()

    #Normalizza route_id per compatibilità con GTFS 
    corse_filtrate['route_id_gtfs'] = corse_filtrate['route_id'].str.replace("Linea ", "").str.strip()

    fermate_totali = pd.DataFrame()

    
    palette = px.colors.qualitative.Set2
    colori_linee = {}

    for idx, row in corse_filtrate.iterrows():
        route_id_gtfs = row['route_id_gtfs']
        route_id_display = row['route_id']
        trips_match = trips[trips['route_id'] == route_id_gtfs]

        if not trips_match.empty:
            trip_id = trips_match['trip_id'].iloc[0] 
            stops_trip = stop_times[stop_times['trip_id'] == trip_id]
            stop_ids = stops_trip['stop_id'].unique()
            fermate_linea = stops[stops['stop_id'].isin(stop_ids)].copy()
            fermate_linea['route_id'] = route_id_display 

            colore = palette[idx % len(palette)]
            colori_linee[route_id_display] = colore
            fermate_linea['color'] = colore

            fermate_totali = pd.concat([fermate_totali, fermate_linea], ignore_index=True)

    if fermate_totali.empty:
        st.warning("Nessuna fermata trovata per le corse selezionate.")
    else:
        fermate_totali['stop_lat'] = fermate_totali['stop_lat'].astype(float)
        fermate_totali['stop_lon'] = fermate_totali['stop_lon'].astype(float)

        m = folium.Map(
            location=[fermate_totali['stop_lat'].mean(), fermate_totali['stop_lon'].mean()],
            zoom_start=12
        )

        for _, row in fermate_totali.iterrows():
            folium.CircleMarker(
                location=(row['stop_lat'], row['stop_lon']),
                radius=5,
                color=row['color'],
                fill=True,
                fill_color=row['color'],
                fill_opacity=0.8,
                tooltip=row['stop_name']
            ).add_to(m)

        st_folium(m, width=700, height=500)
        st.markdown("**Figura:** Mappa interattiva delle fermate associate alle corse selezionate in base a settimana e orario.")

        #Tabella fermate
        st.subheader(" Fermate coinvolte")
        st.dataframe(fermate_totali[['route_id', 'stop_name', 'stop_lat', 'stop_lon']].drop_duplicates().sort_values(by='route_id'))

except FileNotFoundError as e:
    st.error(f" File mancante: {e.filename}")



