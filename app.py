import streamlit as st
import pandas as pd
import requests
from pyairtable import Api

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA E INTERFAZ
# ==========================================
st.set_page_config(
    page_title="Control de Firmas - Atlántida Distribuciones",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Control de Firmas y Difusión de Eventos")

# ==========================================
# 2. CONEXIÓN A AIRTABLE (Secrets)
# ==========================================
try:
    AIRTABLE_API_KEY = st.secrets["airtable"]["api_key"].strip()
    BASE_ID = st.secrets["airtable"]["base_id"].strip()
    TABLE_NAME = st.secrets["airtable"]["table_name"].strip()
    
    api = Api(AIRTABLE_API_KEY)
    table_eventos = api.table(BASE_ID, TABLE_NAME)
except Exception as e:
    st.error(f"Error cargando credenciales de Airtable: {e}")
    st.stop()

# ==========================================
# 3. FUNCIONES DE PUBLICACIÓN EN REDES
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
            return False, "Instagram requiere una URL pública de la imagen (HTTP/HTTPS). Revisa el campo cartel_url."

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
# 4. CARGA DE REGISTROS DESDE AIRTABLE
# ==========================================

records = table_eventos.all()

if records:
    raw_data = []
    for r in records:
        fields = r['fields'].copy()
        fields['record_id'] = r['id']
        raw_data.append(fields)
        
    df = pd.DataFrame(raw_data)

    # Definir pestañas del panel de control
    tab1, tab2, tab3 = st.tabs([
        "📊 Control de Firmas y Eventos", 
        "📢 Generador y Difusión en Redes", 
        "➕ Registrar Nuevo Evento"
    ])

    # ------------------------------------------
    # PESTAÑA 1: TABLA Y FILTROS DE FIRMAS
    # ------------------------------------------
    with tab1:
        st.subheader("Listado general de eventos y firmas")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if 'lugar' in df.columns:
                lugares = ["Todos"] + [x for x in df['lugar'].dropna().unique() if str(x).strip() != '']
                lugar_sel = st.selectbox("Filtrar por librería/lugar:", lugares)
            else:
                lugar_sel = "Todos"
                
        with col_f2:
            if 'confirmado' in df.columns:
                estado_sel = st.selectbox("Estado de confirmación:", ["Todos", "Confirmados", "Pendientes"])
            else:
                estado_sel = "Todos"

        df_filtrado = df.copy()
        if lugar_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado['lugar'] == lugar_sel]
            
        if estado_sel == "Confirmados" and 'confirmado' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['confirmado'] == True]
        elif estado_sel == "Pendientes" and 'confirmado' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['confirmado'] != True]

        # Ocultar campos internos de la tabla técnica
        cols_mostrar = [c for c in df_filtrado.columns if c != 'record_id']
        st.dataframe(df_filtrado[cols_mostrar], use_container_width=True)

    # ------------------------------------------
    # PESTAÑA 2: GENERADOR DE TEXTOS Y REDES
    # ------------------------------------------
    with tab2:
        st.subheader("Generación de Texto de Difusión y Publicación")
        
        if 'evento' in df.columns:
            eventos_disponibles = df['evento'].dropna().tolist()
            evento_elegido = st.selectbox("Selecciona la firma/evento a promocionar:", eventos_disponibles)
            
            fila_evento = df[df['evento'] == evento_elegido].iloc[0]
            
            lugar_evt = fila_evento.get('lugar', 'Librería')
            cartel_url_evt = fila_evento.get('cartel_url', '')

            # Texto por defecto o personalizado
            texto_base = fila_evento.get('difusion', '')
            if not texto_base or pd.isna(texto_base):
                texto_base = f"¡No te pierdas nuestro nuevo evento! 📖✨\n\n{evento_elegido} en {lugar_evt}.\n\n¡Te esperamos para compartir una jornada literaria inolvidable! ✍️📚"

            col_izq, col_der = st.columns([1, 1])

            with col_izq:
                st.markdown("#### Mensaje a publicar")
                mensaje_final = st.text_area("Edita el texto antes de enviar:", value=texto_base, height=200)
                
            with col_der:
                st.markdown("#### Cartel del evento")
                if cartel_url_evt and str(cartel_url_evt).startswith("http"):
                    st.image(cartel_url_evt, caption="Cartel de Airtable", width=300)
                else:
                    st.info("Este evento no tiene URL de cartel asignada en Airtable.")
                
                archivo_subido = st.file_uploader("Sustituir cartel con una imagen local:", type=["jpg", "png", "jpeg"])
                if archivo_subido is not None:
                    st.image(archivo_subido, caption="Cartel local cargado", width=300)

            st.divider()
            
            # Botones de envío
            c_fb, c_ig = st.columns(2)

            with c_fb:
                if st.button("🚀 Publicar en Facebook", use_container_width=True):
                    with st.spinner("Enviando publicación a Facebook..."):
                        target = archivo_subido if archivo_subido is not None else cartel_url_evt
                        exito, msg = publicar_en_facebook(mensaje_final, target)
                        if exito:
                            st.success(msg)
                        else:
                            st.error(msg)

            with c_ig:
                if st.button("📸 Publicar en Instagram", use_container_width=True):
                    with st.spinner("Enviando publicación a Instagram..."):
                        if archivo_subido is not None:
                            st.warning("Para publicar en Instagram necesitas una URL HTTP/HTTPS pública. Añade la URL del cartel a la columna cartel_url de Airtable.")
                        else:
                            exito, msg = publicar_en_instagram(mensaje_final, cartel_url_evt)
                            if exito:
                                st.success(msg)
                            else:
                                st.error(msg)

    # ------------------------------------------
    # PESTAÑA 3: FORMULARIO DE NUEVO REGISTRO
    # ------------------------------------------
    with tab3:
        st.subheader("Registrar nuevo evento o firma")
        
        with st.form("nuevo_evento_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                nom_evt = st.text_input("Nombre del evento / Libro:")
                id_evt = st.text_input("ID o Código:")
                url_cartel = st.text_input("URL pública del cartel (HTTP/HTTPS):")
            with col_b:
                lug_evt = st.text_input("Librería / Lugar:")
                conf_evt = st.checkbox("Evento confirmado", value=True)
                txt_dif = st.text_area("Texto personalizado de difusión (opcional):")

            guardar = st.form_submit_button("💾 Guardar evento en Airtable")

            if guardar:
                if nom_evt and lug_evt:
                    datos_nuevo = {
                        "evento": nom_evt,
                        "lugar": lug_evt,
                        "confirmado": conf_evt
                    }
                    if id_evt:
                        datos_nuevo["id"] = id_evt
                    if url_cartel:
                        datos_nuevo["cartel_url"] = url_cartel
                    if txt_dif:
                        datos_nuevo["difusion"] = txt_dif

                    try:
                        table_eventos.create(datos_nuevo)
                        st.success("¡Evento guardado con éxito! Recarga la página para actualizar la lista.")
                    except Exception as err:
                        st.error(f"No se pudo guardar en Airtable: {err}")
                else:
                    st.error("Debes rellenar al menos el nombre del evento y el lugar.")

else:
    st.warning("No se encontraron registros en Airtable. Comprueba el nombre de la tabla en Secrets.")
