# TAB 3: EDITAR EVENTO (Con diagnóstico de errores)
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
            
            edit_evento_desc = st.text_input("Descripción del Evento", value=str(fila_sel.get("evento", "")))
            edit_cartel_url = st.text_input("Enlace del Cartel (Google Drive)", value=str(fila_sel.get("cartel_url", "")))
            
            col_btn1, col_btn2 = st.columns(2)
            submit = col_btn1.form_submit_button("Guardar Cambios")
            btn_email = col_btn2.form_submit_button("📧 Enviar Notificación")

            if submit:
                datos_actualizados = {
                    "Autor": edit_autor, "lugar": edit_lugar, "fecha": str(edit_fecha),
                    "evento": edit_evento_desc, "cartel_url": edit_cartel_url.strip()
                }
                if actualizar_dato("eventos", rec_id, datos_actualizados):
                    st.success("¡Evento actualizado!")
                    st.rerun()

            if btn_email:
                st.write(f"--- Diagnóstico ---")
                st.write(f"Buscando al autor: '{edit_autor}'")
                
                # Buscamos específicamente en la tabla de autores
                autor_info = df_autores[df_autores["Nombre"].astype(str).str.strip() == edit_autor.strip()]
                
                if not autor_info.empty:
                    st.write(f"Autor encontrado en la tabla.")
                    if "Email" in autor_info.columns:
                        destinatario = autor_info.iloc[0]["Email"]
                        if pd.isna(destinatario) or str(destinatario).strip() == "":
                            st.error("ERROR: La celda de Email está vacía para este autor.")
                        else:
                            st.write(f"Email detectado: {destinatario}")
                            asunto = f"Notificación: Evento - {edit_evento_desc}"
                            cuerpo = f"Hola, tienes un evento en {edit_lugar}. Cartel: {edit_cartel_url}"
                            
                            if enviar_email(destinatario, asunto, cuerpo):
                                st.success(f"¡Éxito! Correo enviado a {destinatario}")
                            else:
                                st.error("Error al conectar con el servidor de correo. Revisa tus Secrets.")
                    else:
                        st.error("ERROR: No existe una columna llamada 'Email' en la tabla 'autores'.")
                else:
                    st.error(f"ERROR: No se encontró al autor '{edit_autor}' en la tabla 'autores'. Asegúrate de que el nombre esté escrito exactamente igual.")
    else:
        st.info("No hay eventos registrados.")
