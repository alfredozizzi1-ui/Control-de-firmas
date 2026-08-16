import streamlit as st
import pandas as pd
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, time, date

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

# ... (mantén las funciones cargar_datos, guardar_dato, actualizar_dato igual que antes)

# --- (Código principal de la App hasta la TAB 3) ---

# TAB 3: EDITAR EVENTO (Integrando el botón de envío)
with tab3:
    st.header("Modificar un Evento Existente")
    if not df_eventos.empty:
        df_edit_local = df_eventos.copy()
        df_edit_local["id_num"] = pd.to_numeric(df_edit_local["id"], errors='coerce').fillna(0)
        df_edit_local = df_edit_local.sort_values(by="id_num", ascending=True)

        df_edit_local["opcion_combo"] = df_edit_local.apply(lambda r: f"#{int(r.get('id_num', 0))} - {r.get('Autor', 'Sin autor')} ({r.get('fecha', '')} en {r.get('lugar', '')})", axis=1)
        
        evento_a_editar = st.selectbox("Selecciona el evento que deseas modificar", df_edit_local["opcion_combo"].tolist())
        
        fila_sel = df_edit_local[df_edit_local["opcion_combo"] == evento_a_editar].iloc[0]
        rec_id = fila_sel["airtable_record_id"]

        with st.form("form_editar_evento"):
            edit_autor = st.text_input("Autor", value=str(fila_sel.get("Autor", "")))
            edit_lugar = st.text_input("Lugar / Librería", value=str(fila_sel.get("lugar", "")))
            
            f_actual = fila_sel.get("fecha", str(date.today()))
            edit_fecha = st.date_input("Fecha", value=pd.to_datetime(f_actual).date())
            
            edit_hora_inicio = st.time_input("Hora de Inicio", value=datetime.strptime(str(fila_sel.get("hora_inicio", "18:00")), "%H:%M").time())
            edit_hora_fin = st.time_input("Hora de Fin", value=datetime.strptime(str(fila_sel.get("hora_fin", "19:30")), "%H:%M").time())

            edit_evento_desc = st.text_input("Descripción del Evento", value=str(fila_sel.get("evento", "")))
            edit_anotaciones = st.text_area("Anotaciones", value=str(fila_sel.get("anotaciones", "")))
            edit_cartel_url = st.text_input("Enlace del Cartel", value=str(fila_sel.get("cartel_url", "")))
            edit_confirmado = st.checkbox("¿Evento confirmado?", value=bool(fila_sel.get("confirmado", False)))

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                submit = st.form_submit_button("Guardar Cambios")
            with col_btn2:
                btn_email = st.form_submit_button("📧 Enviar Notificación al Autor")

            if submit:
                datos_actualizados = {
                    "Autor": edit_autor, "lugar": edit_lugar, "fecha": str(edit_fecha),
                    "hora_inicio": edit_hora_inicio.strftime("%H:%M"), "hora_fin": edit_hora_fin.strftime("%H:%M"),
                    "evento": edit_evento_desc, "anotaciones": edit_anotaciones,
                    "cartel_url": edit_cartel_url.strip(), "confirmado": edit_confirmado
                }
                if actualizar_dato("eventos", rec_id, datos_actualizados):
                    st.success("¡Evento actualizado!")
                    st.rerun()

            if btn_email:
                # Buscar email del autor
                autor_info = df_autores[df_autores["Nombre"] == edit_autor]
                if not autor_info.empty and "Email" in autor_info.columns:
                    destinatario = autor_info.iloc[0]["Email"]
                    asunto = f"Notificación: Evento de firma - {edit_evento_desc}"
                    cuerpo = f"Hola {edit_autor},\n\nTienes un nuevo evento programado:\nEvento: {edit_evento_desc}\nFecha: {edit_fecha}\nLugar: {edit_lugar}\n\nCartel: {edit_cartel_url}\n\nSaludos."
                    
                    if enviar_email(destinatario, asunto, cuerpo):
                        st.success(f"Correo enviado a {destinatario}")
                else:
                    st.error("No se encontró email para este autor en la tabla de autores.")
    else:
        st.info("No hay eventos registrados.")
