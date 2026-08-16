import streamlit as st
import pandas as pd
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, time, date

st.set_page_config(page_title="Control Interno - Firmas de Autores", layout="wide")
st.title("📖 Control Interno - Firmas de Autores")
st.caption("Gestión interna sincronizada mediante API directa con Airtable.")

# --- CONFIGURACIÓN EMAIL ---
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
    except Exception:
        return False

# --- CONFIGURACIÓN META (FACEBOOK) ---
def publicar_en_facebook(mensaje, url_imagen):
    """
    Gestiona la comunicación con la API de Facebook para publicar contenido.
    """
    try:
        page_id = st.secrets["meta"]["page_id"]
        token = st.secrets["meta"]["page_access_token"]
        
        url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
        
        payload = {
            'url': url_imagen,
            'caption': mensaje,
            'access_token': token
        }
        
        response = requests.post(url, data=payload)
        resultado = response.json()
        
        if response.status_code == 200:
            return True, "¡Publicación enviada con éxito a Facebook! 🚀"
        else:
            error_msg = resultado.get('error', {}).get('message', 'Error desconocido en la API de Meta')
            return False, f"Error al publicar: {error_msg}"
            
    except Exception as e:
        return False, f"Fallo crítico en la conexión con Meta: {str(e)}"

# --- CONFIGURACIÓN AIRTABLE ---
try:
    api_key = st.secrets["airtable"]["api_key"].strip()
    base_id = st.secrets["airtable"]["base_id"].strip()
    HEADERS = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
except Exception as e:
    st.error(f"Error cargando las credenciales de Airtable: {e}")

# --- SECCIÓN DE PUBLICACIÓN EN REDES SOCIALES ---
st.markdown("---")
st.markdown("### 📱 Publicación en Redes Sociales (Facebook)")
texto_evento = st.text_area("Texto del evento para Facebook:", "¡No te pierdas nuestro próximo evento con Atlántida Distribuciones!")
url_del_cartel = st.text_input("URL pública del cartel (imagen):", placeholder="Ej: https://ejemplo.com/cartel.jpg")

if st.button("🚀 Publicar en Redes Sociales"):
    if not url_del_cartel:
        st.warning("Por favor, introduce una URL válida para la imagen.")
    else:
        with st.spinner("Conectando con Facebook..."):
            exito, mensaje = publicar_en_facebook(texto_evento, url_del_cartel)
            
            if exito:
                st.success(mensaje)
            else:
                st.error(mensaje)
                st.info("Revisa que la URL de la imagen sea accesible públicamente.")
