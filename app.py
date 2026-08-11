import streamlit as st
import pandas as pd
import requests
from datetime import datetime, time

st.set_page_config(page_title="Control Interno - Firmas de Autores", layout="wide")
st.title("📋 Control Interno: Firmas de Autores")
st.caption("Gestión interna sincronizada mediante API directa con Airtable.")

# Configurar conexión directa
try:
    api_key = st.secrets["airtable"]["api_key"].strip()
    base_id = st.secrets["airtable"]["base_id"].strip()
    HEADERS = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
except Exception as e:
    st.error("⚠️ Configura las claves de Airtable en los Secrets de Streamlit.")
    st.stop()

@st.cache_data(ttl=60)
def cargar_datos(nombre_tabla):
    url = f"https://api.airtable.com/v0/{base_id}/{nombre_tabla}"
    try:
        respuesta = requests.get(url, headers=HEADERS)
        if respuesta.status_code == 200:
            records = respuesta.json().get("records", [])
            if not records:
                return pd.DataFrame()
            return pd.DataFrame([r["fields"] for r in records])
        else:
            st.error(f"Error {respuesta.status_code} al cargar {nombre_tabla}: {respuesta.text}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Fallo de conexión al cargar {nombre_tabla}: {e}")
        return pd.DataFrame()

def guardar_dato(nombre_tabla, datos):
    url = f"https://api.airtable.com/v0/{base_id}/{nombre_tabla}"
    payload = {"records": [{"fields": datos}]}
    try:
        respuesta = requests.post(url, headers=HEADERS, json=payload)
        if respuesta.status_code == 200:
            st.cache_data.clear()
            return True
        else:
            st.error(f"Error {respuesta.status_code} al guardar en {nombre_tabla}: {respuesta.text}")
            return False
    except Exception as e:
        st.error(f"Fallo de conexión al guardar: {e}")
        return False

# Cargar datos
df_eventos = cargar_datos("eventos")
df_autores = cargar_datos("autores")
df_librerias = cargar_datos("librerias")

lista_autores = df_autores["Nombre"].dropna().astype(str).tolist() if not df_autores.empty and "Nombre" in df_autores.columns else []
lista_librerias = df_librerias["Nombre"].dropna().astype(str).tolist() if not df_librerias.empty and "Nombre" in df_librerias.columns else []

tab1, tab2, tab3, tab4 = st.tabs(["📅 Listado de Eventos", "➕ Registrar Nuevo Evento", "👤 Listado de Autores", "🏛️ Listado de Librerías"])

# TAB 1: EVENTOS
with tab1:
    st.header("Eventos Programados")
    if not df_eventos.empty:
        df_display = df_eventos.copy()
        if "confirmado" in df_display.columns:
            df_display["Confirmado"] = df_display["confirmado"].apply(
                lambda x: "✅ Sí" if str(x).lower() in ["true", "1", "yes", "si"] else "⏳ Pendiente"
            )
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No hay eventos registrados en Airtable.")

# TAB 2: NUEVO EVENTO
with tab2:
    st.header("Dar de alta un nuevo evento")
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        opciones_autores = sorted(list(set(lista_autores))) + ["➕ Añadir nuevo autor..."]
        autor_sel = st.selectbox("Seleccionar Autor", opciones_autores)
        autor_final = st.text_input("Nombre del nuevo autor").strip() if autor_sel == "➕ Añadir nuevo autor..." else autor_sel

    with col_sel2:
        opciones_librerias = sorted(list(set(lista_librerias))) + ["➕ Añadir nueva librería..."]
        lib_sel = st.selectbox("Seleccionar Lugar / Librería", opciones_librerias)
        libreria_final = st.text_input("Nombre de la nueva librería").strip() if lib_sel == "➕ Añadir nueva librería..." else lib_sel

    with st.form("form_nuevo_evento"):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            fecha = st.date_input("Fecha")
        with col_f2:
            hora_inicio = st.time_input("Hora de Inicio", value=time(18, 0))
        with col_f3:
            hora_fin = st.time_input("Hora de Fin", value=time(19, 30))

        evento = st.text_input("Evento")
        cartel_archivo = st.text_input("Ruta/Nombre del cartel (ej. cartel.jpg)")
        confirmado = st.checkbox("¿Evento confirmado?", value=False)

        if st.form_submit_button("Guardar Evento"):
            if not autor_final or not libreria_final:
                st.error("Por favor completa el autor y la librería.")
            else:
                if autor_final not in lista_autores:
                    guardar_dato("autores", {"Nombre": autor_final})

                if libreria_final not in lista_librerias:
                    guardar_dato("librerias", {"Nombre": libreria_final})

                nuevo_id = int(pd.to_numeric(df_eventos["id"], errors='coerce').max() + 1) if not df_eventos.empty and "id" in df_eventos.columns and not df_eventos["id"].isnull().all() else 1
                
                record_evento = {
                    "id": str(nuevo_id),
                    "Autor": autor_final,
                    "fecha": str(fecha),
                    "hora_inicio": hora_inicio.strftime("%H:%M"),
                    "hora_fin": hora_fin.strftime("%H:%M"),
                    "lugar": libreria_final,
                    "evento": evento,
                    "cartel": cartel_archivo if cartel_archivo else "Sin cartel",
                    "confirmado": bool(confirmado)
                }

                if guardar_dato("eventos", record_evento):
                    st.success(f"¡Evento #{nuevo_id} guardado con éxito!")
                    st.rerun()

# TAB 3: AUTORES
with tab3:
    st.header("Listado de Autores Registrados")
    nuevo_a = st.text_input("Añadir autor al catálogo")
    if st.button("Guardar Autor"):
        if nuevo_a.strip():
            if guardar_dato("autores", {"Nombre": nuevo_a.strip()}):
                st.success(f"Autor '{nuevo_a.strip()}' añadido con éxito.")
                st.rerun()
    st.dataframe(df_autores, use_container_width=True, hide_index=True)

# TAB 4: LIBRERÍAS
with tab4:
    st.header("Listado de Librerías Registradas")
    nueva_l = st.text_input("Añadir librería al catálogo")
    if st.button("Guardar Librería"):
        if nueva_l.strip():
            if guardar_dato("librerias", {"Nombre": nueva_l.strip()}):
                st.success(f"Librería '{nueva_l.strip()}' añadida con éxito.")
                st.rerun()
    st.dataframe(df_librerias, use_container_width=True, hide_index=True)
