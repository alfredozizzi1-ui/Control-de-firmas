import streamlit as st
import pandas as pd
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, time, date
import re
import os

st.set_page_config(page_title="Control Interno - Firmas de Autores", layout="wide")
st.title("📋 Control Interno: Firmas de Autores")
st.caption("Gestión interna sincronizada mediante API directa con Airtable.")

# Crear carpeta local para guardar los carteles subidos si no existe
if not os.path.exists("carteles"):
    os.makedirs("carteles")

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

@st.cache_data(ttl=60)
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

# Cargar datos
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

    with st.form("form_nuevo_evento", clear_on_submit=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        fecha_sel = col_f1.date_input("Fecha", value=date.today())
        hora_inicio = col_f2.time_input("Inicio", value=time(18, 0))
        hora_fin = col_f3.time_input("Fin", value=time(19, 30))
        evento = st.text_input("Evento")
        anotaciones_evento = st.text_area("Anotaciones")
        cartel_file = st.file_uploader("Sube la imagen del cartel", type=["jpg", "jpeg", "png"])
        confirmado = st.checkbox("¿Evento confirmado?")

        if st.form_submit_button("Guardar Evento"):
            if not autor_final or not libreria_final: 
                st.error("Completa Autor y Librería.")
            else:
                cartel_path = ""
                if cartel_file is not None:
                    cartel_path = os.path.join("carteles", cartel_file.name)
                    with open(cartel_path, "wb") as f:
                        f.write(cartel_file.getbuffer())
                nuevo_id = int(pd.to_numeric(df_eventos["id"], errors='coerce').max() + 1) if not df_eventos.empty and "id" in df_eventos.columns else 1
                record = {"id": str(nuevo_id), "Autor": autor_final, "fecha": str(fecha_sel), "hora_inicio": hora_inicio.strftime("%H:%M"), "hora_fin": hora_fin.strftime("%H:%M"), "lugar": libreria_final, "evento": evento, "anotaciones": anotaciones_evento, "cartel_url": cartel_path, "confirmado": bool(confirmado)}
                if guardar_dato("eventos", record):
                    st.success("¡Evento guardado!"); st.rerun()

with tab3:
    st.header("Modificar Evento")
    if not df_eventos.empty:
        df_edit = df_eventos.copy()
        df_edit["id_num"] = pd.to_numeric(df_edit["id"], errors='coerce').fillna(0)
        df_edit["opcion"] = df_edit.apply(lambda r: f"#{int(r['id_num'])} - {r.get('Autor')} ({r.get('fecha')})", axis=1)
        evento_sel = st.selectbox("Selecciona evento", df_edit["opcion"].tolist())
        fila = df_edit[df_edit["opcion"] == evento_sel].iloc[0]
        
        with st.form("form_editar_evento"):
            edit_autor = st.text_input("Autor", value=fila.get("Autor", ""))
            edit_lugar = st.text_input("Lugar", value=fila.get("lugar", ""))
            edit_fecha = st.date_input("Fecha", value=pd.to_datetime(fila.get("fecha")).date())
            edit_cartel_file = st.file_uploader("Cambiar imagen del cartel", type=["jpg", "jpeg", "png"])
            
            col_h1, col_h2 = st.columns(2)
            try: h_ini_val = datetime.strptime(str(fila.get("hora_inicio", "18:00")), "%H:%M").time()
            except: h_ini_val = time(18, 0)
            try: h_fin_val = datetime.strptime(str(fila.get("hora_fin", "19:30")), "%H:%M").time()
            except: h_fin_val = time(19, 30)

            with col_h1:
                edit_hora_inicio = st.time_input("Hora de Inicio", value=h_ini_val)
            with col_h2:
                edit_hora_fin = st.time_input("Hora de Fin", value=h_fin_val)
            
            edit_evento_desc = st.text_input("Evento", value=fila.get("evento", ""))
            
            if st.form_submit_button("Guardar Cambios"):
                datos_actualizacion = {"Autor": edit_autor, "lugar": edit_lugar, "fecha": str(edit_fecha), "hora_inicio": edit_hora_inicio.strftime("%H:%M"), "hora_fin": edit_hora_fin.strftime("%H:%M"), "evento": edit_evento_desc}
                if actualizar_dato("eventos", fila["airtable_record_id"], datos_actualizacion):
                    st.success("¡Actualizado!"); st.rerun()

with tab4:
    st.header("Autores"); st.dataframe(df_autores, use_container_width=True)
with tab5:
    st.header("Librerías"); st.dataframe(df_librerias, use_container_width=True)
with tab6:
    st.header("Bloc General"); st.text_area("Notas", height=300)

# ==========================================
# --- MÓDULO DE PUBLICACIÓN EN FACEBOOK ---
# ==========================================

def publicar_en_facebook(mensaje, imagen_path_o_url):
    try:
        page_id = st.secrets["meta"]["page_id"].strip()
        token = st.secrets["meta"]["page_access_token"].strip()
        url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
        
        if os.path.exists(imagen_path_o_url):
            with open(imagen_path_o_url, 'rb') as img_file:
                files = {'source': img_file}
                payload = {'message': mensaje, 'access_token': token}
                response = requests.post(url, data=payload, files=files)
        else:
            payload = {'url': imagen_path_o_url, 'caption': mensaje, 'access_token': token}
            response = requests.post(url, data=payload)
            
        resultado = response.json()
        if response.status_code == 200:
            return True, "¡Publicación enviada con éxito a Facebook! 🚀"
        else:
            return False, f"Error: {resultado.get('error', {}).get('message', 'Desconocido')}"
    except Exception as e:
        return False, f"Fallo crítico: {str(e)}"

# ==========================================
# --- AUTOMATIZACIÓN DESDE AIRTABLE ---
# ==========================================

st.markdown("---")
st.markdown("### 📚 Publicar Evento en Facebook")

if not df_eventos.empty:
    df_eventos["opcion_menu"] = df_eventos["id"].astype(str) + " - " + df_eventos["evento"].astype(str) + " (" + df_eventos["lugar"].astype(str) + ")"
    evento_elegido = st.selectbox("Selecciona el evento a publicar:", df_eventos["opcion_menu"])
    fila = df_eventos[df_eventos["opcion_menu"] == evento_elegido].iloc[0]

    # Preparar datos para el texto
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
    imagen_final = ""
    if isinstance(cartel_val, str) and os.path.exists(cartel_val): imagen_final = cartel_val
    elif isinstance(cartel_val, list) and len(cartel_val) > 0: imagen_final = cartel_val[0].get("url", "")
    elif isinstance(cartel_val, str) and cartel_val.startswith("http"): imagen_final = cartel_val

    archivo_subido_extra = st.file_uploader("O sube/cambia el cartel aquí mismo:", type=["jpg", "jpeg", "png"], key="extra_subida")
    if archivo_subido_extra is not None:
        temp_path = os.path.join("carteles", archivo_subido_extra.name)
        with open(temp_path, "wb") as f: f.write(archivo_subido_extra.getbuffer())
        imagen_final = temp_path

    if imagen_final: st.image(imagen_final, width=300)
    
    if st.button("🚀 Publicar en Facebook con Imagen"):
        if not imagen_final: st.error("Falta imagen.")
        else:
            with st.spinner("Subiendo imagen y publicando en Facebook..."):
                exito, mensaje = publicar_en_facebook(mensaje_auto, imagen_final)
                if exito: st.success(mensaje)
                else: st.error(mensaje)
else:
    st.info("No hay eventos disponibles.")
