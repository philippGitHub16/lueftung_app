import requests
import pandas as pd
from pvlib import solarposition
import streamlit as st
import google.generativeai as genai

# API-Key konfigurieren (Ersetze das durch deinen echten Key)
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

@st.cache_data(ttl=1800)  # Cacht das KI-Ergebnis für 30 Minuten (schont API & Ladezeit)
def hole_ki_empfehlung(temp, regen_vorschau, lqi, wind, pollen_zusammenfassung):
    # Generatives Modell auswählen (Flash ist extrem schnell)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    Du bist ein intelligenter, sympathischer Wetter- und Sport-Coach.
    Hier sind die aktuellen Daten für Mannheim:
    - Außentemperatur: {temp} °C
    - Regen in den nächsten 60 Minuten: {regen_vorschau} mm
    - Luftqualitätsindex (LQI, Skala 1-6): {lqi}
    - Windgeschwindigkeit: {wind} m/s
    - Pollenlage: {pollen_zusammenfassung}

    Erstelle daraus eine prägnante, motivierende Tagesempfehlung (maximal 3 Sätze) für mein heutiges Training und Alltag. 
    
    Regeln für deine Empfehlung:
    - Passe die Tipps an meine Sportarten an: Triathlon, Rennradfahren und Trailrunning, Laufen.
    - Wenn das Wetter matschig oder regnerisch ist und es auf die Trails geht, empfiehl mir meine Brooks Catamount 4 für den besten Grip.
    - Wenn es trocken ist und schnelle Lauf-Intervalle auf Asphalt anstehen, erwähne meine Hoka Mach 6. 
    - Wenn perfektes Trail-Wetter herrscht, schlag ruhig vor, dass ich Simon für eine gemeinsame Runde einpacke.
    - Ist die Luft extrem stickig oder heiß, mahne zur Vorsicht bei der Herzfrequenz oder schlage vor, die Watt-Ziele auf dem Rad etwas nach unten zu korrigieren.
    - Gib mir auch Hinweise zur normalen Alltagsbekleidung: Sollte ich mich eher wärmer Anziehen (geschlossene Schuhe, lange Hose, Jacken) oder sollte ich mich möglichst leicht und luftig anziehen und dafür mehr auf Sonnenschutz und -creme achten?
    
    Bleib locker, motivierend und extrem praxisnah!
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"🚨 System-Fehler: {e}"
    
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

def hole_pollenflug():
    url = "https://opendata.dwd.de/climate_environment/health/alerts/s31fg.json"
    try:
        antwort = requests.get(url).json()
        
        # Wir durchsuchen die DWD-Daten gezielt nach der Region Mannheim (ID 91)
        for region in antwort['content']:
            if region['partregion_id'] == 91:
                return region['Pollen']
                
        return None
    except Exception as e:
        return None

def hole_regen_vorhersage(lat, lon):
    # Kostenloses 15-Minuten-Regenradar von Open-Meteo
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&minutely_15=precipitation&timezone=Europe%2FBerlin&forecast_days=1"
    try:
        daten = requests.get(url).json()
        zeiten = pd.to_datetime(daten['minutely_15']['time'])
        regen = daten['minutely_15']['precipitation']
        
        df = pd.DataFrame({'zeit': zeiten, 'regen': regen})
        
        # Zeitzone setzen, um sie mit der aktuellen Uhrzeit zu vergleichen
        df['zeit'] = df['zeit'].dt.tz_localize('Europe/Berlin')
        jetzt = pd.Timestamp.now(tz='Europe/Berlin')
        
        # Wir schneiden die Vergangenheit ab und holen uns die nächsten 4 Viertelstunden
        df_zukunft = df[df['zeit'] > jetzt].head(4) 
        regen_vorschau = df_zukunft['regen'].tolist()
        
        # Falls um 23:45 Uhr nicht mehr genug Daten für heute da sind, füllen wir mit 0 auf
        while len(regen_vorschau) < 4:
            regen_vorschau.append(0.0)
            
        return regen_vorschau
    except Exception as e:
        return [0.0, 0.0, 0.0, 0.0]

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

wetter_warnungen = antwort_owm.get('alerts', [])
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

# --- Pollenflug-Daten abrufen ---
pollen_daten = hole_pollenflug()
pollen_abzug = 0
relevante_pollen = {}

if pollen_daten:
    # DWD-Skala in Zahlen übersetzen für die Berechnung
    belastung_map = {'0': 0, '0-1': 0.5, '1': 1, '1-2': 1.5, '2': 2, '2-3': 2.5, '3': 3}
    max_belastung = 0
    
    for art, daten in pollen_daten.items():
        heute_str = daten.get('today', '0')
        if heute_str == '-1': heute_str = '0' # -1 bedeutet "keine Daten"
        
        belastung_num = belastung_map.get(heute_str, 0)
        relevante_pollen[art] = heute_str
        
        if belastung_num > max_belastung:
            max_belastung = belastung_num
            
    # Score bestrafen: Ab Stufe 1.5 (mittel) fangen wir an, Punkte abzuziehen.
    # Stufe 3 (sehr hoch) zieht z.B. 30 Punkte ab und verhindert das Lüften oft komplett.
    if max_belastung >= 1.5:
        pollen_abzug = int(max_belastung * 10)
        score -= pollen_abzug

