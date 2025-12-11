import numpy as np

class AnalisisNumerico:
    def __init__(self, sistema_inventario):
        self.sistema = sistema_inventario
    
    def analizar_precios(self):
        """Análisis numérico de precios usando NumPy"""
        try:
            productos = self.sistema.db.obtener_productos("")
            if not productos:
                return {}
            
            # Convertir a arrays de NumPy asegurando tipos numéricos
            precios_compra = np.array([float(p.get('precio_compra', 0)) for p in productos])
            precios_venta = np.array([float(p.get('precio_venta', 0)) for p in productos])
            stocks = np.array([int(p.get('stock', 0)) for p in productos])
            
            # Cálculos estadísticos
            analisis = {
                "precios_compra": {
                    "media": float(np.mean(precios_compra)) if len(precios_compra) > 0 else 0,
                    "mediana": float(np.median(precios_compra)) if len(precios_compra) > 0 else 0,
                    "std": float(np.std(precios_compra)) if len(precios_compra) > 0 else 0,
                    "min": float(np.min(precios_compra)) if len(precios_compra) > 0 else 0,
                    "max": float(np.max(precios_compra)) if len(precios_compra) > 0 else 0,
                    "percentil_25": float(np.percentile(precios_compra, 25)) if len(precios_compra) > 0 else 0,
                    "percentil_75": float(np.percentile(precios_compra, 75)) if len(precios_compra) > 0 else 0
                },
                "precios_venta": {
                    "media": float(np.mean(precios_venta)) if len(precios_venta) > 0 else 0,
                    "mediana": float(np.median(precios_venta)) if len(precios_venta) > 0 else 0,
                    "std": float(np.std(precios_venta)) if len(precios_venta) > 0 else 0
                },
                "margenes": {
                    "margen_promedio": float(np.mean((precios_venta - precios_compra) / precios_compra * 100)) if len(precios_compra) > 0 and np.all(precios_compra > 0) else 0,
                    "margen_total": float(np.sum(precios_venta - precios_compra)) if len(precios_compra) > 0 else 0
                },
                "valor_inventario": {
                    "valor_total": float(np.sum(precios_compra * stocks)) if len(precios_compra) > 0 else 0,
                    "valor_promedio_por_producto": float(np.mean(precios_compra * stocks)) if len(precios_compra) > 0 else 0
                }
            }
            
            return analisis
        except Exception as e:
            print(f"Error en análisis NumPy: {e}")
            return {}
    
    def identificar_outliers(self):
        """Identificar precios atípicos usando NumPy"""
        try:
            productos = self.sistema.db.obtener_productos("")
            if not productos or len(productos) < 3:
                return []
            
            precios = np.array([float(p.get('precio_venta', 0)) for p in productos])
            
            # Calcular Q1, Q3 e IQR
            Q1 = np.percentile(precios, 25)
            Q3 = np.percentile(precios, 75)
            IQR = Q3 - Q1
            
            # Evitar división por cero
            if IQR == 0:
                return []
            
            # Definir límites para outliers
            limite_inferior = Q1 - 1.5 * IQR
            limite_superior = Q3 + 1.5 * IQR
            
            # Identificar outliers
            outliers = []
            for producto in productos:
                precio = float(producto.get('precio_venta', 0))
                if precio < limite_inferior:
                    outliers.append({
                        **producto,
                        "tipo_outlier": "Bajo",
                        "precio": precio,
                        "limite_inferior": limite_inferior,
                        "limite_superior": limite_superior
                    })
                elif precio > limite_superior:
                    outliers.append({
                        **producto,
                        "tipo_outlier": "Alto",
                        "precio": precio,
                        "limite_inferior": limite_inferior,
                        "limite_superior": limite_superior
                    })
            
            return outliers
        except Exception as e:
            print(f"Error identificando outliers: {e}")
            return []
    
    def analisis_clustering_basico(self):
        """Análisis básico de clustering de precios"""
        try:
            productos = self.sistema.db.obtener_productos("")
            if not productos or len(productos) < 2:
                return {}
            
            # Crear matriz de características asegurando tipos numéricos
            caracteristicas = []
            for p in productos:
                caracteristicas.append([
                    float(p.get('precio_compra', 0)),
                    float(p.get('precio_venta', 0)),
                    int(p.get('stock', 0))
                ])
            
            caracteristicas = np.array(caracteristicas)
            
            # Verificar que no haya columnas con desviación estándar cero
            stds = np.std(caracteristicas, axis=0)
            if np.any(stds == 0):
                # Si alguna columna tiene std=0, usar datos sin normalizar
                caracteristicas_norm = caracteristicas
            else:
                # Normalizar
                caracteristicas_norm = (caracteristicas - np.mean(caracteristicas, axis=0)) / stds
            
            # Análisis básico (sin ML avanzado)
            analisis = {
                "correlaciones": {
                    "precio_compra_venta": float(np.corrcoef(caracteristicas[:, 0], caracteristicas[:, 1])[0, 1]) if len(caracteristicas) > 1 else 0,
                    "precio_stock": float(np.corrcoef(caracteristicas[:, 0], caracteristicas[:, 2])[0, 1]) if len(caracteristicas) > 1 else 0
                },
                "estadisticas_agrupadas": {
                    "media_caracteristicas": np.mean(caracteristicas, axis=0).tolist() if len(caracteristicas) > 0 else [0, 0, 0],
                    "std_caracteristicas": np.std(caracteristicas, axis=0).tolist() if len(caracteristicas) > 0 else [0, 0, 0]
                }
            }
            
            return analisis
        except Exception as e:
            print(f"Error en clustering: {e}")
            return {}