import warnings
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, time

FILE_EVENTOS = "eventos.json"
FILE_AUTORES = "autores.json"
FILE_LIBRERIAS = "librerias.json"

st.set_page_config(page_title="Control Interno - Firmas de Autores", layout="wide")

st.title("📋 Control Interno: Firmas de Autores")
st.caption("Gestión interna de eventos, horarios, carteles, confirmación, autores y librerías.")

# Cargar y guardar eventos
def cargar_eventos():
    if os.path.exists(FILE_EVENTOS):
        try:
            with open(FILE_EVENTOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return [
        {
            "id": 1, 
            "Autor": "Autor Ejemplo", 
            "fecha": str(datetime.today().date()), 
            "hora_inicio": "18:00",
            "hora_fin": "19:30",
            "lugar": "Librería Principal", 
            "evento": "Presentación y Firma", 
            "cartel": "cartel_ejemplo.jpg",
            "confirmado": True
        }
    ]

def guardar_eventos(datos):
    with open(FILE_EVENTOS, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

# Cargar y guardar autores
def cargar_autores():
    if os.path.exists(FILE_AUTORES):
        try:
            with open(FILE_AUTORES, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return ["Autor Ejemplo"]

def guardar_autores(datos):
    datos_unicos = sorted(list(set(datos)))
    with open(FILE_AUTORES, "w", encoding="utf-8") as f:
        json.dump(datos_unicos, f, ensure_ascii=False, indent=4)

# Cargar y guardar librerías / lugares
def cargar_librerias():
    if os.path.exists(FILE_LIBRERIAS):
        try:
            with open(FILE_LIBRERIAS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return ["Librería Principal"]

def guardar_librerias(datos):
    datos_unicos = sorted(list(set(datos)))
    with open(FILE_LIBRERIAS, "w", encoding="utf-8") as f:
        json.dump(datos_unicos, f, ensure_ascii=False, indent=4)

# Inicializar sesiones
if 'eventos' not in st.session_state:
    st.session_state.eventos = cargar_eventos()

if 'autores' not in st.session_state:
    st.session_state.autores = cargar_autores()

if 'librerias' not in st.session_state:
    st.session_state.librerias = cargar_librerias()

tab1, tab2, tab3, tab4 = st.tabs(["📅 Listado de Eventos", "➕ Registrar Nuevo Evento", "👤 Listado de Autores", "🏛️ Listado de Librerías"])

with tab1:
    st.header("Eventos Programados")
    if st.session_state.eventos:
        df_eventos = pd.DataFrame(st.session_state.eventos)
        
        df_display = df_eventos.copy()
        
        # Garantizar compatibilidad con eventos creados anteriormente
        if "hora_inicio" not in df_display.columns:
            df_display["hora_inicio"] = "N/D"
        if "hora_fin" not in df_display.columns:
            df_display["hora_fin"] = "N/D"
            
        df_display["Confirmado"] = df_display["confirmado"].apply(lambda x: "✅ Sí" if bool(x) else "⏳ Pendiente")
        
        # Renombrar columnas para la tabla de visualización
        df_table = df_display.rename(columns={
            "hora_inicio": "Hora Inicio",
            "hora_fin": "Hora Fin"
        })
        
        st.dataframe(
            df_table[["id", "Autor", "fecha", "Hora Inicio", "Hora Fin", "lugar", "evento", "cartel", "Confirmado"]], 
            use_container_width=True,
            hide_index=True
        )
        st.divider()
        st.subheader("Detalle del Evento")
        ids_eventos = [e["id"] for e in st.session_state.eventos]
        evento_seleccionado_id = st.selectbox("Selecciona el ID del evento para ver detalles", ids_eventos)
        ev_actual = next((e for e in st.session_state.eventos if e["id"] == evento_seleccionado_id), None)
        
        if ev_actual:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Autor:** {ev_actual.get('Autor', '')}")
                st.markdown(f"**Fecha:** {ev_actual.get('fecha', '')}")
                st.markdown(f"**Horario:** De {ev_actual.get('hora_inicio', 'N/D')} a {ev_actual.get('hora_fin', 'N/D')} hs")
                st.markdown(f"**Lugar / Librería:** {ev_actual.get('lugar', '')}")
                st.markdown(f"**Evento:** {ev_actual.get('evento', '')}")
                
                esta_confirmado = ev_actual.get('confirmado', False)
                estado_txt = "✅ **Confirmado** por autor y librería" if esta_confirmado else "⏳ **Pendiente** de confirmación"
                st.markdown(f"**Estado:** {estado_txt}")
            with col2:
                st.markdown(f"**Cartel asociado:** `{ev_actual.get('cartel', 'Sin cartel')}`")
    else:
        st.info("No hay eventos registrados.")

with tab2:
    st.header("Dar de alta un nuevo evento")
    
    col_sel1, col_sel2 = st.columns(2)
    
    with col_sel1:
        opciones_autores = sorted(st.session_state.autores) + ["➕ Añadir nuevo autor..."]
        autor_seleccionado = st.selectbox("Seleccionar Autor", opciones_autores)
        
        if autor_seleccionado == "➕ Añadir nuevo autor...":
            nuevo_autor_input = st.text_input("Escribe el nombre del nuevo autor")
            autor_final = nuevo_autor_input.strip()
        else:
            autor_final = autor_seleccionado

    with col_sel2:
        opciones_librerias = sorted(st.session_state.librerias) + ["➕ Añadir nueva librería..."]
        libreria_seleccionada = st.selectbox("Seleccionar Lugar / Librería", opciones_librerias)
        
        if libreria_seleccionada == "➕ Añadir nueva librería...":
            nueva_libreria_input = st.text_input("Escribe el nombre de la nueva librería")
            libreria_final = nueva_libreria_input.strip()
        else:
            libreria_final = libreria_seleccionada

    with st.form("form_nuevo_evento"):
        # Selector de Fecha y Horarios en 3 columnas
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            fecha = st.date_input("Fecha")
        with col_f2:
            hora_inicio = st.time_input("Hora de Inicio", value=time(18, 0))
        with col_f3:
            hora_fin = st.time_input("Hora de Fin", value=time(19, 30))
            
        evento = st.text_input("Evento")
        cartel_archivo = st.text_input("Nombre del archivo de cartel o Ruta (ej. cartel.jpg)")
        confirmado = st.checkbox("¿Evento confirmado por el autor y la librería?", value=False)
        
        guardar_evento = st.form_submit_button("Guardar Evento")
        
        if guardar_evento:
            if not autor_final:
                st.error("Por favor, selecciona o escribe un nombre de autor válido.")
            elif not libreria_final:
                st.error("Por favor, selecciona o escribe un nombre de librería/lugar válido.")
            else:
                if autor_final not in st.session_state.autores:
                    st.session_state.autores.append(autor_final)
                    guardar_autores(st.session_state.autores)
                
                if libreria_final not in st.session_state.librerias:
                    st.session_state.librerias.append(libreria_final)
                    guardar_librerias(st.session_state.librerias)
                
                nuevo_id = max([e["id"] for e in st.session_state.eventos], default=0) + 1
                nuevo_ev = {
                    "id": nuevo_id,
                    "Autor": autor_final,
                    "fecha": str(fecha),
                    "hora_inicio": hora_inicio.strftime("%H:%M"),
                    "hora_fin": hora_fin.strftime("%H:%M"),
                    "lugar": libreria_final,
                    "evento": evento,
                    "cartel": cartel_archivo if cartel_archivo else "Sin cartel",
                    "confirmado": confirmado
                }
                st.session_state.eventos.append(nuevo_ev)
                guardar_eventos(st.session_state.eventos)
                
                st.success(f"¡Evento guardado con exito para las {hora_inicio.strftime('%H:%M')} hs (ID: {nuevo_id})!")
                st.rerun()

with tab3:
    st.header("Listado de Autores Registrados")
    col_a1, col_a2 = st.columns([3, 1])
    with col_a1:
        nuevo_autor_directo = st.text_input("Añadir autor directamente al catálogo", key="input_autor_tab3")
    with col_a2:
        st.write("")
        st.write("")
        if st.button("Guardar Autor"):
            if nuevo_autor_directo.strip():
                nombre_clean = nuevo_autor_directo.strip()
                if nombre_clean not in st.session_state.autores:
                    st.session_state.autores.append(nombre_clean)
                    guardar_autores(st.session_state.autores)
                    st.success(f"Autor '{nombre_clean}' añadido correctamente.")
                    st.rerun()
                else:
                    st.warning("Ese autor ya existe en el catálogo.")
    
    st.divider()
    if st.session_state.autores:
        df_autores = pd.DataFrame({"Nombre del Autor": sorted(st.session_state.autores)})
        st.dataframe(df_autores, use_container_width=True, hide_index=True)

with tab4:
    st.header("Listado de Librerías / Lugares Registrados")
    col_l1, col_l2 = st.columns([3, 1])
    with col_l1:
        nueva_libreria_directa = st.text_input("Añadir librería directamente al catálogo", key="input_lib_tab4")
    with col_l2:
        st.write("")
        st.write("")
        if st.button("Guardar Librería"):
            if nueva_libreria_directa.strip():
                nombre_clean = nueva_libreria_directa.strip()
                if nombre_clean not in st.session_state.librerias:
                    st.session_state.librerias.append(nombre_clean)
                    guardar_librerias(st.session_state.librerias)
                    st.success(f"Librería '{nombre_clean}' añadida correctamente.")
                    st.rerun()
                else:
                    st.warning("Esa librería ya existe en el catálogo.")
    
    st.divider()
    if st.session_state.librerias:
        df_librerias = pd.DataFrame({"Nombre de la Librería / Lugar": sorted(st.session_state.librerias)})
        st.dataframe(df_librerias, use_container_width=True, hide_index=True)
