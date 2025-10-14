import oracledb
import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar .env desde el directorio raíz del proyecto
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

class Database:
    def __init__(self):
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.host = os.getenv('DB_HOST')
        self.port = os.getenv('DB_PORT')
        self.service = os.getenv('DB_SERVICE')
        self.dsn = f"{self.host}:{self.port}/{self.service}"
        
    def get_connection(self):
        """Obtiene una conexión a la base de datos"""
        try:
            connection = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn
            )
            return connection
        except oracledb.Error as e:
            print(f"Error conectando a la base de datos: {e}")
            raise
    
    def execute_query(self, query, params=None, fetch=True):
        """Ejecuta una consulta y retorna los resultados"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                columns = [col[0] for col in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                result = [dict(zip(columns, row)) for row in rows]
                return result
            else:
                connection.commit()
                return {"affected_rows": cursor.rowcount}
                
        except oracledb.Error as e:
            if connection:
                connection.rollback()
            print(f"Error ejecutando query: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def execute_many(self, query, data_list):
        """Ejecuta múltiples inserts/updates"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.executemany(query, data_list)
            connection.commit()
            return {"affected_rows": cursor.rowcount}
        except oracledb.Error as e:
            if connection:
                connection.rollback()
            print(f"Error ejecutando query: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

# Instancia global
db = Database()


