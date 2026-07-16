import requests # internetverbindung für API
import pandas as pd # Datenanalysen und Tabellen in python
import pvlib # Bibliothek aus Photovotaik-Forschung
import streamlit as st # grafische Oberfläche

# --- STREAMLIT OBERFLÄCHE ---
st.title("🌬️ Meine Lüftungs-App")
innen_temp = st.slider("Wie warm ist es aktuell drinnen? (°C)", min_value=7, max_value=40, value=25, step=1)

## Wetter API
API_KEY = "9ee7e41d71cdbf876ad44bca100bdc86"  # <-- WICHTIG: Tausche das gegen deinen OpenWeatherMap-Schlüssel
STADT = "Mannheim"
url = f"http://api.openweathermap.org/data/2.5/weather?q={STADT}&appid={API_KEY}&units=metric&lang=de"
antwort = requests.get(url)
if antwort.status_code == 200:
    wetter_daten = antwort.json()

#Variablen
## Koordinaten & Uhrzeit
koordinate_lat = 49.4964        ## mein Fenster zeigt nach 302°, https://www.sonnenverlauf.de/#/49.4963,8.4874,19/2026.07.16/13:29/1/1
koordinate_long = 8.4874
jetzt = pd.Timestamp.now(tz='Europe/Berlin')

## Wetterdaten
aussen_temp = wetter_daten["main"]["temp"]
wetter_beschreibung = wetter_daten["weather"][0]["description"]
sonnen_daten = pvlib.solarposition.get_solarposition(jetzt, koordinate_lat, koordinate_long)
aktueller_azimut = sonnen_daten['azimuth'].iloc[0]
regnet_es = "regen" in wetter_beschreibung.lower()
wind_speed = wetter_daten["wind"]["speed"]
wind_richtung = wetter_daten["wind"]["deg"]
luftfeuchtigkeit = wetter_daten["main"]["humidity"]
taupunkt = aussen_temp - ((100-luftfeuchtigkeit)/5)
bewoelkung = wetter_daten["clouds"]["all"]

## Scoring-System
score = 0
if aussen_temp < innen_temp:
    score += 50 
if 210 <= aktueller_azimut <= 342 and bewoelkung < 50: 
    score -= 25
if taupunkt > 16:
    score -= 20
if wind_speed > 3 and (wind_richtung <= 10 or wind_richtung >= 245):
    score += 20

## Streamlit Dashboard
st.subheader("Aktuelle Daten")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Außentemperatur", f"{round(aussen_temp)} °C")
    st.caption(f"Windrichtung: {wind_richtung}°") 
    st.caption(f"Wind: {wind_speed} m/s")
with col2:
    st.metric("Innentemperatur", f"{round(innen_temp)} °C")
    st.caption(f"Azimuth: {round(aktueller_azimut)}°")
col3.metric("Score", score)

st.subheader("Entscheidung")
if regnet_es and wind_speed > 5 and (wind_richtung <= 10 or wind_richtung >= 245):
    st.error("🚨 Not-Aus: Zu starker Regen auf dem Fenster. Schotten dicht!")
elif score >= 50:
    st.success("✅ Es ist sicher und kühlend. Jetzt lüften!")
else:
    st.warning("⏳ Besser noch warten, die Bedingungen passen noch nicht.")
