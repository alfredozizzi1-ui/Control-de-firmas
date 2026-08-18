import streamlit as st
import pandas as pd
import requests
from pyairtable import Api

# ==========================================
# 1. CONFIGURACIÓN E INICIALIZACIÓN
# ==========================================
st.set_page_config(
    page_title="Gestor de Eventos - Atlántida Distribuciones",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Gestor de Eventos y Publicación en Redes")

# Conexión con Airtable mediante Secrets
AIRTABLE_API_KEY = st.secrets["airtable"]["api_key"].strip()
BASE_ID = st.secrets["airtable"]["base_id"].strip()
TABLE_NAME = st.secrets["airtable"]["table_name"].strip()

api = Api(AIRTABLE_API_KEY)
table = api.table(BASE_ID, TABLE_NAME)

# ==========================================
# 2. FUNCIONES DE PUBLICACIÓN EN REDES
# ==========================================

def publicar_en_facebook(mensaje, imagen_path_o_url):
    """Publica un texto con imagen en la página de Facebook."""
    try:
        page_id = st.secrets["meta"]["page_id"].strip()
        token = st.secrets["meta"]["page_access_token"].strip()
        url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
        
        if str(imagen_path_o_url).startswith("http"):
            payload = {'url': imagen_path_o_url, 'message': mensaje, 'access_token': token}
            res = requests.post(url, data=payload)
        else:
            payload = {'message': mensaje, 'access_token': token}
            with open(imagen_path_o_url, 'rb') as img_file:
                files = {'source': img_file}
                res = requests.post(url, data=payload, files=files)
                
        data = res.json()
        if res.status_code == 200:
            return True, "¡Publicado con éxito en Facebook! 🚀"
        else:
            return False, f"Error en Facebook: {data.get('error', {}).get('message', 'Error desconocido')}"
    except Exception as e:
        return False, f"Fallo al conectar con Facebook: {str(e)}"


def publicar_en_instagram(mensaje, imagen_url):
    """Publica una imagen con pie de foto en Instagram Business."""
    try:
        ig_account_id = st.secrets["meta"]["instagram_account_id"].strip()
        token = st.secrets["meta"]["page_access_token"].strip()
        
        if not str(imagen_url).startswith("http"):
            return False, "Instagram requiere una URL pública de la imagen (HTTP/HTTPS). Asegúrate de que el campo cartel_url contenga el enlace."

        # Paso 1: Crear contenedor multimedia
        url_container = f"https://graph.facebook.com/v18.0/{ig_account_id}/media"
        payload_container = {
            'image_url': imagen_url,
            'caption': mensaje,
            'access_token': token
        }
        res_container = requests.post(url_container, data=payload_container)
        data_container = res_container.json()

        if res_container.status_code != 200:
            error_msg = data_container.get('error', {}).get('message', 'Error al crear contenedor')
            return False, f"Error en Instagram (Paso 1): {error_msg}"

        creation_id = data_container.get("id")

        # Paso 2: Publicar contenedor
        url_publish = f"https://graph.facebook.com/v18.0/{ig_account_id}/media_publish"
        payload_publish = {
            'creation_id': creation_id,
            'access_token': token
        }
        res_publish = requests.post(url_publish, data=payload_publish)
        data_publish = res_publish.json()

        if res_publish.status_code == 200:
            return True, "¡Publicado con éxito en Instagram! 📸✨"
        else:
            error_msg = data_publish.get('error', {}).get('message', 'Error al publicar')
            return False, f"Error en Instagram (Paso 2): {error_msg}"

    except Exception as e:
        return False, f"Fallo al conectar con Instagram: {str(e)}"


# ==========================================
# 3. LECTURA Y PROCESAMIENTO DE DATOS
# ==========================================

records = table.all()
if records:
    data = [r['fields'] for r in records]
    df = pd.DataFrame(data)
    
    # Selección de evento
    if 'evento' in df.columns:
        eventos_list = df['evento'].dropna().tolist()
        evento_seleccionado = st.selectbox("Selecciona un evento para gestionar:", eventos_list)
        
        # Filtrar fila seleccionada
        fila = df[df['evento'] == evento_seleccionado].iloc[0]
        
        # Extraer campos
        mensaje = fila.get('difusion', f"¡No te pierdas nuestro evento {evento_seleccionado}!")
        cartel_url = fila.get('cartel_url', '')

        st.subheader("Vista previa de la publicación")
        st.info(mensaje)

        # Mostrar cartel si existe
        if cartel_url and str(cartel_url).startswith("http"):
            st.image(cartel_url, caption="Cartel del evento", width=350)
        else:
            st.warning("No hay un cartel cargado o la URL no es válida.")

        uploaded_file = st.file_uploader("O sube/cambia el cartel aquí mismo:", type=["jpg", "png", "jpeg"])
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Nuevo cartel preparado", width=350)

        st.divider()

        # ==========================================
        # 4. BOTONES DE PUBLICACIÓN EN REDES
        # ==========================================
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🚀 Publicar en Facebook", use_container_width=True):
                with st.spinner("Publicando en Facebook..."):
                    exito, msg = publicar_en_facebook(mensaje, cartel_url)
                    if exito:
                        st.success(msg)
                    else:
                        st.error(msg)

        with col2:
            if st.button("📸 Publicar en Instagram", use_container_width=True):
                with st.spinner("Publicando en Instagram..."):
                    exito, msg = publicar_en_instagram(mensaje, cartel_url)
                    if exito:
                        st.success(msg)
                    else:
                        st.error(msg)
else:
    st.warning("No se encontraron registros en la tabla de Airtable.")
