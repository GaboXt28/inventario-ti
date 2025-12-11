import pandas as pd
from database import DatabaseManager
from analisis_numpy import AnalisisNumerico
from functools import reduce

class SistemaInventario:
    def __init__(self):
        self.db = DatabaseManager()
        self.analizador_numpy = AnalisisNumerico(self)
        
    @property
    def df(self):
        """
        Propiedad que retorna el inventario completo como DataFrame.
        Incluye un 'Adaptador Universal' para manejar listas o DataFrames.
        """
        try:
            # 1. Obtener datos crudos de la BD
            datos = self.db.exportar_a_dataframe()
            
            # 2. Adaptador: Si llega una lista, convertirla a DataFrame
            if isinstance(datos, list):
                df = pd.DataFrame(datos)
            else:
                df = datos # Ya es un DataFrame
                
            # 3. Limpieza de tipos de datos
            if not df.empty:
                cols_numericas = ['precio_compra', 'precio_venta', 'stock', 'stock_minimo']
                for col in cols_numericas:
                    if col in df.columns:
                        # Forzamos conversión a número, los errores se vuelven 0
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        except Exception as e:
            print(f"Error crítico obteniendo DataFrame: {e}")
            return pd.DataFrame()
    
    def obtener_kpis(self):
        """Obtiene indicadores clave de rendimiento"""
        return self.db.obtener_kpis()
    
    def buscar_funcional(self, busqueda=""):
        """Busca productos y retorna un DataFrame limpio"""
        try:
            # Obtener datos (puede ser lista o DF)
            datos = self.db.obtener_productos(busqueda)
            
            # Adaptador
            if isinstance(datos, list):
                df = pd.DataFrame(datos)
            else:
                df = datos
            
            # Limpieza
            if not df.empty:
                cols_numericas = ['precio_compra', 'precio_venta', 'stock', 'stock_minimo']
                for col in cols_numericas:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        except Exception as e:
            print(f"Error en búsqueda: {e}")
            return pd.DataFrame()
    
    # --- MÉTODOS DE ESCRITURA (Pasamanos a la BD) ---
    
    def registrar_movimiento(self, sku, cantidad, tipo, motivo=""):
        # Normalizamos el tipo para la base de datos (minusculas)
        tipo_db = "entrada" if tipo.lower() == "entrada" else "salida"
        return self.db.actualizar_stock(sku, cantidad, tipo_db, motivo)
    
    def registrar_producto(self, sku, nombre, categoria, marca, precio_compra, precio_venta, stock):
        return self.db.agregar_producto(sku, nombre, categoria, marca, precio_compra, precio_venta, stock)
    
    # --- MÉTODOS DE HISTORIAL ---
    
    def obtener_historial_movimientos(self, limit=10):
        # Devuelve lista de diccionarios (perfecto para Streamlit)
        return self.db.obtener_movimientos_recientes(limit)
    
    def obtener_historial_completo(self):
        return self.db.obtener_historial()
    
    # --- LÓGICA DE NEGOCIO Y PROG. FUNCIONAL ---
    
    def _convertir_valor_seguro(self, valor, tipo_esperado):
        """Ayudante para conversiones seguras de tipos"""
        try:
            if tipo_esperado == 'float':
                return float(valor)
            elif tipo_esperado == 'int':
                return int(float(valor)) # Maneja strings como "5.0"
            return str(valor)
        except:
            return 0 if tipo_esperado in ['int', 'float'] else ""

    def aplicar_descuento(self, porcentaje):
        """Proyección de precios usando map (Programación Funcional)"""
        try:
            productos = self.db.obtener_productos("") # Devuelve lista
            if not productos: return []
            
            # Si devuelve DF, convertir a lista de dicts para usar map
            if isinstance(productos, pd.DataFrame):
                productos = productos.to_dict('records')
            
            pct = self._convertir_valor_seguro(porcentaje, 'float')
            
            # map devuelve un iterador, lo convertimos a lista
            return list(map(
                lambda p: {
                    **p,
                    'precio_venta_con_descuento': float(p.get('precio_venta', 0)) * (1 - pct/100),
                    'descuento_aplicado': pct
                },
                productos
            ))
        except Exception as e:
            print(f"Error en map: {e}")
            return []

    def obtener_productos_criticos(self, umbral=5):
        """Filtrado de stock bajo usando filter (Programación Funcional)"""
        try:
            productos = self.db.obtener_productos("")
            if not productos: return []
            
            if isinstance(productos, pd.DataFrame):
                productos = productos.to_dict('records')
            
            limite = self._convertir_valor_seguro(umbral, 'int')
            
            return list(filter(
                lambda p: int(p.get('stock', 0)) < limite,
                productos
            ))
        except Exception as e:
            print(f"Error en filter: {e}")
            return []

    def calcular_valor_total_inventario(self):
        """Cálculo acumulativo usando reduce (Programación Funcional)"""
        try:
            productos = self.db.obtener_productos("")
            if not productos: return 0.0
            
            if isinstance(productos, pd.DataFrame):
                productos = productos.to_dict('records')
                
            return reduce(
                lambda acc, p: acc + (float(p.get('precio_compra', 0)) * int(p.get('stock', 0))),
                productos, 
                0.0
            )
        except Exception as e:
            print(f"Error en reduce: {e}")
            return 0.0

    # --- ENLACES A MÓDULOS DE ANÁLISIS ---
    
    def obtener_reporte_consolidado(self):
        return self.db.obtener_reporte_consolidado()
        
    def obtener_estadisticas_avanzadas(self):
        return self.db.obtener_estadisticas_avanzadas()

    def analizar_precios_numpy(self):
        # Delega al módulo de numpy
        if self.analizador_numpy:
            return self.analizador_numpy.analizar_precios()
        return {}
    
    def identificar_outliers_numpy(self):
        if self.analizador_numpy:
            return self.analizador_numpy.identificar_outliers()
        return []
        
    def ejercicio_numpy_reshape(self):
        # Intenta usar el método de DB o retorna vacío si no existe
        return self.db.ejercicio_numpy_reshape() if hasattr(self.db, 'ejercicio_numpy_reshape') else {}
        
    def ejercicio_numpy_sort(self):
        return self.db.ejercicio_numpy_sort() if hasattr(self.db, 'ejercicio_numpy_sort') else {}