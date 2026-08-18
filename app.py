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

st.title("📚 Control de Firmas y Gestor de Eventos")

# ==========================================
# 2. CONEXIÓN A AIRTABLE (3 TABLAS)
# ==========================================
try:
    AIRTABLE_API_KEY = st.secrets["airtable"]["api_key"].strip()
    BASE_ID = st.secrets["airtable"]["base_id"].strip()
    
    api = Api(AIRTABLE_API_KEY)
    table_eventos = api.table(BASE_ID, "eventos")
    table_autores = api.table(BASE_ID, "autores")
    table_librerias = api.table(BASE_ID, "librerias")
except Exception as e:
    st.error(f"Error al conectar con Airtable. Revisa tus Secrets: {e}")
    st.stop()

# Cargar listas auxiliares de Autores y Librerías
@st.cache_data(ttl=60)
def cargar_autores_y_librerias():
    lista_autores, lista_librerias = [], []
    try:
        rec_autores = table_autores.all()
        for r in rec_autores:
            nombre = r['fields'].get('nombre') or r['fields'].get('autor') or r['fields'].get('Nombre')
            if nombre:
                lista_autores.append(nombre)
    except Exception:
        pass

    try:
        rec_librerias = table_librerias.all()
        for r in rec_librerias:
            nombre = r['fields'].get('nombre') or r['fields'].get('libreria') or r['fields'].get('Lugar')
            if nombre:
                lista_librerias.append(nombre)
    except Exception:
        pass

    return sorted(lista_autores), sorted(lista_librerias)

autores_list, librerias_list = cargar_autores_y_librerias()

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
# 4. CARGA DE EVENTOS Y PESTAÑAS
# ==========================================

records = table_eventos.all()

