if col_b2.form_submit_button("📧 Enviar Notificación"):
                autor_info = df_autores[df_autores["Nombre"].astype(str).str.strip() == edit_autor.strip()]
                
                if not autor_info.empty and "Email" in autor_info.columns:
                    destinatario = autor_info.iloc[0]["Email"]
                    
                    if not pd.isna(destinatario) and str(destinatario).strip() != "":
                        # --- LÓGICA DE CARTEL ---
                        if edit_cartel_url and edit_cartel_url.strip():
                            info_cartel = f"Puedes consultar el cartel del evento aquí:\n{edit_cartel_url}"
                        else:
                            info_cartel = "En este momento estamos finalizando el diseño del cartel. Te lo haremos llegar en un próximo correo en cuanto esté disponible."
                        
                        asunto = f"Confirmación de Evento: {edit_evento_desc} - {edit_lugar}"
                        
                        cuerpo = f"""Estimado/a {edit_autor},

Esperamos que este mensaje te encuentre bien.

Desde Atlántida Distribuciones, nos complace confirmarte los detalles del próximo evento programado:

EVENTO: {edit_evento_desc}
FECHA: {edit_fecha.strftime('%d de %B de %Y')}
LUGAR: {edit_lugar}
HORARIO: {h_ini_val.strftime('%H:%M')} - {h_fin_val.strftime('%H:%M')}

{info_cartel}

Quedamos a tu entera disposición para cualquier consulta adicional que puedas necesitar.

Atentamente,

Equipo de Atlántida Distribuciones
www.atlantidadistribuciones.es
"""
                        
                        if enviar_email(destinatario, asunto, cuerpo):
                            st.success(f"✅ Notificación enviada con éxito a {destinatario}")
                        else:
                            st.error("❌ Fallo en el envío del servidor SMTP.")
                    else:
                        st.error("❌ El campo de Email está vacío en la ficha del autor.")
                else:
                    st.error("❌ Autor no encontrado o sin email registrado.")