# --- REGEN-GEFAHREN-ANALYSE ---
regen_in_15m, regen_in_30m, regen_in_45m, regen_in_60m = hole_regen_vorhersage(koordinate_lat, koordinate_long)

# Dein Fenster zeigt nach 302°. 
# Wir berechnen, ob der Wind in einem 85°-Winkel von vorne oder der Seite auf das Fenster drückt.
wind_differenz = abs((wind_richtung - 302 + 180) % 360 - 180)
wind_weht_ins_fenster = wind_differenz <= 85 

# Es regnet nur rein, wenn der Wind draufsteht UND er stark genug ist (> 2 m/s)
kann_reinregnen = wind_weht_ins_fenster and wind_speed >= 2.0

regen_alarm_nachricht = None

# Wir prüfen die Niederschlagsmenge (alles ab 0.5 mm ist deutlich spürbar)
if kann_reinregnen:
    if regen_in_15m >= 0.5:
        regen_alarm_nachricht = "🚨 Akute Warnung: In unter 15 Min starker Regen, der direkt aufs Fenster drückt! Schließen!"
        score -= 100  # Veto: Das Fenster muss zu.
    elif regen_in_30m >= 0.5:
        regen_alarm_nachricht = "⚠️ Warnung: In ca. 30 Min zieht Regen aufs Fenster. Im Auge behalten!"
        score -= 40
    elif regen_in_60m >= 0.5:
        regen_alarm_nachricht = "⏱️ Hinweis: In einer Stunde wird Frontal-Regen erwartet."
        score -= 15

if wetter_warnungen:
    for warnung in wetter_warnungen:
        warn_text = warnung.get('event', 'Unwetterwarnung')
        st.error(f"🚨 ACHTUNG (Offizielle Warnung): {warn_text}")
if regen_alarm_nachricht:
    if "Akute Warnung" in regen_alarm_nachricht:
        st.error(regen_alarm_nachricht)
    else:
        st.warning(regen_alarm_nachricht)

# Dein bisheriger Entscheidungsbaum
if regnet_es and wind_speed > 5 and (wind_richtung <= 10 or wind_richtung >= 245):
    st.error("🚨 Not-Aus: Es regnet bereits stark auf das Fenster. Schotten dicht!")
elif score >= 50:
    st.success("✅ Es ist sicher und kühlend. Jetzt lüften!")
else:
    st.info("⏳ Besser noch warten, die Bedingungen passen noch nicht perfekt.")

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

# Aktiven LQI sicherstellen (Fallback auf 1.0, falls die API kurz hängt)
aktiver_lqi = float(lqi_wert) if lqi_wert else 1.0

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
        🏙️ Luftqualität (Friedrichsring)
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

st.subheader("🌿 Pollenflug (Mannheim)")

if pollen_daten:
    # Nur Pollen herausfiltern, die aktuell > 0 sind
    fliegende_pollen = {art: belastung for art, belastung in relevante_pollen.items() if belastung != '0'}
    
    if fliegende_pollen:
        # Wir erzeugen dynamisch Spalten, maximal 4 in einer Reihe
        cols = st.columns(4)
        col_idx = 0
        
        for art, belastung in fliegende_pollen.items():
            with cols[col_idx % 4]:
                st.metric(art, f"Stufe {belastung}")
            col_idx += 1
            
        if pollen_abzug > 0:
            st.warning(f"Achtung: Aufgrund der Pollenbelastung wurde der Lüftungs-Score um {pollen_abzug} Punkte gesenkt.")
    else:
        st.success("Aktuell kein relevanter Pollenflug. Freies Durchatmen!")
else:
    st.info("Pollen-Daten vom DWD werden gerade aktualisiert.")

# --- KI-EMPFEHLUNG GENERIEREN ---

# Pollen-Daten für den Prompt als Text aufbereiten
if 'relevante_pollen' in locals() and relevante_pollen:
    pollen_text = ", ".join([f"{art}: Stufe {bel}" for art, bel in relevante_pollen.items() if bel != '0'])
    if not pollen_text:
        pollen_text = "Keine relevanten Pollen"
else:
    pollen_text = "Keine Daten verfügbar"

# KI-Text abrufen
ki_tipp = hole_ki_empfehlung(
    round(aussen_temp, 1),
    [regen_in_15m, regen_in_30m, regen_in_45m, regen_in_60m],
    aktiver_lqi,
    wind_speed,
    pollen_text
)

# Prominent als Infobox anzeigen
st.info(f"**KI-Tages-Coach:** {ki_tipp}")