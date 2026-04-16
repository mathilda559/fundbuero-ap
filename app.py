import streamlit as st
from PIL import Image
import sqlite3
import os
from datetime import datetime
from transformers import pipeline

# ===== CONFIG =====
st.set_page_config(page_title="Fundbüro", page_icon="🔎", layout="wide")

# ===== CSS =====
st.markdown("""
<style>
.card {
    background-color: white;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ===== PATH =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_PATH = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_PATH, exist_ok=True)

# ===== DB =====
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT,
    confidence REAL,
    image_path TEXT,
    timestamp TEXT,
    status TEXT
)
""")
conn.commit()

# ===== MODEL =====
classifier = pipeline("image-classification", model="google/vit-base-patch16-224")

# ===== SIDEBAR =====
st.sidebar.title("📂 Navigation")
menu = st.sidebar.radio("", ["Hochladen", "Fundstücke", "Abgeholt"])

# ===== TIME FORMAT =====
def format_time(ts):
    dt = datetime.strptime(ts, "%Y%m%d%H%M%S")
    return dt.strftime("%d.%m.%Y – %H:%M")

# ===== UPLOAD =====
if menu == "Hochladen":
    st.title("📤 Fundstück hochladen")

    uploaded_file = st.file_uploader("Bild auswählen", type=["jpg", "png", "jpeg"])

    if uploaded_file:
        image = Image.open(uploaded_file)

        col1, col2 = st.columns(2)

        with col1:
            st.image(image, use_column_width=True)

        with col2:
            if st.button("🔍 Analysieren"):
                result = classifier(image)[0]

                label = result["label"]
                confidence = round(result["score"] * 100, 2)

                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                file_path = os.path.join(UPLOAD_PATH, f"{timestamp}.png")
                image.save(file_path)

                c.execute("""
                INSERT INTO items (label, confidence, image_path, timestamp, status)
                VALUES (?, ?, ?, ?, ?)
                """, (label, confidence, file_path, timestamp, "gefunden"))

                conn.commit()

                st.success(f"Erkannt: {label} ({confidence}%)")

# ===== FUNDSTÜCKE =====
elif menu == "Fundstücke":
    st.title("📋 Gefundene Objekte")

    search = st.text_input("🔍 Suche")

    if search:
        c.execute("SELECT * FROM items WHERE label LIKE ? AND status='gefunden'", ('%' + search + '%',))
    else:
        c.execute("SELECT * FROM items WHERE status='gefunden' ORDER BY id DESC")

    items = c.fetchall()

    cols = st.columns(3)

    for i, item in enumerate(items):
        with cols[i % 3]:
            st.markdown('<div class="card">', unsafe_allow_html=True)

            st.image(item[3], use_column_width=True)
            st.markdown(f"### {item[1]}")
            st.write(f"**Sicherheit:** {item[2]}%")
            st.caption(format_time(item[4]))

            if st.button("✅ Abgeholt", key=item[0]):
                c.execute("UPDATE items SET status='abgeholt' WHERE id=?", (item[0],))
                conn.commit()
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

# ===== ABGEHOLT =====
elif menu == "Abgeholt":
    st.title("📦 Abgeholte Objekte")

    c.execute("SELECT * FROM items WHERE status='abgeholt' ORDER BY id DESC")
    items = c.fetchall()

    cols = st.columns(3)

    for i, item in enumerate(items):
        with cols[i % 3]:
            st.markdown('<div class="card">', unsafe_allow_html=True)

            st.image(item[3], use_column_width=True)
            st.markdown(f"### {item[1]}")
            st.caption(format_time(item[4]))

            st.markdown('</div>', unsafe_allow_html=True)
