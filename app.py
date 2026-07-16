import requests # internetverbindung für API
import pandas as pd # Datenanalysen und Tabellen in python
import pvlib # Bibliothek aus Photovotaik-Forschung
import streamlit as st # grafische Oberfläche


## Wetter API
API_KEY = "9ee7e41d71cdbf876ad44bca100bdc86"  # <-- WICHTIG: Tausche das gegen deinen OpenWeatherMap-Schlüssel
STADT = "Mannheim"
url = f"http://api.openweathermap.org/data/2.5/weather?q={STADT}&appid={API_KEY}&units=metric&lang=de"
antwort = requests.get(url)
if antwort.status_code == 200:
    wetter_daten = antwort.json()

#Variablen
## Koordinaten & Uhrzeit
koordinate_lat = 49.4964
koordinate_long = 8.4874
jetzt = pd.Timestamp.now(tz='Europe/Berlin')

## Wetterdaten
innen_temp = 27.0 
aussen_temp = wetter_daten["main"]["temp"]
wetter_beschreibung = wetter_daten["weather"][0]["description"]
sonnen_daten = pvlib.solarposition.get_solarposition(jetzt, koordinate_lat, koordinate_long)
aktueller_azimut = sonnen_daten['azimuth'].iloc[0]
regnet_es = "regen" in wetter_beschreibung.lower()
wind_speed = wetter_daten["wind"]["speed"]
wind_richtung = wetter_daten["wind"]["deg"]
luftfeuchtigkeit = wetter_daten["main"]["humidity"]
taupunkt = aussen_temp - ((100-luftfeuchtigkeit)/5)

## Scoring-System
score = 0
if aussen_temp < innen_temp:
    score += 50 
if 220 <= aktueller_azimut <= 290:
    score -= 20
if taupunkt > 16:
    score -= 20
if wind_richtung > 3 and 245 <= wind_richtung <= 335:
    score += 20


# --- STREAMLIT OBERFLÄCHE ---
st.title("🌬️ Meine Lüftungs-App")

st.subheader("Aktuelle Daten")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Außentemperatur", f"{aussen_temp} °C")
    st.caption(f"Windrichtung: {wind_richtung}°") 
    st.caption(f"Wind: {wind_speed} m/s")
col2.metric("Innen", f"{innen_temp} °C")
col3.metric("Score", score)

st.subheader("Entscheidung")
if regnet_es and wind_speed > 5 and 245 <= wind_richtung <= 335:
    st.error("🚨 Not-Aus: Zu starker Regen auf dem Fenster. Schotten dicht!")
elif score >= 50:
    st.success("✅ Es ist sicher und kühlend. Jetzt lüften!")
else:
    st.warning("⏳ Besser noch warten, die Bedingungen passen noch nicht.")
