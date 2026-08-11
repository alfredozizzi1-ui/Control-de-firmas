# ... (mantén todo el resto del código igual, solo actualiza las partes de fecha en TAB 2 y TAB 3)

# TAB 2: NUEVO EVENTO
with tab2:
    # ... (código anterior)
    with st.form("form_nuevo_evento"):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            # AHORA USAMOS CALENDARIO VISUAL
            fecha_sel = st.date_input("Fecha", value=date.today())
        with col_f2:
            hora_inicio = st.time_input("Hora de Inicio", value=time(18, 0))
        with col_f3:
            hora_fin = st.time_input("Hora de Fin", value=time(19, 30))
        
        # ... (resto del formulario)
        if st.form_submit_button("Guardar Evento"):
            # ...
            # Usamos fecha_sel directamente (que ya es objeto date)
            record_evento = {
                "id": str(nuevo_id),
                "Autor": autor_final,
                "fecha": str(fecha_sel), # Airtable acepta YYYY-MM-DD perfectamente
                # ... resto del registro
            }

# TAB 3: EDITAR EVENTO EXISTENTE
with tab3:
    # ...
    with st.form("form_editar_evento"):
        # ...
        f_actual = fila_sel.get("fecha", str(date.today()))
        try:
            f_val = pd.to_datetime(f_actual).date()
        except:
            f_val = date.today()
        
        edit_fecha = st.date_input("Fecha", value=f_val)
        
        # ... (resto del formulario de edición)
        if st.form_submit_button("Guardar Cambios"):
            # Usamos edit_fecha directamente
            datos_actualizados = {
                # ...
                "fecha": str(edit_fecha),
                # ...
            }
