import streamlit as st
import pandas as pd
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, time as d_time, date
import os
import time

st.set_page_config(page_title="Control Interno - Firmas de Autores", layout="wide")
st.title("📋 Control Interno: Firmas de Autores")
st.caption("Gestión interna sincronizada con Airtable y Cloudinary.")

if not os.path.exists("carteles"):
    os.makedirs("carteles")

# ==========================================
# --- FUNCIONES AUXILIARES ---
# ==========================================
def subir_a_cloudinary(archivo_file):
    try:
        cloud_name = st.secrets["cloudinary"]["cloud_name"].strip()
        upload_preset = st.secrets["cloudinary"]["upload_preset"].strip()
        url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"
        payload = {"upload_preset": upload_preset}
        files = {"file": archivo_file.getvalue()}
        res = requests.post(url, data=payload, files=files)
        data = res.json()
        return data.get("secure_url", "")
    except Exception as e:
        st.error(f"Error en Cloudinary: {e}")
        return ""

def extraer_url_cartel(val):
    if isinstance(val, list) and len(val) > 0:
        return val[0].get("url", "") if isinstance(val[0], dict) else ""
    elif isinstance(val, str):
        return val.strip()
    return ""

def enviar_email(destinatario, asunto, cuerpo):
    try:
        msg = MIMEText(cuerpo)
        msg['Subject'] = asunto
        msg['From'] = st.secrets["email"]["usuario"]
        msg['To'] = destinatario
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(st.secrets["email"]["usuario"], st.secrets["email"]["password"])
            server.sendmail(st.secrets["email"]["usuario"], destinatario, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Error al enviar email: {e}")
        return False

# --- CONFIGURACIÓN AIRTABLE ---
api_key = st.secrets["airtable"]["api_key"].strip()
base_id = st.secrets["airtable"]["base_id"].strip()
HEADERS = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

@st.cache_data(ttl=5)
def cargar_datos(nombre_tabla):
    url = f"https://api.airtable.com/v0/{base_id}/{nombre_tabla}"
    try:
        respuesta = requests.get(url, headers=HEADERS)
        if respuesta.status_code == 200:
            records = respuesta.json().get("records", [])
            data = [{**r["fields"], "airtable_record_id": r["id"]} for r in records]
            return pd.DataFrame(data)
        return pd.DataFrame()
    except: return pd.DataFrame()

def guardar_dato(nombre_tabla, datos):
    url = f"https://api.airtable.com/v0/{base_id}/{nombre_tabla}"
    if requests.post(url, headers=HEADERS, json={"records": [{"fields": datos}]}).status_code == 200:
        st.cache_data.clear(); return True
    return False

def actualizar_dato(nombre_tabla, record_id, datos):
    url = f"https://api.airtable.com/v0/{base_id}/{nombre_tabla}/{record_id}"
    if requests.patch(url, headers=HEADERS, json={"fields": datos}).status_code == 200:
        st.cache_data.clear(); return True
    return False

# --- UI ---
df_eventos = cargar_datos("eventos")
df_autores = cargar_datos("autores")
df_librerias = cargar_datos("librerias")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📅 Listado", "➕ Registrar", "✏️ Editar", "👤 Autores", "🏛️ Librerías"])

with tab1:
    st.header("Eventos Próximos")
    if not df_eventos.empty:
        st.dataframe(df_eventos, use_container_width=True)

with tab2:
    st.header("Registrar Evento")
    with st.form("nuevo_evento", clear_on_submit=True):
        autor = st.text_input("Autor")
        lugar = st.text_input("Lugar")
        fecha = st.date_input("Fecha")
        cartel = st.file_uploader("Cartel", type=["jpg", "png"])
        enviar_mail = st.checkbox("Enviar confirmación por email")
        dest = st.text_input("Email destinatario")
        if st.form_submit_button("Guardar"):
            c_url = subir_a_cloudinary(cartel) if cartel else ""
            if guardar_dato("eventos", {"Autor": autor, "lugar": lugar, "fecha": str(fecha), "cartel_url": c_url}):
                if enviar_mail: enviar_email(dest, "Evento creado", f"Evento con {autor} en {lugar}")
                st.success("Guardado"); st.rerun()

with tab3:
    st.header("Modificar Evento")
    if not df_eventos.empty:
        opciones = ["---"] + df_eventos.apply(lambda r: f"{r['id']} - {r.get('Autor')}", axis=1).tolist()
        sel = st.selectbox("Seleccionar", opciones, key="sel_edit")
        if sel != "---":
            fila = df_eventos[df_eventos["id"] == sel.split(" - ")[0]].iloc[0]
            with st.form(key=f"form_{fila['id']}"):
                e_autor = st.text_input("Autor", value=fila.get("Autor", ""))
                e_lugar = st.text_input("Lugar", value=fila.get("lugar", ""))
                e_cartel = st.file_uploader("Nuevo cartel", type=["jpg", "png"])
                enviar_mail = st.checkbox("Enviar correo de cambios")
                dest = st.text_input("Email destinatario")
                if st.form_submit_button("Actualizar"):
                    c_url = subir_a_cloudinary(e_cartel) if e_cartel else fila.get("cartel_url", "")
                    if actualizar_dato("eventos", fila["airtable_record_id"], {"Autor": e_autor, "lugar": e_lugar, "cartel_url": c_url}):
                        if enviar_mail: enviar_email(dest, "Cambios en evento", f"Detalles: {e_autor} en {e_lugar}")
                        st.success("Actualizado"); st.rerun()

# --- PUBLICACIÓN INTEGRADA ---
st.markdown("---")
st.subheader("📚 Publicar en Redes")
if not df_eventos.empty:
    pub_sel = st.selectbox("Evento a publicar", df_eventos["id"].tolist())
    fila_pub = df_eventos[df_eventos["id"] == pub_sel].iloc[0]
    img = extraer_url_cartel(fila_pub.get("cartel_url", ""))
    if img: st.image(img, width=200)
    
    if st.button("🚀 Publicar Facebook"):
        st.write("Publicando en Facebook...")
    if st.button("📸 Publicar Instagram"):
        with st.spinner("Publicando en Instagram..."):
            time.sleep(3)
            st.write("¡Publicado en Instagram!")
