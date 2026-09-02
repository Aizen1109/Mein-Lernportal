import os
import streamlit as st
from google import genai
from google.genai import types

# ------------------------------------------------------------------------------
# PAGE CONFIGURATION
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Learning Portal & Agent Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS für modernes Dark-Design
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stCard {
        background-color: #1e222d;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #2e3440;
        margin-bottom: 15px;
    }
    h1, h2, h3 { color: #5e81ac !important; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# INITIALIZATION & SIDEBAR
# ------------------------------------------------------------------------------
st.sidebar.title("🤖 Agenten-Steuerung")

# API Key automatisch aus den Streamlit Secrets laden oder manuell eingeben
api_key = st.secrets.get("GEMINI_API_KEY") or st.sidebar.text_input(
    "Gemini API Key", 
    type="password", 
    help="Trage hier deinen Google Gemini API Key ein oder hinterlege ihn in den Streamlit Secrets."
)

if not api_key:
    st.sidebar.warning("⚠️ Bitte hinterlege deinen API Key in den Streamlit Secrets oder trage ihn oben ein.")
    st.info("👋 Willkommen in deinem persönlichen AI-Lernportal! Bitte trage deinen API-Key ein, um zu starten.")
    st.stop()

client = genai.Client(api_key=api_key)

# System-Prompts für die Agenten anpassen
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Agenten-Konfiguration")
custom_summary_prompt = st.sidebar.text_area(
    "Lernzettel-Anweisung (System Prompt)",
    value="""Erstelle einen perfekten, hochstrukturierten Lernzettel für ein Universitätsstudium.
Struktur:
1. Kernthema & Kurzzusammenfassung
2. Wichtige Definitionen & Begriffe
3. Formeln & Rechenwege (falls vorhanden, in LaTeX)
4. Praxis- & Anwendungsbeispiele
5. Typische Klausur-Fallen & Merksätze"""
)

# ------------------------------------------------------------------------------
# MAIN INTERFACE
# ------------------------------------------------------------------------------
st.title("🎓 AI Learning Portal")
st.caption("Erstelle automatisiert Lernzettel aus Skripten & simuliere Klausuraufgaben.")

tabs = st.tabs(["📄 Skript-Upload & Lernzettel", "🧪 Klausur-Simulation", "📚 Meine Module"])

# ------------------------------------------------------------------------------
# TAB 1: UPLOAD & LERNZETTEL-GENERATOR
# ------------------------------------------------------------------------------
with tabs[0]:
    st.header("1. Material hochladen & Lernzettel generieren")
    
    uploaded_files = st.file_uploader(
        "Lade Vorlesungsskripte (PDF) oder Bilder/Fotos hoch:",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True
    )
    
    module_name = st.text_input("Modul-/Fachthema (z. B. VWL Grundlagen, Wirtschaftsinformatik):", "VWL Grundlagen")
    
    if st.button("🚀 Lernzettel jetzt generieren", type="primary"):
        if not uploaded_files:
            st.error("Bitte lade mindestens eine Datei oder ein Bild hoch.")
        else:
            with st.spinner("Agent verarbeitet deine Dokumente und erstellt den Lernzettel..."):
                try:
                    # Dateien für die API aufbereiten
                    contents = [custom_summary_prompt, f"Thema: {module_name}"]
                    for file in uploaded_files:
                        bytes_data = file.read()
                        mime_type = file.type
                        contents.append(
                            types.Part.from_bytes(data=bytes_data, mime_type=mime_type)
                        )
                    
                    # Gemini Model aufrufen
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=contents,
                    )
                    
                    st.session_state["last_summary"] = response.text
                    st.success("Lernzettel erfolgreich erstellt!")
                except Exception as e:
                    st.error(f"Fehler bei der Generierung: {e}")

    if "last_summary" in st.session_state:
        st.markdown("---")
        st.subheader(f"📌 Generierter Lernzettel: {module_name}")
        st.markdown(st.session_state["last_summary"])
        st.download_button(
            label="💾 Lernzettel als Markdown herunterladen",
            data=st.session_state["last_summary"],
            file_name=f"Lernzettel_{module_name.replace(' ', '_')}.md",
            mime="text/markdown"
        )

# ------------------------------------------------------------------------------
# TAB 2: KLAUSUR-SIMULATION
# ------------------------------------------------------------------------------
with tabs[1]:
    st.header("2. Interaktive Klausur-Simulation")
    
    if "last_summary" not in st.session_state:
        st.info("Bitte generiere zuerst im ersten Tab einen Lernzettel aus deinen Unterlagen.")
    else:
        st.write("Der Simulation-Agent generiert Prüfungsfragen basierend auf deinem aktuellen Lernzettel.")
        
        if st.button("🎲 Neue Klausuraufgaben generieren"):
            with st.spinner("Klausurfragen werden erstellt..."):
                quiz_prompt = f"""Basierend auf folgendem Lernstoff, erstelle 3 typische Klausuraufgaben für ein Hochschulstudium:
1. Eine Definitions-/Freitextfrage
2. Eine Transfer-/Anwendungsaufgabe
3. Eine Rechen- oder Szenarioaufgabe

Lernstoff:
{st.session_state['last_summary']}

Formatiere die Fragen klar und verständlich."""

                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=[quiz_prompt]
                )
                st.session_state["current_quiz"] = response.text

        if "current_quiz" in st.session_state:
            st.markdown("### 📝 Deine Prüfungsaufgaben:")
            st.markdown(st.session_state["current_quiz"])
            
            st.markdown("---")
            user_answers = st.text_area("Schreibe hier deine Antworten rein, um sie bewerten zu lassen:", height=200)
            
            if st.button("📊 Antworten prüfen & Feedback erhalten"):
                if not user_answers:
                    st.warning("Bitte trage deine Antworten ein.")
                else:
                    with st.spinner("Agent wertet deine Antworten aus..."):
                        eval_prompt = f"""Du bist ein Universitätsprofessor. Bewerte die folgenden Antworten des Studenten zu den gestellten Fragen.

Geforderte Fragen:
{st.session_state['current_quiz']}

Antworten des Studenten:
{user_answers}

Gib eine detaillierte Korrektur, vergib Punkte/Prozentangaben und erkläre eventuelle Fehler genau."""

                        eval_response = client.models.generate_content(
                            model="gemini-3.6-flash",
                            contents=[eval_prompt]
                        )
                        st.markdown("### 🎯 Bewertung & Korrektur:")
                        st.markdown(eval_response.text)

# ------------------------------------------------------------------------------
# TAB 3: MODULE & ARCHIV
# ------------------------------------------------------------------------------
with tabs[2]:
    st.header("3. Modulübersicht")
    st.write("Hier kannst du deine erstellten Lernzettel verwalten.")
    if "last_summary" in st.session_state:
        st.success(f"Aktuell geladenes Thema: **{module_name}**")
    else:
        st.write("Noch keine aktiven Module geladen.")
