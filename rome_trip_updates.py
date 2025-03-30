from gtfs_realtime_pb2 import FeedMessage
from datetime import datetime, timezone
import pytz
import pandas as pd  

# Percorso dei file
file_path = "C:/Users/C.Marino/Desktop/rome_trip_updates.pb"
output_txt_path = "C:/Users/C.Marino/Desktop/trip_updates.txt"

#Fuso orario italiano
italian_timezone = pytz.timezone("Europe/Rome")


feed = FeedMessage()

# Leggi il file .pb
with open(file_path, "rb") as f:
    feed.ParseFromString(f.read())

# Apre il file .txt per scrivere i dati
with open(output_txt_path, mode='w') as txt_file:
    # Scrive l'intestazione
    txt_file.write("trip_id,stop_id,arrival_date,arrival_time,arrival_time_utc\n")
    
    # Estrae i dati e scrive nel file
    for entity in feed.entity:
        if entity.trip_update:
            trip_id = entity.trip_update.trip.trip_id
            for stop_time_update in entity.trip_update.stop_time_update:
                stop_id = stop_time_update.stop_id
                arrival_time = stop_time_update.arrival.time  

                # Controlla e converte il timestamp
                if arrival_time > 0:
                    
                    
                    dt_utc = datetime.fromtimestamp(arrival_time, timezone.utc)
                    dt_local = dt_utc.astimezone(italian_timezone)
                    arrival_date = dt_local.strftime('%Y-%m-%d')
                    arrival_time_only = dt_local.strftime('%H:%M:%S')

                    # Scrive i dati nel file, includendo il timestamp e l'ora locale
                    txt_file.write(f"{trip_id},{stop_id},{arrival_date},{arrival_time_only}\n")

print(f"Dati esportati correttamente nel file TXT: {output_txt_path}")
