import os
import sqlite3
import psycopg2
import pandas as pd
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        # Buscamos la variable de entorno que pusimos en Render
        self.database_url = os.getenv("DATABASE_URL")
        self._inicializar_bd()
    
    def _get_connection(self):
        """Obtiene conexión a Postgres (Nube) o SQLite (Local)"""
        try:
            if self.database_url:
                # Estamos en Render/Nube -> Usar PostgreSQL
                return psycopg2.connect(self.database_url)
            else:
                # Estamos en Local -> Usar SQLite
                return sqlite3.connect("inventario_ti.db")
        except Exception as e:
            print(f"Error de conexión: {e}")
            return None

    def _inicializar_bd(self):
        """Crea las tablas si no existen (Compatible con ambas BD)"""
        conn = self._get_connection()
        if not conn: return
        
        try:
            with conn:
                cursor = conn.cursor()
                
                # Sintaxis SQL compatible (SERIAL para Postgres, AUTOINCREMENT lo maneja SQLite diferente)
                # Truco: En Postgres usamos SERIAL PRIMARY KEY, en SQLite INTEGER PRIMARY KEY AUTOINCREMENT
                # Para simplificar, usamos sentencias separadas o try/except, pero aquí usaré sintaxis genérica:
                
                if self.database_url:
                    # --- CREACIÓN PARA POSTGRESQL ---
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS productos (
                            id SERIAL PRIMARY KEY,
                            sku TEXT UNIQUE NOT NULL,
                            nombre TEXT NOT NULL,
                            categoria TEXT,
                            marca TEXT,
                            precio_compra REAL DEFAULT 0,
                            precio_venta REAL DEFAULT 0,
                            stock INTEGER DEFAULT 0,
                            stock_minimo INTEGER DEFAULT 5,
                            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS movimientos (
                            id SERIAL PRIMARY KEY,
                            sku TEXT NOT NULL,
                            tipo TEXT NOT NULL,
                            cantidad INTEGER NOT NULL,
                            motivo TEXT,
                            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (sku) REFERENCES productos(sku)
                        );
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS historial (
                            id SERIAL PRIMARY KEY,
                            accion TEXT NOT NULL,
                            detalle TEXT,
                            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    ''')
                else:
                    # --- CREACIÓN PARA SQLITE (LOCAL) ---
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS productos (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            sku TEXT UNIQUE NOT NULL,
                            nombre TEXT NOT NULL,
                            categoria TEXT,
                            marca TEXT,
                            precio_compra REAL DEFAULT 0,
                            precio_venta REAL DEFAULT 0,
                            stock INTEGER DEFAULT 0,
                            stock_minimo INTEGER DEFAULT 5,
                            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS movimientos (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            sku TEXT NOT NULL,
                            tipo TEXT NOT NULL,
                            cantidad INTEGER NOT NULL,
                            motivo TEXT,
                            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (sku) REFERENCES productos(sku)
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS historial (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            accion TEXT NOT NULL,
                            detalle TEXT,
                            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
        except Exception as e:
            print(f"Error inicializando BD: {e}")
        finally:
            conn.close()

    # --- MÉTODOS AUXILIARES ---
    def _ejecutar_consulta(self, query, params=(), return_id=False):
        conn = self._get_connection()
        if not conn: return None
        
        try:
            # Adaptar placeholder: SQLite usa ?, Postgres usa %s
            if self.database_url:
                query = query.replace('?', '%s')
            
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    if return_id:
                        return cursor.fetchone()[0]
            return True
        except Exception as e:
            print(f"Error BD: {e}")
            return False
        finally:
            conn.close()

    def _leer_datos(self, query, params=()):
        conn = self._get_connection()
        if not conn: return []
        
        try:
            # Adaptar placeholder
            if self.database_url:
                query = query.replace('?', '%s')
                # Postgres ILIKE para búsquedas insensibles a mayúsculas
                if 'LIKE' in query and self.database_url:
                    query = query.replace('LIKE', 'ILIKE')

            return pd.read_sql_query(query, conn, params=params)
        except Exception as e:
            print(f"Error lectura BD: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    # --- FUNCIONES PÚBLICAS (Igual que antes, pero usando los métodos internos) ---

    def agregar_producto(self, sku, nombre, categoria, marca, precio_compra, precio_venta, stock, stock_minimo=5):
        query = '''
            INSERT INTO productos (sku, nombre, categoria, marca, precio_compra, precio_venta, stock, stock_minimo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        params = (sku, nombre, categoria, marca, precio_compra, precio_venta, stock, stock_minimo)
        
        if self._ejecutar_consulta(query, params):
            self._registrar_historial('creacion_producto', f'Producto {sku} - {nombre} creado')
            return True, "✅ Producto agregado"
        return False, "❌ Error: SKU duplicado o error de conexión"

    def obtener_productos(self, busqueda=""):
        if busqueda:
            query = '''
                SELECT sku, nombre, categoria, marca, precio_compra, precio_venta, stock, stock_minimo
                FROM productos
                WHERE sku LIKE ? OR nombre LIKE ? OR categoria LIKE ? OR marca LIKE ?
                ORDER BY nombre
            '''
            term = f"%{busqueda}%"
            df = self._leer_datos(query, (term, term, term, term))
        else:
            query = "SELECT * FROM productos ORDER BY nombre"
            df = self._leer_datos(query)
        
        return df.to_dict('records') if not df.empty else []

    def actualizar_stock(self, sku, cantidad, tipo, motivo=""):
        # 1. Verificar stock actual
        df = self._leer_datos("SELECT stock FROM productos WHERE sku = ?", (sku,))
        if df.empty: return False, "Producto no encontrado"
        
        stock_actual = df.iloc[0]['stock']
        
        if tipo == "entrada":
            nuevo_stock = stock_actual + cantidad
        else:
            nuevo_stock = stock_actual - cantidad
            if nuevo_stock < 0: return False, "Stock insuficiente"
            
        # 2. Actualizar
        q_update = "UPDATE productos SET stock = ?, fecha_actualizacion = CURRENT_TIMESTAMP WHERE sku = ?"
        if self._ejecutar_consulta(q_update, (nuevo_stock, sku)):
            # 3. Registrar movimiento
            q_mov = "INSERT INTO movimientos (sku, tipo, cantidad, motivo) VALUES (?, ?, ?, ?)"
            self._ejecutar_consulta(q_mov, (sku, tipo, cantidad, motivo))
            
            # 4. Historial
            self._registrar_historial('movimiento_stock', f'{tipo} de {cantidad} para {sku}')
            return True, f"Stock actualizado: {nuevo_stock}"
            
        return False, "Error al actualizar"

    def _registrar_historial(self, accion, detalle):
        query = "INSERT INTO historial (accion, detalle) VALUES (?, ?)"
        self._ejecutar_consulta(query, (accion, detalle))

    def obtener_kpis(self):
        df_prod = self._leer_datos("SELECT precio_compra, stock, stock_minimo FROM productos")
        if df_prod.empty:
            return {'total_items': 0, 'total_valor': 0, 'alertas': 0}
            
        total_items = len(df_prod)
        total_valor = (df_prod['precio_compra'] * df_prod['stock']).sum()
        alertas = len(df_prod[df_prod['stock'] < df_prod['stock_minimo']])
        
        return {
            'total_items': int(total_items),
            'total_valor': float(total_valor),
            'alertas': int(alertas)
        }

    def exportar_a_dataframe(self):
        return self._leer_datos("SELECT * FROM productos ORDER BY nombre")

    def obtener_historial_movimientos(self, limit=10):
        query = '''
            SELECT m.sku, p.nombre, m.tipo, m.cantidad, m.motivo, m.fecha
            FROM movimientos m
            JOIN productos p ON m.sku = p.sku
            ORDER BY m.fecha DESC LIMIT ?
        '''
        df = self._leer_datos(query, (limit,))
        return df.to_dict('records') if not df.empty else []

    def obtener_historial_completo(self):
        return self._leer_datos("SELECT * FROM historial ORDER BY fecha DESC LIMIT 100").to_dict('records')

    def obtener_estadisticas_avanzadas(self):
        # Esta consulta es compleja para el wrapper genérico, la hacemos directa con pandas
        conn = self._get_connection()
        if not conn: return {"por_categoria": {}}
        
        try:
            query = '''
                SELECT categoria, COUNT(*) as cantidad, SUM(stock) as total_stock, 
                       AVG(precio_compra) as precio_promedio, SUM(precio_compra * stock) as valor_total
                FROM productos
                WHERE categoria IS NOT NULL
                GROUP BY categoria
            '''
            df = pd.read_sql_query(query, conn)
            
            result = {"por_categoria": {}}
            for _, row in df.iterrows():
                cat = row['categoria']
                result["por_categoria"][cat] = {
                    "cantidad": int(row['cantidad']),
                    "total_stock": int(row['total_stock']),
                    "precio_promedio": float(row['precio_promedio']),
                    "valor_total": float(row['valor_total'])
                }
            return result
        except:
            return {"por_categoria": {}}
        finally:
            conn.close()

    def obtener_reporte_consolidado(self):
        # Simplificado reutilizando métodos
        return {
            "resumen": self.obtener_kpis(),
            "categorias": self.obtener_estadisticas_avanzadas()["por_categoria"]
        }