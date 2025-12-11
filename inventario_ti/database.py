import os
import sqlite3
import psycopg2
import pandas as pd
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        # Detectar si estamos en Render (Nube) o Local
        self.database_url = os.getenv("DATABASE_URL")
        self._inicializar_bd()
    
    def _get_connection(self):
        try:
            if self.database_url:
                return psycopg2.connect(self.database_url)
            else:
                return sqlite3.connect("inventario_ti.db")
        except Exception as e:
            print(f"Error de conexión: {e}")
            return None

    def _inicializar_bd(self):
        conn = self._get_connection()
        if not conn: return
        try:
            with conn:
                cursor = conn.cursor()
                # Crear tablas (Compatible con SQLite y Postgres)
                if self.database_url:
                    # Postgres
                    cursor.execute('CREATE TABLE IF NOT EXISTS productos (id SERIAL PRIMARY KEY, sku TEXT UNIQUE, nombre TEXT, categoria TEXT, marca TEXT, precio_compra REAL, precio_venta REAL, stock INTEGER, stock_minimo INTEGER DEFAULT 5, fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP, fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
                    cursor.execute('CREATE TABLE IF NOT EXISTS movimientos (id SERIAL PRIMARY KEY, sku TEXT, tipo TEXT, cantidad INTEGER, motivo TEXT, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
                    cursor.execute('CREATE TABLE IF NOT EXISTS historial (id SERIAL PRIMARY KEY, accion TEXT, detalle TEXT, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
                else:
                    # SQLite
                    cursor.execute('CREATE TABLE IF NOT EXISTS productos (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT UNIQUE, nombre TEXT, categoria TEXT, marca TEXT, precio_compra REAL, precio_venta REAL, stock INTEGER, stock_minimo INTEGER DEFAULT 5, fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP, fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
                    cursor.execute('CREATE TABLE IF NOT EXISTS movimientos (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, tipo TEXT, cantidad INTEGER, motivo TEXT, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
                    cursor.execute('CREATE TABLE IF NOT EXISTS historial (id INTEGER PRIMARY KEY AUTOINCREMENT, accion TEXT, detalle TEXT, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
        except Exception as e:
            print(f"Error init BD: {e}")
        finally:
            conn.close()

    def _ejecutar_consulta(self, query, params=()):
        conn = self._get_connection()
        if not conn: return False
        try:
            if self.database_url: query = query.replace('?', '%s')
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
            return True
        except Exception as e:
            print(f"Error SQL: {e}")
            return False
        finally:
            conn.close()

    def _leer_datos(self, query, params=()):
        conn = self._get_connection()
        if not conn: return pd.DataFrame() # Retornar DF vacío siempre en error
        try:
            if self.database_url: 
                query = query.replace('?', '%s')
                if 'LIKE' in query: query = query.replace('LIKE', 'ILIKE')
            
            return pd.read_sql_query(query, conn, params=params)
        except Exception as e:
            print(f"Error lectura: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    # --- FUNCIONES PRINCIPALES ---

    def obtener_productos(self, busqueda=""):
        if busqueda:
            query = "SELECT * FROM productos WHERE sku LIKE ? OR nombre LIKE ? OR marca LIKE ? ORDER BY nombre"
            term = f"%{busqueda}%"
            df = self._leer_datos(query, (term, term, term))
        else:
            df = self._leer_datos("SELECT * FROM productos ORDER BY nombre")
        
        # IMPORTANTE: Devolvemos lista de diccionarios para compatibilidad
        return df.to_dict('records') if not df.empty else []

    def exportar_a_dataframe(self):
        # Esta funcion SÍ devuelve DataFrame puro
        return self._leer_datos("SELECT * FROM productos ORDER BY nombre")

    def agregar_producto(self, sku, nombre, cat, marca, pc, pv, stock, min_stock=5):
        q = "INSERT INTO productos (sku, nombre, categoria, marca, precio_compra, precio_venta, stock, stock_minimo) VALUES (?,?,?,?,?,?,?,?)"
        if self._ejecutar_consulta(q, (sku, nombre, cat, marca, pc, pv, stock, min_stock)):
            self._historial('creacion', f'Creado {sku}')
            return True, "Producto creado"
        return False, "Error: SKU duplicado"

    def actualizar_stock(self, sku, cant, tipo, motivo=""):
        df = self._leer_datos("SELECT stock FROM productos WHERE sku = ?", (sku,))
        if df.empty: return False, "No existe producto"
        
        actual = df.iloc[0]['stock']
        nuevo = actual + cant if tipo == 'entrada' else actual - cant
        if nuevo < 0: return False, "Stock insuficiente"
        
        if self._ejecutar_consulta("UPDATE productos SET stock = ? WHERE sku = ?", (nuevo, sku)):
            self._ejecutar_consulta("INSERT INTO movimientos (sku, tipo, cantidad, motivo) VALUES (?,?,?,?)", (sku, tipo, cant, motivo))
            self._historial('movimiento', f'{tipo} {cant} unid. {sku}')
            return True, "Stock actualizado"
        return False, "Error update"

    def obtener_kpis(self):
        df = self._leer_datos("SELECT precio_compra, stock, stock_minimo FROM productos")
        if df.empty: return {'total_items': 0, 'total_valor': 0, 'alertas': 0}
        return {
            'total_items': len(df),
            'total_valor': (df['precio_compra'] * df['stock']).sum(),
            'alertas': len(df[df['stock'] < df['stock_minimo']])
        }

    def obtener_movimientos_recientes(self, limit=10):
        # Aseguramos que existe la función que daba error
        q = "SELECT m.*, p.nombre FROM movimientos m JOIN productos p ON m.sku = p.sku ORDER BY m.fecha DESC LIMIT ?"
        df = self._leer_datos(q, (limit,))
        return df.to_dict('records') if not df.empty else []

    def obtener_historial(self):
        # Aseguramos que existe la función que daba error
        return self._leer_datos("SELECT * FROM historial ORDER BY fecha DESC LIMIT 50").to_dict('records')

    def obtener_estadisticas_avanzadas(self):
        df = self._leer_datos("SELECT categoria, count(*) as cant, sum(stock) as st, sum(precio_compra*stock) as val FROM productos GROUP BY categoria")
        if df.empty: return {"por_categoria": {}}
        res = {}
        for _, r in df.iterrows():
            res[r['categoria']] = {'cantidad': r['cant'], 'total_stock': r['st'], 'valor_total': r['val']}
        return {"por_categoria": res}

    def obtener_reporte_consolidado(self):
        return {"resumen": self.obtener_kpis(), "categorias": self.obtener_estadisticas_avanzadas()["por_categoria"]}

    def _historial(self, acc, det):
        self._ejecutar_consulta("INSERT INTO historial (accion, detalle) VALUES (?,?)", (acc, det))