import streamlit as st
import pandas as pd
import requests
from datetime import datetime, time, date

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
            data = []
            for r in records:
                fields = r["fields"]
                fields["airtable_record_id"] = r["id"]
                data.append(fields)
            return pd.DataFrame(data)
        else:
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
        else:
            st.error(f"Error al guardar: {respuesta.text}")
            return False
    except Exception as e:
        st.error(f"Fallo de conexión: {e}")
        return False

def actualizar_dato(nombre_tabla, record_id, datos):
    url = f"https://api.airtable.com/v0/{base_id}/{nombre_tabla}/{record_id}"
    payload = {"fields": datos}
    try:
        respuesta = requests.patch(url, headers=HEADERS, json=payload)
        if respuesta.status_code == 200:
            st.cache_data.clear()
            return True
        else:
            st.error(f"Error al actualizar: {respuesta.text}")
            return False
    except Exception as e:
        st.error(f"Fallo de conexión: {e}")
        return False

# Cargar datos
df_eventos = cargar_datos("eventos")
df_autores = cargar_datos("autores")
df_librerias = cargar_datos("librerias")

lista_autores = df_autores["Nombre"].dropna().astype(str).tolist() if not df_autores.empty and "Nombre" in df_autores.columns else []
lista_librerias = df_librerias["Nombre"].dropna().astype(str).tolist() if not df_librerias.empty and "Nombre" in df_librerias.columns else []

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📅 Listado de Eventos", 
    "➕ Registrar", 
    "✏️ Editar Evento", 
    "👤 Autores", 
    "🏛️ Librerías", 
    "📝 Bloc General"
])

# TAB 1: EVENTOS
with tab1:
    st.header("Eventos Próximos Programados")
    if not df_eventos.empty:
        df_display = df_eventos.copy()
        
        if "fecha" in df_display.columns:
            df_display["fecha_dt"] = pd.to_datetime(df_display["fecha"], errors='coerce').dt.date
            hoy = date.today()
            df_display = df_display[df_display["fecha_dt"] >= hoy]
            df_display = df_display.sort_values(by="fecha_dt", ascending=True)
            df_display = df_display.drop(columns=["fecha_dt"])

        if not df_display.empty:
            def formatear_fecha(f):
                try:
                    return pd.to_datetime(f).strftime("%d-%m-%Y")
                except Exception:
                    return f
            df_display["fecha"] = df_display["fecha"].apply(formatear_fecha)

            if "confirmado" in df_display.columns:
                df_display["Confirmado"] = df_display["confirmado"].apply(
                    lambda x: "✅ Sí" if str(x).lower() in ["true", "1", "yes", "si"] else "⏳ Pendiente"
                )
                df_display = df_display.drop(columns=["confirmado"])

            columnas_deseadas = ["Autor", "fecha", "lugar", "hora_inicio", "hora_fin", "evento", "anotaciones", "Confirmado"]
            columnas_existentes = [col for col in columnas_deseadas if col in df_display.columns]
            otras_columnas = [col for col in df_display.columns if col not in columnas_existentes and col not in ["id", "airtable_record_id", "cartel_archivo"]]
            
            df_display = df_display[columnas_existentes + otras_columnas]

            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("No hay eventos próximos programados.")
    else:
        st.info("No hay eventos registrados en Airtable.")

# TAB 2: NUEVO EVENTO
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

    with st.form("form_nuevo_evento"):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            fecha_sel = st.date_input("Fecha", value=date.today())
            st.caption(f"Fecha seleccionada: **{fecha_sel.strftime('%d-%m-%Y')}**")
        with col_f2:
            hora_inicio = st.time_input("Hora de Inicio", value=time(18, 0))
        with col_f3:
            hora_fin = st.time_input("Hora de Fin", value=time(19, 30))

        evento = st.text_input("Evento")
        anotaciones_evento = st.text_area("Anotaciones para este evento")
        archivo_cartel = st.file_uploader("Subir cartel del evento (Imagen o PDF)", type=["jpg", "jpeg", "png", "pdf"])
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
                    "fecha": str(fecha_sel),
                    "hora_inicio": hora_inicio.strftime("%H:%M"),
                    "hora_fin": hora_fin.strftime("%H:%M"),
                    "lugar": libreria_final,
                    "evento": evento,
                    "anotaciones": anotaciones_evento,
                    "confirmado": bool(confirmado)
                }

                if archivo_cartel is not None:
                    record_evento["cartel_archivo"] = [{"url": "https://via.placeholder.com/150", "filename": archivo_cartel.name}]

                if guardar_dato("eventos", record_evento):
                    st.success(f"¡Evento #{nuevo_id} guardado con éxito!")
                    st.rerun()

