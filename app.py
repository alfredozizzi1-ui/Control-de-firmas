import streamlit as st
import pandas as pd
from datetime import datetime, time
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Control Interno - Firmas de Autores", layout="wide")
st.title("📋 Control Interno: Firmas de Autores")
st.caption("Gestión interna sincronizada permanentemente con Google Sheets.")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Funciones de lectura
def cargar_datos(sheet_name):
    try:
        data = conn.read(worksheet=sheet_name, ttl="0s")
        return data.dropna(how="all")
    except Exception as e:
        return pd.DataFrame()

# Cargar datos actuales
df_eventos = cargar_datos("eventos")
df_autores = cargar_datos("autores")
df_librerias = cargar_datos("librerias")

lista_autores = df_autores["Nombre"].tolist() if not df_autores.empty and "Nombre" in df_autores.columns else ["Autor Ejemplo"]
lista_librerias = df_librerias["Nombre"].tolist() if not df_librerias.empty and "Nombre" in df_librerias.columns else ["Librería Principal"]

tab1, tab2, tab3, tab4 = st.tabs(["📅 Listado de Eventos", "➕ Registrar Nuevo Evento", "👤 Listado de Autores", "🏛️ Listado de Librerías"])

# TAB 1: EVENTOS
with tab1:
    st.header("Eventos Programados")
    if not df_eventos.empty:
        df_display = df_eventos.copy()
        if "confirmado" in df_display.columns:
            df_display["Confirmado"] = df_display["confirmado"].apply(lambda x: "✅ Sí" if str(x).upper() in ["TRUE", "1", "YES", "SI"] else "⏳ Pendiente")
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:        st.info("No hay eventos registrados en la hoja de cálculo.")

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
                # Guardar nuevo autor si aplica
                if autor_final not in lista_autores:
                    df_new_aut = pd.concat([df_autores, pd.DataFrame([{"Nombre": autor_final}])], ignore_index=True)
                    conn.update(worksheet="autores", data=df_new_aut)

                # Guardar nueva librería si aplica
                if libreria_final not in lista_librerias:
                    df_new_lib = pd.concat([df_librerias, pd.DataFrame([{"Nombre": libreria_final}])], ignore_index=True)
                    conn.update(worksheet="librerias", data=df_new_lib)

                # Guardar el nuevo evento
                nuevo_id = int(df_eventos["id"].max() + 1) if not df_eventos.empty and "id" in df_eventos.columns else 1
                nuevo_registro = pd.DataFrame([{
                    "id": nuevo_id,
                    "Autor": autor_final,
                    "fecha": str(fecha),
                    "hora_inicio": hora_inicio.strftime("%H:%M"),
                    "hora_fin": hora_fin.strftime("%H:%M"),
                    "lugar": libreria_final,
                    "evento": evento,
                    "cartel": cartel_archivo if cartel_archivo else "Sin cartel",
                    "confirmado": confirmado
                }])

                df_final_eventos = pd.concat([df_eventos, nuevo_registro], ignore_index=True)
                conn.update(worksheet="eventos", data=df_final_eventos)

                st.success(f"¡Evento #{nuevo_id} guardado con éxito en Google Sheets!")
                st.rerun()

# TAB 3: AUTORES
with tab3:
    st.header("Listado de Autores Registrados")
    nuevo_a = st.text_input("Añadir autor al catálogo")
    if st.button("Guardar Autor"):
        if nuevo_a.strip():
            df_new_aut = pd.concat([df_autores, pd.DataFrame([{"Nombre": nuevo_a.strip()}])], ignore_index=True)
            conn.update(worksheet="autores", data=df_new_aut)
            st.success("Autor añadido.")
            st.rerun()
    st.dataframe(df_autores, use_container_width=True, hide_index=True)

# TAB 4: LIBRERÍAS
with tab4:
    st.header("Listado de Librerías Registradas")
    nueva_l = st.text_input("Añadir librería al catálogo")
    if st.button("Guardar Librería"):
        if nueva_l.strip():
            df_new_lib = pd.concat([df_librerias, pd.DataFrame([{"Nombre": nueva_l.strip()}])], ignore_index=True)
            conn.update(worksheet="librerias", data=df_new_lib)
            st.success("Librería añadida.")
            st.rerun()
    st.dataframe(df_librerias, use_container_width=True, hide_index=True)
