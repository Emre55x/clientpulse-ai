import streamlit as st
import openai
import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# Geheimnisse laden
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# ---------------------------------------------------------
# DATENBANK SETUP (Das "Gedächtnis")
# ---------------------------------------------------------
def init_db():
    # Verbindet sich mit der Datenbank (oder erstellt sie neu)
    conn = sqlite3.connect("kundenbank.db")
    c = conn.cursor()
    # Erstellt die Tabelle 'kunden', falls sie noch nicht existiert
    c.execute('''CREATE TABLE IF NOT EXISTS kunden
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  rohe_notizen TEXT,
                  ki_analyse TEXT,
                  datum TEXT)''')
    conn.commit()
    conn.close()

# Startet die Datenbank beim Laden der App
init_db()

# ---------------------------------------------------------
# BENUTZEROBERFLÄCHE
# ---------------------------------------------------------
st.title("ClientPulse AI")
st.write("Dein digitaler Assistent für Kundennotizen im Vertrieb.")

# Wir erstellen zwei Reiter (Tabs) für mehr Übersicht
tab1, tab2 = st.tabs(["Neue Notiz erfassen", "Kunden-Datenbank & Suche"])

# --- TAB 1: DATENEINGABE ---
with tab1:
    st.subheader("1. Neuen Kunden analysieren und speichern")
    
    # Neues Feld: Wir brauchen den Namen für die Datenbank-Suche
    kunden_name = st.text_input("Name des Kunden (z.B. Herr Schmitz):")
    raw_notes = st.text_area("Kopiere hier deine Gesprächsnotizen rein:", height=150)

    if st.button("Notizen strukturieren & Speichern"):
        if raw_notes and kunden_name:
            if not api_key or api_key == "sk-DeinKopierterSchluesselHier":
                st.error("Bitte trage deinen echten OpenAI API-Schlüssel in die .env Datei ein!")
            else:
                try:
                    client = openai.OpenAI(api_key=api_key)
                    
                    anweisung = """
                    Du bist ein Assistent für Versicherungsvertreter. 
                    Lies die folgenden Notizen und extrahiere:
                    1. Produktinteresse
                    2. Nächster Schritt
                    3. Soft Facts (Hobbys, Urlaub, Familie)
                    4. Einen kurzen, freundlichen Icebreaker-Satz für den nächsten Anruf.
                    Formatiere die Antwort übersichtlich in Stichpunkten.
                    """
                    
                    with st.spinner('KI analysiert und speichert die Notizen...'):
                        antwort = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": anweisung},
                                {"role": "user", "content": raw_notes}
                            ]
                        )
                    
                    # KI Antwort als Text speichern
                    ki_text = antwort.choices[0].message.content
                    
                    # In die Datenbank speichern
                    conn = sqlite3.connect("kundenbank.db")
                    c = conn.cursor()
                    heute = datetime.now().strftime("%d.%m.%Y %H:%M")
                    c.execute("INSERT INTO kunden (name, rohe_notizen, ki_analyse, datum) VALUES (?, ?, ?, ?)", 
                              (kunden_name, raw_notes, ki_text, heute))
                    conn.commit()
                    conn.close()

                    st.success(f"Erfolg! Die Notizen zu {kunden_name} wurden analysiert und sicher in der Datenbank gespeichert.")
                    
                    st.subheader("Ergebnis der Analyse:")
                    st.write(ki_text)
                    
                except Exception as e:
                    st.error(f"Es gab einen Fehler bei der KI-Abfrage: {e}")
                    
        else:
            st.warning("Bitte gib einen Kundennamen und Notizen ein.")

# --- TAB 2: DATENBANK & SUCHE ---
with tab2:
    st.subheader("2. Gesammelte Kundeninformationen")
    
    # Das Suchfeld
    suchbegriff = st.text_input("Suche nach einem Kunden (z.B. Schmitz):")
    
    # Daten aus der Datenbank laden
    conn = sqlite3.connect("kundenbank.db")
    c = conn.cursor()
    
    if suchbegriff:
        # Sucht nach Namen, die den Suchbegriff enthalten
        c.execute("SELECT name, datum, ki_analyse FROM kunden WHERE name LIKE ?", ('%' + suchbegriff + '%',))
    else:
        # Zeigt alle Kunden an, die neuesten zuerst
        c.execute("SELECT name, datum, ki_analyse FROM kunden ORDER BY id DESC")
        
    ergebnisse = c.fetchall()
    conn.close()
    
    # Ergebnisse hübsch anzeigen
    if ergebnisse:
        for kunde in ergebnisse:
            # Ein ausklappbares Feld (Expander) für jeden Kunden
            with st.expander(f"Kunde: {kunde[0]} (Gespeichert am: {kunde[1]})"):
                st.write(kunde[2])
    else:
        st.info("Bisher keine Kunden gefunden. Erfasse zuerst eine neue Notiz im ersten Tab!")