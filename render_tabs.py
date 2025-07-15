def render_bitacora_tab(manager):
    st.title("📒 Bitácora del Sistema")

    # --- Opciones de filtro y paginación ---
    st.subheader("Filtros")
    filter_column = st.selectbox("Columna a filtrar", options=["nombre_usuario", "accion", "tabla_afectada"], index=0)
    filter_value = st.text_input("Valor del filtro")

    pagination_info = {
        "offset": 0,
        "limit": 10,
        "current_page": 1,
        "total_records": 0
    }

    table_placeholder = st.empty()
    pagination_label_placeholder = st.empty()

    # Mostrar los datos
    manager.load_data_logic(
        table_placeholder=table_placeholder,
        pagination_info=pagination_info,
        pagination_label_placeholder=pagination_label_placeholder,
        filter_column=filter_column if filter_value else None,
        filter_value=filter_value if filter_value else None
    )

    # Botones de paginación
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⬅️ Anterior"):
            manager.load_data_logic(
                table_placeholder=table_placeholder,
                pagination_info=pagination_info,
                pagination_label_placeholder=pagination_label_placeholder,
                page_change=-1,
                filter_column=filter_column if filter_value else None,
                filter_value=filter_value if filter_value else None
            )
    with col3:
        if st.button("➡️ Siguiente"):
            manager.load_data_logic(
                table_placeholder=table_placeholder,
                pagination_info=pagination_info,
                pagination_label_placeholder=pagination_label_placeholder,
                page_change=1,
                filter_column=filter_column if filter_value else None,
                filter_value=filter_value if filter_value else None
            )
