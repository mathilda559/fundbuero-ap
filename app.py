import streamlit as st
from PIL import Image
import sqlite3
import os
from datetime import datetime
from transformers import pipeline

# ===== Setup =====
st.set_page_config(page_title="Digitales Fundbüro", layout="centered")

if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Datenbank
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT,
    image_path TEXT,
    timestamp TEXT
)
""")
conn.commit()

# KI Modell (schnell + gut)
classifier = pipeline("image-classification", model="google/vit-base-patch16-224")

# ===== UI =====
st.title("🔎 Digitales Fundbüro")

menu = st.sidebar.selectbox("Menü", ["Hochladen", "Gefundene Objekte"])

# ===== Upload =====
if menu == "Hochladen":
    st.header("📤 Objekt hochladen")

    uploaded_file = st.file_uploader("Bild auswählen", type=["jpg", "png", "jpeg"])

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Hochgeladenes Bild", use_column_width=True)

        if st.button("Analysieren"):
            with st.spinner("KI analysiert das Bild..."):
                result = classifier(image)
                label = result[0]["label"]

                # Bild speichern
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                file_path = f"uploads/{timestamp}.png"
                image.save(file_path)

                # In DB speichern
                c.execute("INSERT INTO items (label, image_path, timestamp) VALUES (?, ?, ?)",
                          (label, file_path, timestamp))
                conn.commit()

                st.success(f"Erkannt: {label}")

# ===== Anzeige + Suche =====
elif menu == "Gefundene Objekte":
    st.header("📋 Gefundene Objekte")

    search = st.text_input("🔍 Suche nach Objekt")

    if search:
        c.execute("SELECT * FROM items WHERE label LIKE ?", ('%' + search + '%',))
    else:
        c.execute("SELECT * FROM items ORDER BY id DESC")

    items = c.fetchall()

    for item in items:
        st.image(item[2], width=200)
        st.write(f"**Objekt:** {item[1]}")
        st.write(f"**Zeit:** {item[3]}")
        st.markdown("---")
