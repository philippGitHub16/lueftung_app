import requests
import pandas as pd
from pvlib import solarposition
import streamlit as st

def hole_mvv_sensoren():
    # Zeitstempel für die API vorbereiten
    jetzt = pd.Timestamp.now(tz='UTC')
    vor_einer_stunde = jetzt - pd.Timedelta(hours=1)
    zeit_bis = jetzt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    zeit_von = vor_einer_stunde.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    url = "https://apps.mvvsmartcities.com/api/dashboarddata?accountId=6233165a7faac33eade2c539&id=268b1470-a99b-4244-942e-d8fbdba033ab"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    basis_payload = {
        "from": zeit_von, "to": zeit_bis,
        "accountId": "6233165a7faac33eade2c539", "orient": "analytics",
        "timezone": "Europe/Berlin", "appId": "268b1470-a99b-4244-942e-d8fbdba033ab",
        "entityId": "39465b34-3e8e-e40b-9cfc-fc43b0aa0e60"
    }

    payload_temp = basis_payload.copy()
    payload_temp.update({"dashboardTemplateTileId": "b56d6160-6cf4-48fa-be5a-51581216d1a2", "timeseries": [{"timeSeriesId": "536a8e89-34c6-4a23-8bac-dec7ae840ee0", "aggregationFunction": "", "gapFill": "None", "displayName": "Klimasensor, Temperatur", "numDigits": 1, "definitionType": "timeseries"}]})
    
    payload_feucht = basis_payload.copy()
    payload_feucht.update({"dashboardTemplateTileId": "930d05a5-cefe-4dda-9190-db40cf82abbc", "timeseries": [{"timeSeriesId": "de1bedd9-1b2c-40ea-8434-ca7895362ef3", "aggregationFunction": "", "gapFill": "None", "displayName": "Klimasensor, Luftfeuchtigkeit", "numDigits": 0, "definitionType": "timeseries"}]})
    
    payload_wind = basis_payload.copy()
    payload_wind.update({"dashboardTemplateTileId": "13c34302-b5e3-433c-8602-aed08d7cf390", "timeseries": [{"timeSeriesId": "af7132bc-38e7-425f-8695-a8a94701a4b6", "aggregationFunction": "", "gapFill": "None", "displayName": " 2305LW012, Durchschn. Windgeschwindigkeit", "displayDigits": 1, "definitionType": "timeseries"}]})

    try:
        temp = requests.post(url, headers=headers, json=payload_temp).json()[0]['indicator']
        feucht = requests.post(url, headers=headers, json=payload_feucht).json()[0]['indicator']
        wind = requests.post(url, headers=headers, json=payload_wind).json()[0]['indicator']
        return temp, feucht, wind
    except Exception as e:
        return None, None, None

# --- STREAMLIT OBERFLÄCHE ---
st.title("🌬️ Meine Lüftungs-App")
st.subheader("🌡️ Temperatur einstellen")
innen_temp = st.slider("Wie warm ist es aktuell drinnen? (°C)", min_value=7, max_value=40, value=25, step=1)

## Koordinaten & Uhrzeit
koordinate_lat = 49.4964  # mein Fenster zeigt nach 302°
koordinate_long = 8.4874
jetzt = pd.Timestamp.now(tz='Europe/Berlin')

# 1. Sonnenstand berechnen
sonnen_daten = solarposition.get_solarposition(jetzt, koordinate_lat, koordinate_long)
aktueller_azimut = sonnen_daten['azimuth'].iloc[0]
sonnen_hoehe = sonnen_daten['elevation'].iloc[0]  

# 2. Wetterdaten holen (OpenWeatherMap für Regen/Wolken)
API_KEY = "9ee7e41d71cdbf876ad44bca100bdc86"
url_owm = f"http://api.openweathermap.org/data/2.5/weather?lat={koordinate_lat}&lon={koordinate_long}&appid={API_KEY}&units=metric&lang=de"
antwort_owm = requests.get(url_owm).json()

bewoelkung = antwort_owm['clouds']['all']
wetter_beschreibung = antwort_owm['weather'][0]['description']
regnet_es = "regen" in wetter_beschreibung.lower()
wind_richtung = antwort_owm['wind']['deg']

# 3. Lokale Premium-Daten von der MVV holen
aussen_temp, aussen_feucht, wind_speed = hole_mvv_sensoren()

# 4. Fallback: Falls MVV down ist, springt OpenWeather ein
if aussen_temp is None:
    aussen_temp = antwort_owm['main']['temp']
    aussen_feucht = antwort_owm['main']['humidity']
    wind_speed = antwort_owm['wind']['speed']

# 5. Finale Berechnungen 
taupunkt = aussen_temp - ((100 - aussen_feucht) / 5)

## Scoring-System
score = 0
if aussen_temp < (innen_temp + 5):
    score += 60 
if 260 <= aktueller_azimut <= 342 and sonnen_hoehe > 0 and bewoelkung < 50:
    score -= 20
if taupunkt > 16:
    score -= 20
if wind_speed > 3 and (wind_richtung <= 30 or wind_richtung >= 200):
    score += 25

st.subheader("Entscheidung")
if regnet_es and wind_speed > 5 and (wind_richtung <= 10 or wind_richtung >= 245):
    st.error("🚨 Not-Aus: Zu starker Regen auf dem Fenster. Schotten dicht!")
elif score >= 50:
    st.success("✅ Es ist sicher und kühlend. Jetzt lüften!")
else:
    st.warning("⏳ Besser noch warten, die Bedingungen passen noch nicht.")

## Streamlit Dashboard
st.subheader("Aktuelle Daten")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Außentemperatur", f"{round(aussen_temp, 1)} °C")
    st.caption(f"Azimuth: {round(aktueller_azimut, 1)}°")
    st.metric("Score", score)
with col2:
    st.metric("Windstärke", f"{wind_speed} m/s")
    st.metric("Windrichtung", f"{wind_richtung}°")
with col3:
    if regnet_es:
        st.metric("Regen", "Ja")
    else:
        st.metric("Regen", "Nein")
    st.metric("Bewölkung", f"{bewoelkung}%")