# TAB 3: EDITAR EVENTO
with tab3:
    st.header("Modificar un Evento Existente")
    if not df_eventos.empty:
        df_eventos["opcion_combo"] = df_eventos.apply(lambda r: f"#{r.get('id', '?')} - {r.get('Autor', 'Sin autor')} ({r.get('fecha', '')} en {r.get('lugar', '')})", axis=1)
        evento_a_editar = st.selectbox("Selecciona el evento que deseas modificar", df_eventos["opcion_combo"].tolist())
        
        fila_sel = df_eventos[df_eventos["opcion_combo"] == evento_a_editar].iloc[0]
        rec_id = fila_sel["airtable_record_id"]

        with st.form("form_editar_evento"):
            edit_autor = st.text_input("Autor", value=str(fila_sel.get("Autor", "")))
            edit_lugar = st.text_input("Lugar / Librería", value=str(fila_sel.get("lugar", "")))
            
            f_actual = fila_sel.get("fecha", str(date.today()))
            try:
                f_val = pd.to_datetime(f_actual).date()
            except:
                f_val = date.today()

            edit_fecha = st.date_input("Fecha", value=f_val)
            st.caption(f"Fecha seleccionada: **{edit_fecha.strftime('%d-%m-%Y')}**")
            
            col_h1, col_h2 = st.columns(2)
            try:
                h_ini_val = datetime.strptime(str(fila_sel.get("hora_inicio", "18:00")), "%H:%M").time()
            except Exception:
                h_ini_val = time(18, 0)
            try:
                h_fin_val = datetime.strptime(str(fila_sel.get("hora_fin", "19:30")), "%H:%M").time()
            except Exception:
                h_fin_val = time(19, 30)

            with col_h1:
                edit_hora_inicio = st.time_input("Hora de Inicio", value=h_ini_val)
            with col_h2:
                edit_hora_fin = st.time_input("Hora de Fin", value=h_fin_val)

            edit_evento_desc = st.text_input("Descripción del Evento", value=str(fila_sel.get("evento", "")))
            edit_anotaciones = st.text_area("Anotaciones", value=str(fila_sel.get("anotaciones", "")))
            
            conf_val = bool(fila_sel.get("confirmado", False))
            edit_confirmado = st.checkbox("¿Evento confirmado?", value=conf_val)

            if st.form_submit_button("Guardar Cambios"):
                datos_actualizados = {
                    "Autor": edit_autor,
                    "lugar": edit_lugar,
                    "fecha": str(edit_fecha),
                    "hora_inicio": edit_hora_inicio.strftime("%H:%M"),
                    "hora_fin": edit_hora_fin.strftime("%H:%M"),
                    "evento": edit_evento_desc,
                    "anotaciones": edit_anotaciones,
                    "confirmado": edit_confirmado
                }

                if actualizar_dato("eventos", rec_id, datos_actualizados):
                    st.success("¡Evento modificado y actualizado con éxito en Airtable!")
                    st.rerun()
    else:
        st.info("No hay eventos registrados para editar.")

# TAB 4: AUTORES
with tab4:
    st.header("Listado de Autores Registrados")
    nuevo_a = st.text_input("Añadir autor al catálogo", key="input_autor_cat")
    if st.button("Guardar Autor", key="btn_guardar_autor"):
        if nuevo_a.strip():
            if guardar_dato("autores", {"Nombre": nuevo_a.strip()}):
                st.success(f"Autor '{nuevo_a.strip()}' añadido con éxito.")
                st.rerun()
    st.dataframe(df_autores, use_container_width=True, hide_index=True)

# TAB 5: LIBRERÍAS
with tab5:
    st.header("Listado de Librerías Registradas")
    nueva_l = st.text_input("Añadir librería al catálogo", key="input_lib_cat")
    if st.button("Guardar Librería", key="btn_guardar_lib"):
        if nueva_l.strip():
            if guardar_dato("librerias", {"Nombre": nueva_l.strip()}):
                st.success(f"Librería '{nueva_l.strip()}' añadido con éxito.")
                st.rerun()
    st.dataframe(df_librerias, use_container_width=True, hide_index=True)

# TAB 6: BLOC GENERAL
with tab6:
    st.header("Bloc de Anotaciones Generales")
    st.caption("Espacio libre para notas rápidas generales.")
    st.text_area("Notas generales:", height=300, placeholder="Apunta aquí recordatorios generales...", key="bloc_general")
