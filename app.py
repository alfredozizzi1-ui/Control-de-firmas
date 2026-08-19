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
st.caption("Gestión interna sincronizada mediante API directa con Airtable.")

if not os.path.exists("carteles"):
    os.makedirs("carteles")

# ==========================================
# --- FUNCIÓN DE SUBIDA A CLOUDINARY ---
# ==========================================
def subir_a_cloudinary(archivo_file_o_ruta):
    """ Suba una imagen a Cloudinary (gratis) y devuelve la URL pública directa """
    try:
        cloud_name = st.secrets["cloudinary"]["cloud_name"].strip()
        upload_preset = st.secrets["cloudinary"]["upload_preset"].strip()
        url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"

        if isinstance(archivo_file_o_ruta, str) and os.path.exists(archivo_file_o_ruta):
            with open(archivo_file_o_ruta, "rb") as file_data:
                payload = {"upload_preset": upload_preset}
                files = {"file": file_data}
                res = requests.post(url, data=payload, files=files)
        else:
            payload = {"upload_preset": upload_preset}
            files = {"file": archivo_file_o_ruta.getvalue()}
            res = requests.post(url, data=payload, files=files)

        data = res.json()
        if res.status_code == 200 and "secure_url" in data:
            return data["secure_url"]
        else:
            st.error(f"Error en Cloudinary: {data.get('error', {}).get('message', 'Error desconocido')}")
            return ""
    except Exception as e:
        st.error(f"Error conectando con Cloudinary: {e}")
        return ""

def extraer_url_cartel(val):
    if isinstance(val, list) and len(val) > 0:
        primer_item = val[0]
        if isinstance(primer_item, dict):
            return primer_item.get("url", "")
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
try:
    api_key = st.secrets["airtable"]["api_key"].strip()
    base_id = st.secrets["airtable"]["base_id"].strip()
    HEADERS = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
except Exception:
    st.error("⚠️ Configura las claves de Airtable en los Secrets.")
    st.stop()

@st.cache_data(ttl=5)
def cargar_datos(nombre_tabla):
    url = f"https://api.airtable.com/v0/{base_id}/{nombre_tabla}"
    try:
        respuesta = requests.get(url, headers=HEADERS)
        if respuesta.status_code == 200:
            records = respuesta.json().get("records", [])
            data = []
            for r in records:
                fields = r["fields"]
                fields["airtable_record_id"] = r["id"]
                data.append(fields)
            return pd.DataFrame(data)
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def guardar_dato(nombre_tabla, datos):
    url = f"https://api.airtable.com/v0/{base_id}/{nombre_tabla}"
    payload = {"records": [{"fields": datos}]}
    try:
        respuesta = requests.post(url, headers=HEADERS, json=payload)
        if respuesta.status_code == 200:
            st.cache_data.clear()
            return True
        return False
    except Exception:
        return False

def actualizar_dato(nombre_tabla, record_id, datos):
    url = f"https://api.airtable.com/v0/{base_id}/{nombre_tabla}/{record_id}"
    payload = {"fields": datos}
    try:
        respuesta = requests.patch(url, headers=HEADERS, json=payload)
        if respuesta.status_code == 200:
            st.cache_data.clear()
            return True
        return False
    except Exception:
        return False

def obtener_email_contacto(autor, lugar, df_aut, df_lib):
    email_aut = ""
    email_lugar = ""
    if not df_aut.empty and "Nombre" in df_aut.columns and "Email" in df_aut.columns:
        f_aut = df_aut[df_aut["Nombre"] == autor]
        if not f_aut.empty:
            email_aut = str(f_aut.iloc[0].get("Email", "")).strip()
    if not df_lib.empty and "Nombre" in df_lib.columns and "Email" in df_lib.columns:
        f_lib = df_lib[df_lib["Nombre"] == lugar]
        if not f_lib.empty:
            email_lugar = str(f_lib.iloc[0].get("Email", "")).strip()
    return email_aut, email_lugar

df_eventos = cargar_datos("eventos")
df_autores = cargar_datos("autores")
df_librerias = cargar_datos("librerias")

lista_autores = df_autores["Nombre"].dropna().astype(str).tolist() if not df_autores.empty and "Nombre" in df_autores.columns else []
lista_librerias = df_librerias["Nombre"].dropna().astype(str).tolist() if not df_librerias.empty and "Nombre" in df_librerias.columns else []

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📅 Listado de Eventos", "➕ Registrar", "✏️ Editar Evento", "👤 Autores", "🏛️ Librerías", "📝 Bloc General"
])

