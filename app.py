import streamlit as st
import pandas as pd
import requests
from datetime import datetime, time
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Control Interno - Firmas de Autores", layout="wide")
st.title("📋 Control Interno: Firmas de Autores")
st.caption("Gestión interna sincronizada permanentemente con Google Sheets.")

# Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_tabla(nombre_pestaña):
    try:
        df = conn.read(worksheet=nombre_pestaña, ttl="0s")
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame()

def guardar_fila(nombre_pestaña, fila_datos):
    url = st.secrets["connections"]["gsheets"].get("web_app_url", "")
    if url:
        payload = {
            "sheet": nombre_pestaña,
            "action": "append",
            "row": fila_datos
        }
        response = requests.post(url, json=payload)
        return response.status_code == 200
    return False

# Cargar datos
df_eventos = cargar_tabla("eventos")
df_autores = cargar_tabla("autores")
df_librerias = cargar_tabla("librerias")

lista_autores = df_autores["Nombre"].dropna().tolist() if not df_autores.empty and "Nombre" in df_autores.columns else []
lista_librerias = df_librerias["Nombre"].dropna().tolist() if not df_librerias.empty and "Nombre" in df_librerias.columns else []

tab1, tab2, tab3, tab4 = st.tabs(["📅 Listado de Eventos", "➕ Registrar Nuevo Evento", "👤 Listado de Autores", "🏛️ Listado de Librerías"])

# TAB 1: EVENTOS
with tab1:
    st.header("Eventos Programados")
    if not df_eventos.empty:
        df_display = df_eventos.copy()
        if "confirmado" in df_display.columns:
            df_display["Confirmado"] = df_display["confirmado"].apply(
                lambda x: "✅ Sí" if str(x).upper() in ["TRUE", "1", "YES", "SI"] else "⏳ Pendiente"
            )
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No hay eventos registrados en la hoja de cálculo.")

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
                    guardar_fila("autores", [autor_final])

                if libreria_final not in lista_librerias:
                    guardar_fila("librerias", [libreria_final])

                nuevo_id = int(df_eventos["id"].max() + 1) if not df_eventos.empty and "id" in df_eventos.columns else 1
                fila_ev = [
                    nuevo_id,
                    autor_final,
                    str(fecha),
                    hora_inicio.strftime("%H:%M"),
                    hora_fin.strftime("%H:%M"),
                    libreria_final,
                    evento,
                    cartel_archivo if cartel_archivo else "Sin cartel",
                    "TRUE" if confirmado else "FALSE"
                ]

                if guardar_fila("eventos", fila_ev):
                    st.success(f"¡Evento #{nuevo_id} guardado con éxito!")
                    st.rerun()

# TAB 3: AUTORES
with tab3:
    st.header("Listado de Autores Registrados")
    nuevo_a = st.text_input("Añadir autor al catálogo")
    if st.button("Guardar Autor"):
        if nuevo_a.strip():
            if guardar_fila("autores", [nuevo_a.strip()]):
                st.success(f"Autor '{nuevo_a.strip()}' añadido con éxito.")
                st.rerun()
    st.dataframe(df_autores, use_container_width=True, hide_index=True)

# TAB 4: LIBRERÍAS
with tab4:
    st.header("Listado de Librerías Registradas")
    nueva_l = st.text_input("Añadir librería al catálogo")
    if st.button("Guardar Librería"):
        if nueva_l.strip():
            if guardar_fila("librerias", [nueva_l.strip()]):
                st.success(f"Librería '{nueva_l.strip()}' añadida con éxito.")
                st.rerun()
    st.dataframe(df_librerias, use_container_width=True, hide_index=True)
