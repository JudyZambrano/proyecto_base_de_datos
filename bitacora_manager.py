# bitacora_manager.py
import streamlit as st
from db_manager import DBManager # Asume que DBManager está en db_manager.py
from datetime import datetime

class BitacoraManager:
    def __init__(self, db_manager: DBManager):
        self.db_manager = db_manager
        self.table_name = "bitacora"
        self.id_column = "id_bitacora" # Columna ID de la tabla bitacora

        # Define las columnas de la tabla bitacora y sus tipos (para el formulario CRUD)
        # Ajusta los tipos según cómo los necesites en los inputs de Streamlit
        self.columns = {
            "id_bitacora": "SERIAL", # Es SERIAL, no se edita/inserta manualmente
            "id_usuario": "INT",
            "nombre_usuario": "TEXT",
            "hora_inicio": "TIMESTAMP",
            "hora_salida": "TIMESTAMP",
            "navegador": "TEXT",
            "ip": "TEXT",
            "maquina": "TEXT",
            "tabla_afectada": "TEXT",
            "accion": "TEXT"
        }

    @st.cache_data(ttl=5) # Cachear los datos por 5 segundos para evitar consultas excesivas
    def get_all_records(self, offset=0, limit=10, filter_column=None, filter_value=None):
        """Obtiene todos los registros de la bitácora con paginación y filtro."""
        try:
            conn = self.db_manager.get_connection()
            if conn is None:
                st.error("No hay conexión a la base de datos para obtener la bitácora.")
                return pd.DataFrame(), 0

            cur = conn.cursor()
            
            # Construir la consulta base
            query = f"SELECT {', '.join(self.columns.keys())} FROM {self.table_name}"
            count_query = f"SELECT COUNT(*) FROM {self.table_name}"
            
            where_clauses = []
            params = []

            # Añadir filtro si está presente
            if filter_column and filter_value:
                # Usar ILIKE para búsqueda insensible a mayúsculas/minúsculas
                where_clauses.append(f"{filter_column} ILIKE %s")
                params.append(f"%{filter_value}%")

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
                count_query += " WHERE " + " AND ".join(where_clauses)
            
            # Ordenar por hora_inicio descendente para la bitácora
            query += " ORDER BY hora_inicio DESC"
            
            # Obtener el total de registros para paginación
            cur.execute(count_query, params)
            total_records = cur.fetchone()[0]

            # Añadir paginación
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cur.execute(query, params)
            records = cur.fetchall()
            
            # Obtener nombres de columnas en el orden correcto
            col_names = [desc[0] for desc in cur.description]
            df = pd.DataFrame(records, columns=col_names)
            
            cur.close()
            return df, total_records
        except Exception as e:
            st.error(f"Error al cargar la bitácora: {e}")
            return pd.DataFrame(), 0

    # --- Métodos CRUD (adaptados para Bitacora: solo lectura y quizás limpieza) ---
    # Para la bitácora, usualmente no se permite "Crear", "Actualizar" o "Eliminar"
    # directamente desde una interfaz CRUD normal, ya que los logs deben ser inmutables.
    # Los logs se "Crean" internamente por las acciones de la aplicación o triggers.
    # Sin embargo, si quieres permitir la "Eliminación" de logs antiguos (limpieza),
    # puedes implementar delete_record_logic.

    # NOTA: create_record_logic y update_record_logic no se usarán directamente
    # para la bitácora en una gestión normal, ya que los registros se insertan automáticamente
    # a través de la función log_action_to_db().

    def create_record_logic(self, data):
        st.warning("La creación directa de registros en la bitácora no está permitida.")
        return False

    def update_record_logic(self, data):
        st.warning("La actualización directa de registros en la bitácora no está permitida.")
        return False

    def delete_record_logic(self, record_id):
        """Permite eliminar un registro de la bitácora por su ID."""
        if not record_id:
            st.error(f"Por favor, introduce el ID del registro de {self.table_name} a eliminar.")
            return False
        
        try:
            conn = self.db_manager.get_connection()
            if conn is None:
                st.error("No hay conexión a la base de datos para eliminar el registro.")
                return False
            
            cur = conn.cursor()
            query = f"DELETE FROM {self.table_name} WHERE {self.id_column} = %s"
            cur.execute(query, (record_id,))
            conn.commit()
            
            if cur.rowcount > 0:
                st.success(f"Registro con ID {record_id} eliminado exitosamente de {self.table_name}.")
                st.cache_data.clear() # Limpiar caché para refrescar la tabla
                return True
            else:
                st.warning(f"No se encontró ningún registro con ID {record_id} en {self.table_name}.")
                return False
        except Exception as e:
            st.error(f"Error al eliminar registro de {self.table_name}: {e}")
            return False

    def load_selected_record_logic(self, record_id):
        st.warning("La carga de registros individuales para edición en la bitácora no es usualmente necesaria.")
        return None

    def load_data_logic(self, table_placeholder, pagination_info, pagination_label_placeholder, page_change=0, filter_column=None, filter_value=None):
        """
        Carga y muestra los datos de la bitácora con paginación y filtros.
        """
        offset = pagination_info["offset"]
        limit = pagination_info["limit"]
        current_page = pagination_info["current_page"]

        if page_change != 0: # Si se hizo clic en un botón de paginación
            new_offset = offset + (page_change * limit)
            if new_offset >= 0:
                offset = new_offset
                current_page += page_change
            pagination_info["offset"] = offset
            pagination_info["current_page"] = current_page
            st.rerun() # Forzar re-render

        df, total_records = self.get_all_records(offset, limit, filter_column, filter_value)
        pagination_info["total_records"] = total_records

        total_pages = (total_records + limit - 1) // limit if total_records > 0 else 1

        if not df.empty:
            table_placeholder.dataframe(df, use_container_width=True)
            pagination_label_placeholder.markdown(f"Página **{current_page}** de **{total_pages}** (Total: **{total_records}** registros)")
        else:
            table_placeholder.info("No hay registros que mostrar en la bitácora con los filtros actuales.")
            pagination_label_placeholder.empty() # Limpiar la etiqueta de paginación
            pagination_info["total_records"] = 0 # Asegurar que el total sea 0


