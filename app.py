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

def hole_luftqualitaet():
    jetzt = pd.Timestamp.now(tz='UTC')
    vor_24h = jetzt - pd.Timedelta(hours=24)
    zeit_bis = jetzt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    zeit_von = vor_24h.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    url = "https://apps.mvvsmartcities.com/api/dashboarddata?accountId=5f6c5c377f1cff0011096a73&id=luftqualitaetsindex_mannheim"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    basis_payload = {
        "from": zeit_von, "to": zeit_bis,
        "accountId": "5f6c5c377f1cff0011096a73", "orient": "analytics",
        "timezone": "Europe/Berlin", "appId": "luftqualitaetsindex_mannheim",
        "entityId": "cc854fd0-68cf-476c-bba6-b7abea28b78c"
    }

    # 1. Luftqualitätsindex (LQI)
    payload_lqi = basis_payload.copy()
    payload_lqi.update({
        "dashboardTemplateTileId": "cedcb9bd-43f8-412d-9065-a35e1039de48", 
        "timeseries": [{"timeSeriesId": "ba078a34-c4ea-4413-a095-b6e528a7bfce", "aggregationFunction": "", "gapFill": "None", "displayName": "UBA - Mannheim Friedrichsring, Luftqualitätsindex", "displayDigits": 2, "definitionType": "timeseries"}]
    })
    
    # 2. Stickstoffdioxid (NO2)
    payload_no2 = basis_payload.copy()
    payload_no2.update({
        "dashboardTemplateTileId": "486286c3-5a13-489b-8657-39e735d43929", 
        "timeseries": [{"timeSeriesId": "de25fb29-a688-4e02-9439-3fe047a717e2", "aggregationFunction": "", "gapFill": "None", "displayName": "UBA - Mannheim Friedrichsring, Stickstoffdioxid NO₂", "displayDigits": 0, "definitionType": "timeseries"}]
    })
    
    # 3. Feinstaub (PM2.5)
    payload_pm = basis_payload.copy()
    payload_pm.update({
        "dashboardTemplateTileId": "af753dcf-f714-4db1-aeb9-5f8026d9be25", 
        "timeseries": [{"timeSeriesId": "dae5ff37-89b3-4055-b170-441b20957fe9", "aggregationFunction": "", "gapFill": "None", "displayName": "UBA - Mannheim Friedrichsring, Feinstaub PM₂,₅", "displayDigits": 0, "definitionType": "timeseries"}]
    })

    try:
        lqi = requests.post(url, headers=headers, json=payload_lqi).json()[0]['indicator']
        no2 = requests.post(url, headers=headers, json=payload_no2).json()[0]['indicator']
        pm25 = requests.post(url, headers=headers, json=payload_pm).json()[0]['indicator']
        return lqi, no2, pm25
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

# Luftqualität vom Friedrichsring holen
lqi_wert, no2_wert, pm25_wert = hole_luftqualitaet()

# 4. Fallback: Falls MVV down ist, springt OpenWeather ein
if aussen_temp is None:
    aussen_temp = antwort_owm['main']['temp']
    aussen_feucht = antwort_owm['main']['humidity']
    wind_speed = antwort_owm['wind']['speed']

# 5. Finale Berechnungen 
taupunkt = aussen_temp - ((100 - aussen_feucht) / 5)

## Scoring-System
score = 0

# 1. Temperatur-Differenz (Das Hauptargument)
if aussen_temp < (innen_temp + 5):
    score += 60 

# 2. Sonnen-Strahlenschutz (Abzug, wenn die Sonne direkt aufs Fenster knallt)
if 260 <= aktueller_azimut <= 342 and sonnen_hoehe > 0 and bewoelkung < 30:
    score -= 20

# 3. Schwüle-Faktor (Abzug bei hoher Feuchtigkeit/Taupunkt)
if taupunkt > 16:
    score -= 20

# 4. Wind-Turbo (Angepasst an die realistische Stadtsensor-Messung)
# Da Laternenmast-Sensoren selten über 3 m/s kommen, reicht hier schon leichter Wind ab 0.8 m/s
if wind_speed > 0.8 and (wind_richtung <= 60 or wind_richtung >= 180):
    score += 25

# 5. NEU: Windstille-Bonus bei Kühle (Wenn es kühl ist, ist Wind egal – frische Luft zieht auch so rein)
elif wind_speed <= 0.8 and aussen_temp < (innen_temp - 1):
    score += 20

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

# --- LQI-Test-Modus ---
test_modus = st.checkbox("Test-Modus LQI", value=True)
if test_modus:
    simulierter_lqi = st.slider("Simulierter LQI-Wert (UBA Skala)", 1.0, 6.0, float(lqi_wert) if lqi_wert else 2.2, step=0.1)
    aktiver_lqi = simulierter_lqi
else:
    aktiver_lqi = lqi_wert if lqi_wert else 1.0

# Nebel-Stärke berechnen (1 = klar, 6 = starker Schleier)
nebel_staerke = max(0.0, min(((aktiver_lqi - 1) / 5.0) * 0.8, 0.8))

# Der komplette Block als ein zusammenhängendes HTML-Element
html_code = f"""
<div style="
    background-color: rgba(120, 120, 120, {nebel_staerke});
    padding: 20px;
    border-radius: 10px;
    transition: background-color 0.3s ease;
    margin-top: 1rem;
    margin-bottom: 1rem;
">
    <h3 style="margin-top: 0; margin-bottom: 20px; font-family: sans-serif; font-size: 1.5rem; font-weight: 600;">
        Luftqualität (Friedrichsring)
    </h3>
    <div style="display: flex; flex-wrap: wrap; gap: 20px; font-family: sans-serif;">
        <div style="flex: 1; min-width: 120px;">
            <div style="font-size: 0.9rem; color: #555; margin-bottom: 5px;">Luftqualitätsindex (LQI)</div>
            <div style="font-size: 1.8rem; font-weight: bold;">{aktiver_lqi}</div>
        </div>
        <div style="flex: 1; min-width: 120px;">
            <div style="font-size: 0.9rem; color: #555; margin-bottom: 5px;">Stickstoffdioxid (NO₂)</div>
            <div style="font-size: 1.8rem; font-weight: bold;">{no2_wert if no2_wert else "N/A"} µg/m³</div>
        </div>
        <div style="flex: 1; min-width: 120px;">
            <div style="font-size: 0.9rem; color: #555; margin-bottom: 5px;">Feinstaub (PM₂.₅)</div>
            <div style="font-size: 1.8rem; font-weight: bold;">{pm25_wert if pm25_wert else "N/A"} µg/m³</div>
        </div>
    </div>
</div>
"""

# HTML im Dashboard ausgeben
st.markdown(html_code, unsafe_allow_html=True)