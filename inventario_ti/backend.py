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
        """Propiedad que retorna DataFrame de productos"""
        try:
            df = self.db.exportar_a_dataframe()
            # Asegurar tipos de datos correctos
            if not df.empty:
                df['precio_compra'] = pd.to_numeric(df['precio_compra'], errors='coerce').fillna(0)
                df['precio_venta'] = pd.to_numeric(df['precio_venta'], errors='coerce').fillna(0)
                df['stock'] = pd.to_numeric(df['stock'], errors='coerce').fillna(0).astype(int)
            return df
        except Exception as e:
            print(f"Error obteniendo DataFrame: {e}")
            return pd.DataFrame()
    
    def obtener_kpis(self):
        return self.db.obtener_kpis()
    
    def buscar_funcional(self, busqueda=""):
        productos = self.db.obtener_productos(busqueda)
        # Convertir a DataFrame asegurando tipos
        if productos:
            df = pd.DataFrame(productos)
            # Convertir columnas numéricas
            numeric_cols = ['precio_compra', 'precio_venta', 'stock', 'stock_minimo']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        return pd.DataFrame()
    
    def registrar_movimiento(self, sku, cantidad, tipo, motivo=""):
        tipo_db = "entrada" if tipo == "Entrada" else "salida"
        return self.db.actualizar_stock(sku, cantidad, tipo_db)
    
    def registrar_producto(self, sku, nombre, categoria, marca, precio_compra, precio_venta, stock):
        return self.db.agregar_producto(sku, nombre, categoria, marca, precio_compra, precio_venta, stock)
    
    def obtener_historial_movimientos(self, limit=10):
        return self.db.obtener_movimientos_recientes(limit)
    
    def obtener_historial_completo(self):
        return self.db.obtener_historial()
    
    # --- FUNCIONES DE CONVERSIÓN SEGURA ---
    def _convertir_valor_seguro(self, valor, tipo_esperado):
        """Convertir valor de forma segura al tipo esperado"""
        try:
            if tipo_esperado == 'float':
                return float(valor)
            elif tipo_esperado == 'int':
                # Primero intentar como float, luego como int
                try:
                    return int(float(valor))
                except:
                    return int(valor)
            else:
                return str(valor)
        except (ValueError, TypeError):
            # Si falla la conversión, retornar valor por defecto
            if tipo_esperado == 'float':
                return 0.0
            elif tipo_esperado == 'int':
                return 0
            else:
                return ""
    
    # --- FUNCIONES DE PROGRAMACIÓN FUNCIONAL (LO APRENDIDO EN CLASES) ---
    
    def aplicar_descuento(self, porcentaje):
        """Aplica descuento a todos los productos usando map"""
        try:
            productos = self.db.obtener_productos("")
            if not productos:
                return []
            
            # Convertir porcentaje a float
            porcentaje_float = self._convertir_valor_seguro(porcentaje, 'float')
            
            # Usando map para transformar
            productos_con_descuento = list(map(
                lambda p: {
                    **p,
                    'precio_venta_con_descuento': float(p.get('precio_venta', 0)) * (1 - porcentaje_float/100),
                    'descuento_aplicado': porcentaje_float
                },
                productos
            ))
            return productos_con_descuento
        except Exception as e:
            print(f"Error aplicando descuento: {e}")
            return []
    
    def obtener_productos_criticos(self, umbral=5):
        """Obtiene productos con stock crítico usando filter"""
        try:
            productos = self.db.obtener_productos("")
            if not productos:
                return []
            
            # Convertir umbral a int
            umbral_int = self._convertir_valor_seguro(umbral, 'int')
            
            # Usando filter con conversión segura
            productos_criticos = list(filter(
                lambda p: int(p.get('stock', 0)) < umbral_int,
                productos
            ))
            return productos_criticos
        except Exception as e:
            print(f"Error obteniendo productos críticos: {e}")
            return []
    
    def calcular_valor_total_inventario(self):
        """Calcula valor total del inventario usando reduce"""
        try:
            productos = self.db.obtener_productos("")
            if not productos:
                return 0.0
            
            # Usando reduce con conversión segura
            valor_total = reduce(
                lambda acc, p: acc + (float(p.get('precio_compra', 0)) * int(p.get('stock', 0))),
                productos,
                0.0
            )
            return valor_total
        except Exception as e:
            print(f"Error calculando valor total: {e}")
            return 0.0
    
    def buscar_avanzado(self, criterio, valor):
        """Búsqueda avanzada con funciones lambda - Versión segura"""
        productos = self.db.obtener_productos("")
        
        try:
            if criterio == "precio_mayor":
                valor_convertido = self._convertir_valor_seguro(valor, 'float')
                return list(filter(
                    lambda p: float(p.get('precio_venta', 0)) > valor_convertido, 
                    productos
                ))
            
            elif criterio == "precio_menor":
                valor_convertido = self._convertir_valor_seguro(valor, 'float')
                return list(filter(
                    lambda p: float(p.get('precio_venta', 0)) < valor_convertido, 
                    productos
                ))
            
            elif criterio == "stock_bajo":
                valor_convertido = self._convertir_valor_seguro(valor, 'int')
                return list(filter(
                    lambda p: int(p.get('stock', 0)) < valor_convertido, 
                    productos
                ))
            
            elif criterio == "marca":
                valor_str = str(valor)
                return list(filter(
                    lambda p: valor_str.lower() in str(p.get('marca', '')).lower(), 
                    productos
                ))
            
            else:
                return productos
                
        except Exception as e:
            print(f"Error en búsqueda avanzada: {e}")
            return productos
    
    # --- DICCIONARIOS AVANZADOS (LO APRENDIDO EN CLASES) ---
    
    def obtener_estadisticas_avanzadas(self):
        """Obtener estadísticas avanzadas usando diccionarios anidados"""
        return self.db.obtener_estadisticas_avanzadas()
    
    def obtener_reporte_consolidado(self):
        """Obtener reporte consolidado"""
        return self.db.obtener_reporte_consolidado()
    
    # --- NUMPY - CIENCIA DE DATOS (LO APRENDIDO EN CLASES) ---
    
    def analizar_precios_numpy(self):
        """Análisis de precios usando NumPy"""
        return self.analizador_numpy.analizar_precios()
    
    def identificar_outliers_numpy(self):
        """Identificar outliers usando NumPy"""
        return self.analizador_numpy.identificar_outliers()
    
    def analizar_correlaciones_numpy(self):
        """Analizar correlaciones usando NumPy"""
        return self.analizador_numpy.analisis_clustering_basico()
    
    # --- EJERCICIOS PRÁCTICOS DE CLASE APLICADOS ---
    
    def ejercicio_numpy_reshape(self):
        """Aplicar ejercicio de reshape de arrays 1D a 2D"""
        try:
            import numpy as np
            productos = self.db.obtener_productos("")
            
            if len(productos) >= 12:
                # Tomar stocks de primeros 12 productos, convertir a enteros de forma segura
                stocks = []
                for p in productos[:12]:
                    try:
                        stocks.append(int(p.get('stock', 0)))
                    except:
                        stocks.append(0)
                
                stocks = np.array(stocks)
                stocks_2d = stocks.reshape(4, 3)
                
                return {
                    "original": stocks.tolist(),
                    "reshaped": stocks_2d.tolist(),
                    "forma_original": stocks.shape,
                    "forma_nueva": stocks_2d.shape
                }
            else:
                return {"error": "Se necesitan al menos 12 productos"}
        except Exception as e:
            return {"error": str(e)}
    
    def ejercicio_numpy_sort(self):
        """Aplicar ejercicio de ordenamiento por diferentes ejes"""
        try:
            import numpy as np
            productos = self.db.obtener_productos("")
            
            if len(productos) >= 4:
                # Crear matriz con precios y stocks, asegurando tipos numéricos
                datos = []
                for p in productos[:4]:
                    try:
                        datos.append([
                            float(p.get('precio_compra', 0)), 
                            float(p.get('precio_venta', 0)), 
                            int(p.get('stock', 0))
                        ])
                    except:
                        datos.append([0.0, 0.0, 0])
                
                datos = np.array(datos)
                
                return {
                    "original": datos.tolist(),
                    "ordenado_eje_0": np.sort(datos, axis=0).tolist(),
                    "ordenado_eje_1": np.sort(datos, axis=1).tolist(),
                    "aplanado_ordenado": np.sort(datos.flatten()).tolist()
                }
            else:
                return {"error": "Se necesitan al menos 4 productos"}
        except Exception as e:
            return {"error": str(e)}