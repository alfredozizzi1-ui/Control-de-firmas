import streamlit as st
import pandas as pd
import requests
from pyairtable import Api

# ==========================================
# 1. CONFIGURACIÓN E INICIALIZACIÓN
# ==========================================
st.set_page_config(
    page_title="Control de Firmas y Eventos - Atlántida Distribuciones",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Control de Firmas y Gestor de Eventos")

# Conexión con Airtable
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
            return False, "Instagram requiere una URL pública de la imagen (HTTP/HTTPS). Revisa el enlace del cartel."

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
# 3. LECTURA DE DATOS DESDE AIRTABLE
# ==========================================

records = table.all()
if records:
    # Extraer campos de Airtable conservando el ID interno de registro
    raw_data = []
    for r in records:
        f = r['fields'].copy()
        f['record_id'] = r['id']
        raw_data.append(f)
        
    df = pd.DataFrame(raw_data)

    # Crear pestañas para la interfaz completa
    tab_tabla, tab_difusion, tab_nuevo = st.tabs([
        "📋 Registro de Eventos", 
        "📢 Publicación en Redes", 
        "➕ Añadir Evento"
    ])

    # ------------------------------------------
    # PESTAÑA 1: TABLA Y FILTROS COMPLETOS
    # ------------------------------------------
    with tab_tabla:
        st.subheader("Listado general de firmas y eventos")
        
        # Filtros rápidos
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if 'lugar' in df.columns:
                lugares = ["Todos"] + list(df['lugar'].dropna().unique())
                lugar_filtro = st.selectbox("Filtrar por librería/lugar:", lugares)
            else:
                lugar_filtro = "Todos"
                
        with col_f2:
            if 'confirmado' in df.columns:
                confirmado_filtro = st.selectbox("Estado de confirmación:", ["Todos", "Confirmados", "Pendientes"])
            else:
                confirmado_filtro = "Todos"

        # Aplicar filtros al DataFrame
        df_display = df.copy()
        if lugar_filtro != "Todos":
            df_display = df_display[df_display['lugar'] == lugar_filtro]
            
        if confirmado_filtro == "Confirmados" and 'confirmado' in df_display.columns:
            df_display = df_display[df_display['confirmado'] == True]
        elif confirmado_filtro == "Pendientes" and 'confirmado' in df_display.columns:
            df_display = df_display[df_display['confirmado'] != True]

        # Mostrar tabla limpia descartando 'record_id'
        columnas_visibles = [c for c in df_display.columns if c != 'record_id']
        st.dataframe(df_display[columnas_visibles], use_container_width=True)

    # ------------------------------------------
    # PESTAÑA 2: MÓDULO DE DIFUSIÓN (FB + IG)
    # ------------------------------------------
    with tab_difusion:
        st.subheader("Gestor de Difusión y Redes Sociales")
        
        opciones_eventos = df['evento'].dropna().tolist() if 'evento' in df.columns else []
        
        if opciones_eventos:
            evento_sel = st.selectbox("Selecciona un evento para gestionar su difusión:", opciones_eventos)
            fila = df[df['evento'] == evento_sel].iloc[0]

            # Construir texto de difusión automáticamente si no existe la columna 'difusion'
            if 'difusion' in fila and pd.notna(fila['difusion']):
                mensaje_difusion = fila['difusion']
            else:
                lugar = fila.get('lugar', 'Librería')
                mensaje_difusion = f"¡No te pierdas nuestro nuevo evento! 📖✨\n\n{evento_sel} en {lugar}.\n\n¡Te esperamos!"

            cartel_url = fila.get('cartel_url', '')

            st.write("---")
            st.markdown("### Vista previa del post")
            mensaje_editado = st.text_area("Texto a publicar:", value=mensaje_difusion, height=120)

            # Cartel
            cartel_final = cartel_url
            if cartel_url and str(cartel_url).startswith("http"):
                st.image(cartel_url, caption="Cartel asociado desde Airtable", width=320)
            else:
                st.info("No hay URL de cartel en Airtable para este evento.")

            uploaded_file = st.file_uploader("O sube/reemplaza el cartel localmente:", type=["jpg", "png", "jpeg"])
            if uploaded_file is not None:
                st.image(uploaded_file, caption="Nuevo cartel cargado", width=320)

            st.write("---")

            col_fb, col_ig = st.columns(2)

            with col_fb:
                if st.button("🚀 Publicar en Facebook", use_container_width=True):
                    with st.spinner("Publicando en Facebook..."):
                        target_img = uploaded_file if uploaded_file is not None else cartel_final
                        exito, msg = publicar_en_facebook(mensaje_editado, target_img)
                        if exito:
                            st.success(msg)
                        else:
                            st.error(msg)

            with col_ig:
                if st.button("📸 Publicar en Instagram", use_container_width=True):
                    with st.spinner("Publicando en Instagram..."):
                        if uploaded_file is not None:
                            st.warning("Instagram requiere una URL pública en HTTP/HTTPS para publicar imágenes. Asegúrate de incluir la dirección directa en la columna cartel_url de Airtable.")
                        else:
                            exito, msg = publicar_en_instagram(mensaje_editado, cartel_final)
                            if exito:
                                st.success(msg)
                            else:
                                st.error(msg)
        else:
            st.warning("No hay eventos disponibles con nombre asignado en el campo 'evento'.")

    # ------------------------------------------
    # PESTAÑA 3: FORMULARIO PARA AÑADIR REGISTROS
    # ------------------------------------------
    with tab_nuevo:
        st.subheader("Registrar nueva firma o evento en Airtable")
        
        with st.form("form_nuevo_evento", clear_on_submit=True):
            nuevo_evento = st.text_input("Nombre del evento / Libro:")
            nuevo_lugar = st.text_input("Lugar / Librería:")
            nuevo_id = st.text_input("ID o Código del evento:")
            nuevo_cartel_url = st.text_input("URL del cartel (HTTP/HTTPS):")
            nuevo_confirmado = st.checkbox("Confirmado", value=True)
            
            submit = st.form_submit_button("💾 Guardar en Airtable")
            
            if submit:
                if nuevo_evento and nuevo_lugar:
                    payload = {
                        "evento": nuevo_evento,
                        "lugar": nuevo_lugar,
                        "confirmado": nuevo_confirmado
                    }
                    if nuevo_id:
                        payload["id"] = nuevo_id
                    if nuevo_cartel_url:
                        payload["cartel_url"] = nuevo_cartel_url
                        
                    try:
                        table.create(payload)
                        st.success("¡Evento guardado con éxito en Airtable! Recarga la página para ver los cambios.")
                    except Exception as e:
                        st.error(f"Error al guardar en Airtable: {str(e)}")
                else:
                    st.error("Por favor, completa al menos los campos 'Nombre del evento' y 'Lugar'.")

else:
    st.warning("No se encontraron registros en la tabla de Airtable. Revisa la configuración de tus Secrets.")