def log_action_to_db(db_manager: DBManager, id_usuario: int | None, nombre_usuario: str, accion: str, tabla_afectada: str | None = None, navegador: str | None = None, ip: str | None = None, maquina: str | None = None):
    """
    Registra una acción en la tabla 'bitacora' de la base de datos.
    Se conecta directamente a la BD para asegurar el registro.
    """
    conn = None
    cur = None
    try:
        conn = db_manager.get_connection() # Obtener conexión desde el DBManager
        if conn is None:
            st.error("No hay conexión de BD disponible para registrar en bitácora.")
            return

        cur = conn.cursor()

        query = """
        INSERT INTO bitacora (id_usuario, nombre_usuario, hora_inicio, navegador, ip, maquina, tabla_afectada, accion)
        VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s);
        """
        # Usar valores predeterminados para IP, navegador, máquina si no se proporcionan
        # En Streamlit, obtener la IP real del cliente es complicado sin un proxy
        navegador = navegador if navegador else "Streamlit_App"
        ip = ip if ip else "N/A" # En local, será 127.0.0.1; en Streamlit Cloud es más complejo
        maquina = maquina if maquina else "Servidor_Streamlit"

        cur.execute(query, (id_usuario, nombre_usuario, navegador, ip, maquina, tabla_afectada, accion))
        conn.commit()
        st.success(f"Acción '{accion}' registrada en bitácora por '{nombre_usuario}'.", icon="📝")
        st.cache_data.clear() # Limpiar caché de bitácora para que se refresque
    except Exception as e:
        st.error(f"Error al registrar en bitácora: {e}", icon="⚠️")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()