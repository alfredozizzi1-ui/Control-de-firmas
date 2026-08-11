# ... (mantén todo el resto del código igual, solo cambia este bloque en la TAB 1)

# TAB 1: EVENTOS
with tab1:
    st.header("Eventos Próximos Programados")
    if not df_eventos.empty:
        df_display = df_eventos.copy()
        
        if "fecha" in df_display.columns:
            # Convertir la columna fecha a formato datetime para filtrar y ordenar
            df_display["fecha_dt"] = pd.to_datetime(df_display["fecha"], errors='coerce').dt.date
            hoy = date.today()
            # Filtrar eventos pasados
            df_display = df_display[df_display["fecha_dt"] >= hoy]
            
            # --- NUEVO: ORDENAR POR FECHA ---
            df_display = df_display.sort_values(by="fecha_dt", ascending=True)
            
            df_display = df_display.drop(columns=["fecha_dt"])

        if not df_display.empty:
            def formatear_fecha(f):
                try:
                    return pd.to_datetime(f).strftime("%d-%m-%Y")
                except Exception:
                    return f
            df_display["fecha"] = df_display["fecha"].apply(formatear_fecha)

            # ... (el resto sigue igual)
