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
        # BLINDAJE: Convertir cualquier cosa que llegue a DataFrame
        datos = self.db.exportar_a_dataframe()
        if isinstance(datos, list):
            df = pd.DataFrame(datos)
        else:
            df = datos
            
        if not df.empty:
            for c in ['precio_compra', 'precio_venta', 'stock']:
                if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        return df
    
    def buscar_funcional(self, busqueda=""):
        datos = self.db.obtener_productos(busqueda)
        # BLINDAJE: Siempre devolver DataFrame a la App
        return pd.DataFrame(datos) if datos else pd.DataFrame()
    
    # --- Pasarelas directas (Wrappers) ---
    def registrar_producto(self, *args): return self.db.agregar_producto(*args)
    def registrar_movimiento(self, sku, cant, tipo, mot=""): 
        tipo = "entrada" if tipo.lower() == "entrada" else "salida"
        return self.db.actualizar_stock(sku, cant, tipo, mot)
    
    def obtener_kpis(self): return self.db.obtener_kpis()
    def obtener_historial_movimientos(self, limit=10): return self.db.obtener_movimientos_recientes(limit)
    def obtener_historial_completo(self): return self.db.obtener_historial()
    def obtener_estadisticas_avanzadas(self): return self.db.obtener_estadisticas_avanzadas()
    def obtener_reporte_consolidado(self): return self.db.obtener_reporte_consolidado()
    
    # --- NumPy y Lógica ---
    def analizar_precios_numpy(self): return self.analizador_numpy.analizar_precios()
    def identificar_outliers_numpy(self): return self.analizador_numpy.identificar_outliers()
    
    def aplicar_descuento(self, pct):
        try:
            prods = self.db.obtener_productos("")
            return [{**p, 'nuevo_precio': p['precio_venta']*(1-pct/100)} for p in prods]
        except: return []

    def obtener_productos_criticos(self, umbral=5):
        try:
            prods = self.db.obtener_productos("")
            return [p for p in prods if p.get('stock', 0) < umbral]
        except: return []

    def calcular_valor_total_inventario(self):
        try:
            prods = self.db.obtener_productos("")
            return reduce(lambda a,b: a + (b['precio_compra']*b['stock']), prods, 0)
        except: return 0