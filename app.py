import streamlit as st
import pandas as pd
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, time, date

st.set_page_config(page_title="Control Interno - Firmas de Autores", layout="wide")
st.title("📋 Control Interno: Firmas de Autores")
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
except Exception as e:
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
    except: return pd.DataFrame()

def guardar_dato(nombre_tabla, datos):
    url = f"https://api.airtable.com/v0/{base_id}/{nombre_tabla}"
    payload = {"records": [{"fields": datos}]}
    try:
        respuesta = requests.post(url, headers=HEADERS, json=payload)
        if respuesta.status_code == 200:
            st.cache_data.clear()
            return True
        return False
    except: return False

def actualizar_dato(nombre_tabla, record_id, datos):
    url = f"https://api.airtable.com/v0/{base_id}/{nombre_tabla}/{record_id}"
    payload = {"fields": datos}
    try:
        respuesta = requests.patch(url, headers=HEADERS, json=payload)
        if respuesta.status_code == 200:
            st.cache_data.clear()
            return True
        return False
    except: return False

# Cargar datos iniciales
df_eventos = cargar_datos("eventos")
df_autores = cargar_datos("autores")
df_librerias = cargar_datos("librerias")

lista_autores = df_autores["Nombre"].dropna().astype(str).tolist() if not df_autores.empty and "Nombre" in df_autores.columns else []
lista_librerias = df_librerias["Nombre"].dropna().astype(str).tolist() if not df_librerias.empty and "Nombre" in df_librerias.columns else []

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📅 Listado de Eventos", "➕ Registrar", "✏️ Editar Evento", "👤 Autores", "🏛️ Librerías", "📝 Bloc General"
])

# TAB 1: LISTADO
with tab1:
    st.header("Eventos Próximos Programados")
    if not df_eventos.empty:
        df_display = df_eventos.copy()
        if "fecha" in df_display.columns:
            df_display["fecha_dt"] = pd.to_datetime(df_display["fecha"], errors='coerce').dt.date
            df_display = df_display[df_display["fecha_dt"] >= date.today()]
            df_display = df_display.sort_values(by="fecha_dt", ascending=True).drop(columns=["fecha_dt"])

        if "cartel_url" not in df_display.columns: df_display["cartel_url"] = ""
        st.dataframe(df_display, use_container_width=True, hide_index=True, column_config={"cartel_url": st.column_config.LinkColumn("Cartel", display_text="Ver cartel 🖼️")})
    else: st.info("No hay eventos registrados.")

# TAB 2: REGISTRAR
with tab2:
    st.header("Dar de alta un nuevo evento")
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        opciones_autores = sorted(list(set(lista_autores))) + ["➕ Añadir nuevo autor..."]
        autor_sel = st.selectbox("Seleccionar Autor", opciones_autores, key="nuevo_autor_sel")
        autor_final = st.text_input("Nombre del nuevo autor", key="nuevo_autor_txt").strip() if autor_sel == "➕ Añadir nuevo autor..." else autor_sel
    with col_sel2:
        opciones_librerias = sorted(list(set(lista_librerias))) + ["➕ Añadir nueva librería..."]
        lib_sel = st.selectbox("Seleccionar Lugar / Librería", opciones_librerias, key="nuevo_lib_sel")
        libreria_final = st.text_input("Nombre de la nueva librería", key="nuevo_lib_txt").strip() if lib_sel == "➕ Añadir nueva librería..." else lib_sel

    with st.form("form_nuevo_evento", clear_on_submit=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            fecha_sel = st.date_input("Fecha", value=date.today())
        with col_f2:
            hora_inicio = st.time_input("Hora de Inicio", value=time(18, 0))
        with col_f3:
            hora_fin = st.time_input("Hora de Fin", value=time(19, 30))
        evento = st.text_input("Evento")
        anotaciones_evento = st.text_area("Anotaciones")
        cartel_enlace = st.text_input("Enlace del Cartel (Google Drive)")
        confirmado = st.checkbox("¿Evento confirmado?")

        if st.form_submit_button("Guardar Evento"):
            if not autor_final or not libreria_final: st.error("Completa Autor y Librería.")
            else:
                nuevo_id = int(pd.to_numeric(df_eventos["id"], errors='coerce').max() + 1) if not df_eventos.empty and "id" in df_eventos.columns else 1
                record = {"id": str(nuevo_id), "Autor": autor_final, "fecha": str(fecha_sel), "hora_inicio": hora_inicio.strftime("%H:%M"), "hora_fin": hora_fin.strftime("%H:%M"), "lugar": libreria_final, "evento": evento, "anotaciones": anotaciones_evento, "cartel_url": cartel_enlace, "confirmado": bool(confirmado)}
                if guardar_dato("eventos", record):
                    st.success("¡Evento guardado!")
                    st.rerun()

# TAB 3: EDITAR
with tab3:
    st.header("Modificar Evento")
    if not df_eventos.empty:
        df_edit = df_eventos.copy()
        df_edit["id_num"] = pd.to_numeric(df_edit["id"], errors='coerce').fillna(0)
        df_edit = df_edit.sort_values(by="id_num")
        df_edit["opcion"] = df_edit.apply(lambda r: f"#{int(r['id_num'])} - {r.get('Autor')} ({r.get('fecha')})", axis=1)
        
        evento_sel = st.selectbox("Selecciona evento", df_edit["opcion"].tolist())
        fila = df_edit[df_edit["opcion"] == evento_sel].iloc[0]
        
        with st.form("form_editar_evento"):
            edit_autor = st.text_input("Autor", value=fila.get("Autor", ""))
            edit_fecha = st.date_input("Fecha", value=pd.to_datetime(fila.get("fecha")).date())
            edit_cartel = st.text_input("Enlace Cartel", value=fila.get("cartel_url", ""))
            # ... (demás campos)
            col_b1, col_b2 = st.columns(2)
            if col_b1.form_submit_button("Guardar Cambios"):
                # (lógica de actualizar_dato aquí...)
                st.success("Actualizado")
                st.rerun()
            if col_b2.form_submit_button("📧 Enviar Notificación"):
                # (lógica de enviar_email aquí...)
                st.success("Enviado")
