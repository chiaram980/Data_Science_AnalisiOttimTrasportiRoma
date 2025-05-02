import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import io

# ========== Funzioni di supporto ==========

@st.cache_data
def carica_dataset_gtfs():
    routes = pd.read_csv("routes.txt", dtype=str, low_memory=False)
    trips = pd.read_csv("trips.txt", dtype=str, low_memory=False)
    stops = pd.read_csv("stops.txt", dtype=str, low_memory=False)
    return routes, trips, stops

@st.cache_data
def carica_stop_times(file_id):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(url, stream=True)
    response.raise_for_status()
    return pd.read_parquet(io.BytesIO(response.content))

def filtra_routes(routes, dashboard_ids):
    ids_gtfs = [x.replace("Linea ", "").strip() for x in dashboard_ids]
    return routes[(routes['agency_id'] == 'OP1') & (routes['route_type'] == '3') & (routes['route_id'].isin(ids_gtfs))]

def genera_mappa_fermate(trips, stop_times, stops, ottimizzate_df):
    palette = px.colors.qualitative.Set3
    fermate = pd.DataFrame()
    ottimizzate_df['route_id_gtfs'] = ottimizzate_df['route_id'].str.replace("Linea ", "").str.strip()
    for i, row in ottimizzate_df.iterrows():
        match = trips[trips['route_id'] == row['route_id_gtfs']]
        if not match.empty:
            trip_id = match['trip_id'].iloc[0]
            stops_trip = stop_times[stop_times['trip_id'] == trip_id]
            stop_ids = stops_trip['stop_id'].unique()
            fermate_linea = stops[stops['stop_id'].isin(stop_ids)].copy()
            fermate_linea['route_id'] = row['route_id']
            fermate_linea['color'] = palette[i % len(palette)]
            fermate = pd.concat([fermate, fermate_linea], ignore_index=True)
    return fermate

# ========== Dataset base ==========

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

# ========== Layout Streamlit ==========

st.title("Dashboard Ritardi Trasporti Pubblici - Roma")

# Sidebar filtri
st.sidebar.header("Filtri Ritardi Settimanali")
week = st.sidebar.selectbox("Settimana:", sorted(data_fascia["week_range"].unique()))
hours = st.sidebar.multiselect("Ore:", sorted(data_fascia['hour'].unique()), default=sorted(data_fascia['hour'].unique()))
routes_sel = st.sidebar.multiselect("Linee:", sorted(data_fascia['route_id'].unique()), default=sorted(data_fascia['route_id'].unique()))

# Filtro
filtered = data_fascia[(data_fascia['hour'].isin(hours)) & (data_fascia['route_id'].isin(routes_sel)) & (data_fascia['week_range'] == week)]

# Grafici
st.subheader(f"Ritardi medi - Settimana {week}")
st.plotly_chart(px.bar(filtered, x="route_id", y="delay", color="hour", barmode="group"), use_container_width=True)
st.markdown("**Figura 1:** Ritardi medi per ora e linea.")

st.subheader("Heatmap corse extra")
pivot = filtered.pivot_table(index='route_id', columns='hour', values='extra_trips', fill_value=0)
fig_hm, ax = plt.subplots(figsize=(10,6))
sns.heatmap(pivot, cmap='coolwarm', annot=True, fmt='g', ax=ax)
st.pyplot(fig_hm)

st.subheader("Distribuzione ritardi medi")
st.plotly_chart(px.scatter(filtered, x="hour", y="delay", size="extra_trips", color="route_id"), use_container_width=True)

st.subheader("Dati filtrati")
st.dataframe(filtered.sort_values(by="delay", ascending=False))
st.metric("Ritardo medio complessivo (min)", f"{filtered['delay'].mean():.2f}")
st.download_button("Scarica CSV", data=filtered.to_csv(index=False).encode('utf-8'), file_name="ritardi_filtrati.csv", mime="text/csv")

# ========== Output modello prescrittivo ==========

file1, file2 = "ottimizzazione_dashboard_20250325_112654.csv", "ottimizzazione_dashboard_20250325_113839.csv"
try:
    df1, df2 = pd.read_csv(file1), pd.read_csv(file2)
    df1["fascia_oraria"], df2["fascia_oraria"] = "13-14", "09-10"
    df_opt = pd.concat([df1, df2], ignore_index=True)
    df_opt['hour'] = df_opt['hour'].astype(str)

    st.sidebar.header("Filtri corse ottimizzate")
    fasce = st.sidebar.multiselect("Fascia oraria:", df_opt['fascia_oraria'].unique(), default=list(df_opt['fascia_oraria'].unique()))
    routes_opt = st.sidebar.multiselect("Linee:", sorted(df_opt['route_id'].unique()), default=sorted(df_opt['route_id'].unique()), key="opt_routes")
    df_opt_filt = df_opt[df_opt['fascia_oraria'].isin(fasce) & df_opt['route_id'].isin(routes_opt)]
    df_ottimizzato = df_opt_filt.copy()

    st.subheader("Corse extra suggerite")
    fig_bar_opt = px.bar(df_opt_filt, x="route_id", y="extra_trips", color="fascia_oraria", barmode="group")
    st.plotly_chart(fig_bar_opt, use_container_width=True)

    st.subheader("Tabella corse ottimizzate")
    st.dataframe(df_opt_filt.sort_values(by="extra_trips", ascending=False))
    st.metric("Totale corse extra", int(df_opt_filt['extra_trips'].sum()))
    st.metric("Riduzione stimata complessiva (minuti)", f"{df_opt_filt['estimated_impact'].sum():.2f}")

    # ========== Mappa fermate ottimizzate ==========
    with st.expander("Visualizza mappa delle fermate ottimizzate"):
        try:
            routes, trips, stops = carica_dataset_gtfs()
            routes_filt = filtra_routes(routes, df_ottimizzato['route_id'].unique())
            trips_filt = trips[trips['route_id'].isin(routes_filt['route_id'])]
            stop_times = carica_stop_times("1Qx7jVKObRN79CLJwIy9Jzh0VwJ2D9dWZ")
            stop_times_filt = stop_times[stop_times['trip_id'].isin(trips_filt['trip_id'].unique())]

            fermate = genera_mappa_fermate(
                trips_filt, stop_times_filt, stops,
                df_ottimizzato[['route_id', 'hour']].drop_duplicates()
            )

            if not fermate.empty:
                fermate[['stop_lat', 'stop_lon']] = fermate[['stop_lat', 'stop_lon']].astype(float)
                m = folium.Map(
                    location=[fermate['stop_lat'].mean(), fermate['stop_lon'].mean()],
                    zoom_start=12
                )
                for _, r in fermate.iterrows():
                    folium.CircleMarker(
                        location=[r['stop_lat'], r['stop_lon']],
                        radius=5, color=r['color'], fill=True,
                        fill_color=r['color'], fill_opacity=0.8,
                        tooltip=r['stop_name']
                    ).add_to(m)
                st_folium(m, width=700, height=500)
                st.dataframe(
                    fermate[['route_id', 'stop_name', 'stop_lat', 'stop_lon']]
                    .drop_duplicates().sort_values(by='route_id')
                )
            else:
                st.info("Nessuna fermata trovata per i filtri selezionati.")
        except Exception as e:
            st.error(f"Errore durante la generazione della mappa fermate ottimizzate: {e}")

except Exception as e:
    st.error(f"Errore durante il caricamento dei file prescrittivi: {e}")