with tab1:
    st.header("Eventos Próximos Programados")
    if not df_eventos.empty:
        df_display = df_eventos.copy()
        df_display = df_display.replace(['nan', 'None'], '', regex=True)
        if "fecha" in df_display.columns:
            df_display["fecha_dt"] = pd.to_datetime(df_display["fecha"], errors='coerce')
            df_display = df_display[df_display["fecha_dt"].dt.date >= date.today()].sort_values(by="fecha_dt")
            df_display["fecha"] = df_display["fecha_dt"].dt.strftime("%d-%m-%Y")
            df_display = df_display.drop(columns=["fecha_dt"])
        
        if "cartel_url" in df_display.columns:
            df_display["cartel_url"] = df_display["cartel_url"].apply(extraer_url_cartel)

        columnas_ordenadas = ["id", "Autor", "fecha", "hora_inicio", "hora_fin", "lugar", "evento", "confirmado", "anotaciones", "cartel_url"]
        df_display = df_display[[c for c in columnas_ordenadas if c in df_display.columns]]
        st.dataframe(df_display, use_container_width=True, hide_index=True)

with tab2:
    st.header("Dar de alta un nuevo evento")
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        autor_sel = st.selectbox("Seleccionar Autor", sorted(list(set(lista_autores))) + ["➕ Añadir nuevo autor..."])
        autor_final = st.text_input("Nombre del nuevo autor") if autor_sel == "➕ Añadir nuevo autor..." else autor_sel
    with col_sel2:
        lib_sel = st.selectbox("Seleccionar Librería", sorted(list(set(lista_librerias))) + ["➕ Añadir nueva librería..."])
        libreria_final = st.text_input("Nombre de la nueva librería") if lib_sel == "➕ Añadir nueva librería..." else lib_sel

    em_aut, em_lib = obtener_email_contacto(autor_final, libreria_final, df_autores, df_librerias)
    email_destina_reg = em_aut or em_lib

    with st.form("form_nuevo_evento", clear_on_submit=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        fecha_sel = col_f1.date_input("Fecha", value=date.today())
        hora_inicio = col_f2.time_input("Inicio", value=d_time(18, 0))
        hora_fin = col_f3.time_input("Fin", value=d_time(19, 30))
        evento = st.text_input("Evento")
        anotaciones_evento = st.text_area("Anotaciones")
        cartel_file = st.file_uploader("Sube la imagen del cartel", type=["jpg", "jpeg", "png"])
        confirmado = st.checkbox("¿Evento confirmado?")

        st.markdown("---")
        st.markdown("##### ✉️ Notificación por correo")
        enviar_mail_reg = st.checkbox("Enviar correo de confirmación al guardar")
        email_notif_reg = st.text_input("Correo destinatario:", value=email_destina_reg)

        if st.form_submit_button("Guardar Evento"):
            if not autor_final or not libreria_final: 
                st.error("Completa Autor y Librería.")
            else:
                cartel_url_subida = ""
                if cartel_file is not None:
                    with st.spinner("Subiendo cartel a servidor público..."):
                        cartel_url_subida = subir_a_cloudinary(cartel_file)

                nuevo_id = int(pd.to_numeric(df_eventos["id"], errors='coerce').max() + 1) if not df_eventos.empty and "id" in df_eventos.columns else 1
                record = {
                    "id": str(nuevo_id), 
                    "Autor": autor_final, 
                    "fecha": str(fecha_sel), 
                    "hora_inicio": hora_inicio.strftime("%H:%M"), 
                    "hora_fin": hora_fin.strftime("%H:%M"), 
                    "lugar": libreria_final, 
                    "evento": evento, 
                    "anotaciones": anotaciones_evento, 
                    "confirmado": bool(confirmado)
                }
                if cartel_url_subida:
                    # FORMATO CORRECTO PARA ADJUNTOS EN AIRTABLE
                    record["cartel_url"] = [{"url": cartel_url_subida}]
                    st.session_state[f"cartel_temp_{nuevo_id}"] = cartel_url_subida

                if guardar_dato("eventos", record):
                    st.cache_data.clear()
                    if enviar_mail_reg and email_notif_reg.strip():
                        asunto = f"Confirmación de Evento: {autor_final} en {libreria_final}"
                        cuerpo = (
                            f"Hola,\n\nTe confirmamos la programación del evento:\n"
                            f"Autor: {autor_final}\n"
                            f"Lugar: {libreria_final}\n"
                            f"Fecha: {fecha_sel.strftime('%d/%m/%Y')}\n"
                            f"Horario: {hora_inicio.strftime('%H:%M')} - {hora_fin.strftime('%H:%M')}\n\n"
                            f"Un saludo."
                        )
                        enviar_email(email_notif_reg.strip(), asunto, cuerpo)
                    st.success("¡Evento guardado correctamente!"); st.rerun()

with tab3:
    st.header("Modificar Evento")
    if not df_eventos.empty:
        df_edit = df_eventos.copy()
        df_edit["id_num"] = pd.to_numeric(df_edit["id"], errors='coerce').fillna(0)
        df_edit["opcion"] = df_edit.apply(lambda r: f"#{int(r['id_num'])} - {r.get('Autor')} ({r.get('fecha')})", axis=1)
        
        opciones_edit = ["--- Selecciona un evento ---"] + df_edit["opcion"].tolist()
        evento_sel = st.selectbox("Selecciona evento", opciones_edit, key="sel_modificar_evento")

        # DETECTAR CAMBIO DE EVENTO PARA LIMPIAR MEMORIA ANTERIOR
        if "evento_anterior_edit" not in st.session_state:
            st.session_state.evento_anterior_edit = evento_sel
        elif st.session_state.evento_anterior_edit != evento_sel:
            st.session_state.evento_anterior_edit = evento_sel
            st.rerun()

        if evento_sel != "--- Selecciona un evento ---":
            fila = df_edit[df_edit["opcion"] == evento_sel].iloc[0]
            id_actual = str(fila.get("id"))

            em_aut_e, em_lib_e = obtener_email_contacto(fila.get("Autor", ""), fila.get("lugar", ""), df_autores, df_librerias)
            email_destina_edit = em_aut_e or em_lib_e
            
            cartel_actual_edit = st.session_state.get(f"cartel_temp_{id_actual}", extraer_url_cartel(fila.get("cartel_url", "")))
            if cartel_actual_edit:
                st.image(cartel_actual_edit, caption="Cartel actualmente asignado", width=200)

            with st.form(f"form_editar_evento_{id_actual}"):
                edit_autor = st.text_input("Autor", value=fila.get("Autor", ""))
                edit_lugar = st.text_input("Lugar", value=fila.get("lugar", ""))
                edit_fecha = st.date_input("Fecha", value=pd.to_datetime(fila.get("fecha")).date())
                
                edit_cartel_file = st.file_uploader("Cambiar imagen del cartel", type=["jpg", "jpeg", "png"], key=f"edit_cartel_{id_actual}")
                
                col_h1, col_h2 = st.columns(2)
                try: h_ini_val = datetime.strptime(str(fila.get("hora_inicio", "18:00")), "%H:%M").time()
                except: h_ini_val = d_time(18, 0)
                try: h_fin_val = datetime.strptime(str(fila.get("hora_fin", "19:30")), "%H:%M").time()
                except: h_fin_val = d_time(19, 30)

                with col_h1:
                    edit_hora_inicio = st.time_input("Hora de Inicio", value=h_ini_val)
                with col_h2:
                    edit_hora_fin = st.time_input("Hora de Fin", value=h_fin_val)
                
                edit_evento_desc = st.text_input("Evento", value=fila.get("evento", ""))
                edit_anotaciones = st.text_area("Anotaciones", value=fila.get("anotaciones", ""))

                st.markdown("---")
                st.markdown("##### ✉️ Notificación por correo")
                enviar_mail_edit = st.checkbox("Enviar correo con las modificaciones")
                email_notif_edit = st.text_input("Correo destinatario:", value=email_destina_edit)
                
                if st.form_submit_button("Guardar Cambios"):
                    datos_actualizacion = {
                        "Autor": edit_autor, 
                        "lugar": edit_lugar, 
                        "fecha": str(edit_fecha), 
                        "hora_inicio": edit_hora_inicio.strftime("%H:%M"), 
                        "hora_fin": edit_hora_fin.strftime("%H:%M"), 
                        "evento": edit_evento_desc,
                        "anotaciones": edit_anotaciones
                    }

                    if edit_cartel_file is not None:
                        with st.spinner("Subiendo nuevo cartel..."):
                            nueva_url = subir_a_cloudinary(edit_cartel_file)
                            if nueva_url:
                                # FORMATO CORRECTO PARA ADJUNTOS EN AIRTABLE
                                datos_actualizacion["cartel_url"] = [{"url": nueva_url}]
                                st.session_state[f"cartel_temp_{id_actual}"] = nueva_url

                    if actualizar_dato("eventos", fila["airtable_record_id"], datos_actualizacion):
                        st.cache_data.clear()
                        if enviar_mail_edit and email_notif_edit.strip():
                            asunto = f"Actualización de Evento: {edit_autor} en {edit_lugar}"
                            cuerpo = (
                                f"Hola,\n\nTe informamos de los cambios en el evento:\n"
                                f"Autor: {edit_autor}\n"
                                f"Lugar: {edit_lugar}\n"
                                f"Fecha: {edit_fecha.strftime('%d/%m/%Y')}\n"
                                f"Horario: {edit_hora_inicio.strftime('%H:%M')} - {edit_hora_fin.strftime('%H:%M')}\n\n"
                                f"Un saludo."
                            )
                            enviar_email(email_notif_edit.strip(), asunto, cuerpo)
                        st.success("¡Evento e imagen actualizados correctamente!"); st.rerun()

with tab4:
    st.header("👤 Autores")
    with st.form("form_nuevo_autor", clear_on_submit=True):
        nuevo_autor_nombre = st.text_input("Nombre y Apellidos del Autor")
        nuevo_autor_email = st.text_input("Correo electrónico (Opcional)")
        if st.form_submit_button("➕ Guardar Autor"):
            if not nuevo_autor_nombre.strip():
                st.error("El nombre del autor es obligatorio.")
            else:
                record = {"Nombre": nuevo_autor_nombre.strip(), "Email": nuevo_autor_email.strip()}
                if guardar_dato("autores", record):
                    st.cache_data.clear()
                    st.success(f"¡Autor '{nuevo_autor_nombre}' guardado correctamente!")
                    st.rerun()
                else:
                    st.error("Error al guardar en Airtable.")
    st.markdown("---")
    st.dataframe(df_autores, use_container_width=True, hide_index=True)

with tab5:
    st.header("🏛️ Librerías")
    with st.form("form_nueva_libreria", clear_on_submit=True):
        nueva_lib_nombre = st.text_input("Nombre de la Librería / Punto de venta")
        nueva_lib_direccion = st.text_input("Dirección / Municipio (Opcional)")
        nueva_lib_email = st.text_input("Correo electrónico (Opcional)")
        if st.form_submit_button("➕ Guardar Librería"):
            if not nueva_lib_nombre.strip():
                st.error("El nombre de la librería es obligatorio.")
            else:
                record = {"Nombre": nueva_lib_nombre.strip(), "Direccion": nueva_lib_direccion.strip(), "Email": nueva_lib_email.strip()}
                if guardar_dato("librerias", record):
                    st.cache_data.clear()
                    st.success(f"¡Librería '{nueva_lib_nombre}' guardada correctamente!")
                    st.rerun()
                else:
                    st.error("Error al guardar en Airtable.")
    st.markdown("---")
    st.dataframe(df_librerias, use_container_width=True, hide_index=True)

with tab6:
    st.header("Bloc General"); st.text_area("Notas", height=300)

# ==========================================
# --- MÓDULOS DE PUBLICACIÓN EN REDES ---
# ==========================================

def publicar_en_facebook(mensaje, imagen_url):
    try:
        page_id = st.secrets["meta"]["page_id"].strip()
        token = st.secrets["meta"]["page_access_token"].strip()
        url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
        
        payload = {'url': imagen_url, 'caption': mensaje, 'access_token': token}
        response = requests.post(url, data=payload)
            
        resultado = response.json()
        if response.status_code == 200:
            return True, "¡Publicación enviada con éxito a Facebook! 🚀"
        else:
            return False, f"Error en Facebook: {resultado.get('error', {}).get('message', 'Desconocido')}"
    except Exception as e:
        return False, f"Fallo crítico en Facebook: {str(e)}"


def publicar_en_instagram(mensaje, imagen_url):
    try:
        ig_account_id = st.secrets["meta"]["instagram_account_id"].strip()
        token = st.secrets["meta"]["page_access_token"].strip()
        
        if not str(imagen_url).startswith("http"):
            return False, "Instagram requiere una URL pública de la imagen (HTTP/HTTPS)."

        # Paso 1: Crear contenedor de medios
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

        # ESPERA DE 3 SEGUNDOS PARA QUE META PROCESE LA IMAGEN
        time.sleep(3)

        # Paso 2: Publicar contenedor
        url_publish = f"https://graph.facebook.com/v18.0/{ig_account_id}/media_publish"
        payload_publish = {
            'creation_id': creation_id,
            'access_token': token
        }
        res_publish = requests.post(url_publish, data=payload_publish)
        data_publish = res_publish.json()

        if res_publish.status_code == 200:
            return True, "¡Publicación enviada con éxito a Instagram! 📸✨"
        else:
            error_msg = data_publish.get('error', {}).get('message', 'Error al publicar')
            return False, f"Error en Instagram (Paso 2): {error_msg}"

    except Exception as e:
        return False, f"Fallo crítico en Instagram: {str(e)}"

# ==========================================
# --- AUTOMATIZACIÓN DESDE AIRTABLE ---
# ==========================================

st.markdown("---")
st.markdown("### 📚 Publicar Evento en Redes Sociales")

if not df_eventos.empty:
    df_eventos["opcion_menu"] = df_eventos["id"].astype(str) + " - " + df_eventos["evento"].astype(str) + " (" + df_eventos["lugar"].astype(str) + ")"
    evento_elegido = st.selectbox("Selecciona el evento a publicar:", df_eventos["opcion_menu"])
    fila = df_eventos[df_eventos["opcion_menu"] == evento_elegido].iloc[0]
    id_sel = str(fila.get("id"))

    autor_v = str(fila.get('Autor', ''))
    lugar_v = str(fila.get('lugar', ''))
    evento_v = str(fila.get('evento', ''))
    try:
        fecha_obj = pd.to_datetime(fila.get('fecha'))
        fecha_v = fecha_obj.strftime('%d/%m/%Y')
    except:
        fecha_v = str(fila.get('fecha', ''))
    hora_v = str(fila.get('hora_inicio', ''))

    mensaje_auto = (
        f"¡No te pierdas nuestro nuevo evento! 📖✨\n\n"
        f"Presentación del nuevo libro de {autor_v} el día {fecha_v} a las {hora_v} horas en {lugar_v}.\n\n"
        f"¡Te esperamos para compartir una jornada literaria inolvidable! 🖋️📚"
    )

    st.text_area("Mensaje que se publicará:", mensaje_auto, height=150)

    cartel_val = fila.get("cartel_url", "")
    url_de_airtable = extraer_url_cartel(cartel_val)
    
    imagen_final = st.session_state.get(f"cartel_temp_{id_sel}", url_de_airtable)

    archivo_subido_extra = st.file_uploader(
        "O sube/cambia el cartel localmente aquí:", 
        type=["jpg", "jpeg", "png"], 
        key=f"extra_subida_{id_sel}"
    )
    
    if archivo_subido_extra is not None:
        with st.spinner("Subiendo cartel a servidor público..."):
            url_temp = subir_a_cloudinary(archivo_subido_extra)
            if url_temp:
                imagen_final = url_temp
                st.session_state[f"cartel_temp_{id_sel}"] = url_temp
                # FORMATO CORRECTO PARA ADJUNTOS EN AIRTABLE
                actualizar_dato("eventos", fila["airtable_record_id"], {"cartel_url": [{"url": url_temp}]})

    if imagen_final: 
        st.image(imagen_final, width=300)
    else:
        st.warning("⚠️ Este evento no tiene cartel asignado todavía.")
    
    col_fb, col_ig = st.columns(2)

    with col_fb:
        if st.button("🚀 Publicar en Facebook con Imagen", use_container_width=True):
            if not imagen_final: 
                st.error("Falta imagen.")
            else:
                with st.spinner("Subiendo imagen y publicando en Facebook..."):
                    exito, mensaje = publicar_en_facebook(mensaje_auto, imagen_final)
                    if exito: 
                        st.success(mensaje)
                    else: 
                        st.error(mensaje)

    with col_ig:
        if st.button("📸 Publicar en Instagram con Imagen", use_container_width=True):
            if not imagen_final:
                st.error("Falta imagen.")
            else:
                with st.spinner("Enviando publicación a Instagram..."):
                    exito, mensaje = publicar_en_instagram(mensaje_auto, imagen_final)
                    if exito:
                        st.success(mensaje)
                    else:
                        st.error(mensaje)
else:
    st.info("No hay eventos disponibles.")
