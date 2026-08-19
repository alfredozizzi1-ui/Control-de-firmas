with tab3:
    st.header("Modificar Evento")
    if not df_eventos.empty:
        df_edit = df_eventos.copy()
        df_edit["id_num"] = pd.to_numeric(df_edit["id"], errors='coerce').fillna(0)
        df_edit["opcion"] = df_edit.apply(lambda r: f"#{int(r['id_num'])} - {r.get('Autor')} ({r.get('fecha')})", axis=1)
        
        # Guardamos la selección en session_state para detectar cambios
        if "sel_modificar_evento" not in st.session_state:
            st.session_state.sel_modificar_evento = "--- Selecciona un evento ---"
            
        evento_sel = st.selectbox(
            "Selecciona evento a modificar:", 
            ["--- Selecciona un evento ---"] + df_edit["opcion"].tolist(),
            key="sel_modificar_evento"
        )

        if evento_sel != "--- Selecciona un evento ---":
            fila = df_edit[df_edit["opcion"] == evento_sel].iloc[0]
            id_actual = str(fila.get("id"))

            em_aut_e, em_lib_e = obtener_email_contacto(fila.get("Autor", ""), fila.get("lugar", ""), df_autores, df_librerias)
            
            # Formulario con una KEY ÚNICA que cambia al cambiar de evento
            # Esto fuerza a Streamlit a destruir y recrear el formulario limpio
            with st.form(key=f"form_editar_{id_actual}"):
                edit_autor = st.text_input("Autor", value=fila.get("Autor", ""))
                edit_lugar = st.text_input("Lugar", value=fila.get("lugar", ""))
                edit_fecha = st.date_input("Fecha", value=pd.to_datetime(fila.get("fecha")).date())
                
                # Previsualización
                cartel_actual_edit = st.session_state.get(f"cartel_temp_{id_actual}", extraer_url_cartel(fila.get("cartel_url", "")))
                if cartel_actual_edit:
                    st.image(cartel_actual_edit, caption="Cartel actual", width=150)
                
                edit_cartel_file = st.file_uploader("Cambiar imagen del cartel", type=["jpg", "jpeg", "png"])
                
                col_h1, col_h2 = st.columns(2)
                try: h_ini_val = datetime.strptime(str(fila.get("hora_inicio", "18:00")), "%H:%M").time()
                except: h_ini_val = d_time(18, 0)
                try: h_fin_val = datetime.strptime(str(fila.get("hora_fin", "19:30")), "%H:%M").time()
                except: h_fin_val = d_time(19, 30)

                edit_hora_inicio = col_h1.time_input("Hora de Inicio", value=h_ini_val)
                edit_hora_fin = col_h2.time_input("Hora de Fin", value=h_fin_val)
                
                edit_evento_desc = st.text_input("Evento", value=fila.get("evento", ""))
                edit_anotaciones = st.text_area("Anotaciones", value=fila.get("anotaciones", ""))

                st.markdown("---")
                enviar_mail_edit = st.checkbox("Enviar correo con las modificaciones")
                email_notif_edit = st.text_input("Correo destinatario:", value=em_aut_e or em_lib_e)
                
                if st.form_submit_button("Guardar Cambios"):
                    datos_actualizacion = {
                        "Autor": edit_autor, "lugar": edit_lugar, "fecha": str(edit_fecha), 
                        "hora_inicio": edit_hora_inicio.strftime("%H:%M"), 
                        "hora_fin": edit_hora_fin.strftime("%H:%M"), 
                        "evento": edit_evento_desc, "anotaciones": edit_anotaciones
                    }

                    if edit_cartel_file is not None:
                        nueva_url = subir_a_cloudinary(edit_cartel_file)
                        if nueva_url:
                            datos_actualizacion["cartel_url"] = nueva_url
                            st.session_state[f"cartel_temp_{id_actual}"] = nueva_url

                    if actualizar_dato("eventos", fila["airtable_record_id"], datos_actualizacion):
                        st.cache_data.clear()
                        if enviar_mail_edit and email_notif_edit.strip():
                            enviar_email(email_notif_edit.strip(), "Actualización de Evento", "Evento actualizado.")
                        st.success("¡Guardado!")
                        st.rerun()