if records:
    raw_data = []
    for r in records:
        fields = r['fields'].copy()
        fields['record_id'] = r['id']
        raw_data.append(fields)
        
    df = pd.DataFrame(raw_data)

    tab_general, tab_editar, tab_difusion, tab_nuevo = st.tabs([
        "📋 Registro de Eventos", 
        "✏️ Editar / Eliminar Evento", 
        "📢 Publicación en Redes", 
        "➕ Añadir Evento"
    ])

    # ------------------------------------------
    # PESTAÑA 1: LISTADO GENERAL
    # ------------------------------------------
    with tab_general:
        st.subheader("Filtros y Consulta General")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            lugares_opts = ["Todos"] + (librerias_list if librerias_list else list(df['lugar'].dropna().unique()) if 'lugar' in df.columns else [])
            lugar_filtro = st.selectbox("Filtrar por librería/lugar:", lugares_opts)
        with c2:
            autores_opts = ["Todos"] + (autores_list if autores_list else list(df['autor'].dropna().unique()) if 'autor' in df.columns else [])
            autor_filtro = st.selectbox("Filtrar por autor/a:", autores_opts)
        with c3:
            confirmado_filtro = st.selectbox("Estado de confirmación:", ["Todos", "Confirmados", "Pendientes"])

        df_disp = df.copy()
        if lugar_filtro != "Todos" and 'lugar' in df_disp.columns:
            df_disp = df_disp[df_disp['lugar'] == lugar_filtro]
        if autor_filtro != "Todos" and 'autor' in df_disp.columns:
            df_disp = df_disp[df_disp['autor'] == autor_filtro]
        if confirmado_filtro == "Confirmados" and 'confirmado' in df_disp.columns:
            df_disp = df_disp[df_disp['confirmado'] == True]
        elif confirmado_filtro == "Pendientes" and 'confirmado' in df_disp.columns:
            df_disp = df_disp[df_disp['confirmado'] != True]

        columnas_visibles = [c for c in df_disp.columns if c != 'record_id']
        st.dataframe(df_disp[columnas_visibles], use_container_width=True)

    # ------------------------------------------
    # PESTAÑA 2: EDITAR / ELIMINAR EVENTOS
    # ------------------------------------------
    with tab_editar:
        st.subheader("Editar datos de un evento existente")
        
        eventos_list = df['evento'].dropna().tolist() if 'evento' in df.columns else []
        if eventos_list:
            evento_ed_sel = st.selectbox("Selecciona evento a modificar:", eventos_list, key="sel_edit")
            fila_ed = df[df['evento'] == evento_ed_sel].iloc[0]
            rec_id = fila_ed['record_id']

            with st.form("form_editar_evento"):
                col1, col2 = st.columns(2)
                with col1:
                    e_evento = st.text_input("Nombre del evento:", value=str(fila_ed.get('evento', '')))
                    
                    # Cargar autor actual o selector desde lista
                    val_autor = str(fila_ed.get('autor', ''))
                    if autores_list:
                        idx_aut = autores_list.index(val_autor) if val_autor in autores_list else 0
                        e_autor = st.selectbox("Autor/a:", autores_list, index=idx_aut)
                    else:
                        e_autor = st.text_input("Autor/a:", value=val_autor)

                    # Cargar librería actual o selector desde lista
                    val_lugar = str(fila_ed.get('lugar', ''))
                    if librerias_list:
                        idx_lug = librerias_list.index(val_lugar) if val_lugar in librerias_list else 0
                        e_lugar = st.selectbox("Librería / Lugar:", librerias_list, index=idx_lug)
                    else:
                        e_lugar = st.text_input("Librería / Lugar:", value=val_lugar)

                with col2:
                    e_cartel = st.text_input("URL del cartel (HTTP/HTTPS):", value=str(fila_ed.get('cartel_url', '')))
                    e_confirmado = st.checkbox("Confirmado", value=bool(fila_ed.get('confirmado', True)))
                    e_difusion = st.text_area("Texto de difusión:", value=str(fila_ed.get('difusion', '')), height=100)

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    guardar_edit = st.form_submit_button("💾 Guardar Cambios")
                with col_btn2:
                    eliminar_edit = st.form_submit_button("🗑️ Eliminar Evento")

                if guardar_edit:
                    payload_edit = {
                        "evento": e_evento,
                        "autor": e_autor,
                        "lugar": e_lugar,
                        "cartel_url": e_cartel,
                        "confirmado": e_confirmado,
                        "difusion": e_difusion
                    }
                    try:
                        table_eventos.update(rec_id, payload_edit)
                        st.success("¡Evento actualizado correctamente! Actualiza la página.")
                        st.cache_data.clear()
                    except Exception as err:
                        st.error(f"Error al actualizar: {err}")

                if eliminar_edit:
                    try:
                        table_eventos.delete(rec_id)
                        st.warning("Evento eliminado de Airtable. Actualiza la página.")
                        st.cache_data.clear()
                    except Exception as err:
                        st.error(f"Error al eliminar: {err}")

    # ------------------------------------------
    # PESTAÑA 3: PUBLICACIÓN EN REDES (FB + IG)
    # ------------------------------------------
    with tab_difusion:
        st.subheader("Gestor de Difusión y Redes Sociales")
        
        if 'evento' in df.columns:
            evento_sel = st.selectbox("Selecciona un evento para publicar:", df['evento'].dropna().tolist(), key="sel_dif")
            fila = df[df['evento'] == evento_sel].iloc[0]

            mensaje_difusion = fila.get('difusion', f"¡No te pierdas nuestro nuevo evento {evento_sel}!")
            cartel_url = fila.get('cartel_url', '')

            st.write("---")
            st.markdown("### Vista previa del post")
            mensaje_editado = st.text_area("Texto a publicar:", value=mensaje_difusion, height=120)

            cartel_final = cartel_url
            if cartel_url and str(cartel_url).startswith("http"):
                st.image(cartel_url, caption="Cartel desde Airtable", width=320)
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
                            st.warning("Instagram requiere una URL pública en HTTP/HTTPS para publicar imágenes. Asegúrate de incluir la dirección en la columna cartel_url.")
                        else:
                            exito, msg = publicar_en_instagram(mensaje_editado, cartel_final)
                            if exito:
                                st.success(msg)
                            else:
                                st.error(msg)

    # ------------------------------------------
    # PESTAÑA 4: FORMULARIO PARA AÑADIR REGISTROS
    # ------------------------------------------
    with tab_nuevo:
        st.subheader("Registrar nuevo evento o firma")
        
        with st.form("form_nuevo_evento", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                nuevo_evento = st.text_input("Nombre del evento / Libro:")
                
                # Selector de Autores desde Airtable
                if autores_list:
                    nuevo_autor = st.selectbox("Autor/a:", autores_list)
                else:
                    nuevo_autor = st.text_input("Autor/a:")

                # Selector de Librerías desde Airtable
                if librerias_list:
                    nuevo_lugar = st.selectbox("Librería / Lugar:", librerias_list)
                else:
                    nuevo_lugar = st.text_input("Librería / Lugar:")

            with col_b:
                nuevo_cartel_url = st.text_input("URL del cartel (HTTP/HTTPS):")
                nuevo_confirmado = st.checkbox("Confirmado", value=True)
                nuevo_difusion = st.text_area("Texto de difusión (opcional):")

            submit = st.form_submit_button("💾 Guardar en Airtable")

            if submit:
                if nuevo_evento and nuevo_lugar:
                    payload = {
                        "evento": nuevo_evento,
                        "autor": nuevo_autor,
                        "lugar": nuevo_lugar,
                        "confirmado": nuevo_confirmado
                    }
                    if nuevo_cartel_url:
                        payload["cartel_url"] = nuevo_cartel_url
                    if nuevo_difusion:
                        payload["difusion"] = nuevo_difusion

                    try:
                        table_eventos.create(payload)
                        st.success("¡Evento guardado con éxito en Airtable!")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"Error al guardar en Airtable: {str(e)}")
                else:
                    st.error("Por favor, completa los campos requeridos.")

else:
    st.warning("No se encontraron registros en la tabla de Airtable.")
