import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from backend import SistemaInventario
import hashlib
import json
import os
from typing import Dict

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA (ESTO DEBE IR PRIMERO SIEMPRE PARA EVITAR PANTALLA NEGRA)
# ==============================================================================
st.set_page_config(
    page_title="TechInventory Pro",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# 2. ESTILOS CSS GLOBALES (SOLUCIÓN A LETRAS INVISIBLES)
# ==============================================================================
st.markdown("""
<style>
    /* --- REGLA MAESTRA: Todo texto dentro de tarjetas blancas será NEGRO --- */
    .card, .login-card, .login-header, [data-testid="stForm"] {
        color: #000000 !important;
    }
    
    .card h1, .card h2, .card h3, .card p, .card span, .card div,
    .login-card h1, .login-card p,
    [data-testid="stForm"] label, [data-testid="stForm"] p {
        color: #000000 !important;
    }

    /* --- INPUTS Y CAJAS DE TEXTO (Fondo Blanco + Letra Negra) --- */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
        caret-color: #000000 !important; /* El cursor parpadeante */
    }
    
    /* Etiquetas de los inputs */
    .stTextInput label, .stNumberInput label, .stSelectbox label {
        color: #333333 !important;
        font-weight: 600 !important;
    }

    /* --- TARJETAS DEL DASHBOARD (Fondo Blanco) --- */
    .card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 5px solid #667eea;
    }

    /* --- LOGIN ESPECÍFICO --- */
    .login-header {
        background-color: #ffffff;
        padding: 30px 20px 10px 20px;
        border-top-left-radius: 20px;
        border-top-right-radius: 20px;
        text-align: center;
        margin-bottom: 0px; 
    }
    
    /* Quitamos el borde y sombra por defecto del form de streamlit para unirlo al header */
    [data-testid="stForm"] {
        background-color: #ffffff;
        border-bottom-left-radius: 20px;
        border-bottom-right-radius: 20px;
        padding: 20px;
        border: none;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }

    /* --- FONDO GENERAL --- */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
</style>
""", unsafe_allow_html=True)

# ========== SISTEMA DE AUTENTICACIÓN (Lógica) ==========
class SistemaAutenticacion:
    def __init__(self, archivo_usuarios="usuarios.json"):
        self.archivo_usuarios = archivo_usuarios
        self._cargar_usuarios()
    
    def _cargar_usuarios(self):
        if os.path.exists(self.archivo_usuarios):
            try:
                with open(self.archivo_usuarios, 'r') as f:
                    self.usuarios = json.load(f)
            except:
                self.usuarios = self._usuarios_por_defecto()
        else:
            self.usuarios = self._usuarios_por_defecto()
            self._guardar_usuarios()
    
    def _usuarios_por_defecto(self) -> Dict:
        return {
            "admin": {
                "contrasena_hash": self._hash_password("admin123"),
                "nombre": "Administrador Principal",
                "rol": "admin",
                "fecha_creacion": datetime.now().strftime("%Y-%m-%d"),
                "avatar": "👑"
            },
            "supervisor": {
                "contrasena_hash": self._hash_password("sup123"),
                "nombre": "Supervisor de Inventario",
                "rol": "supervisor",
                "fecha_creacion": datetime.now().strftime("%Y-%m-%d"),
                "avatar": "👨‍💼"
            },
            "milagros": {
                "contrasena_hash": self._hash_password("mila123"),
                "nombre": "Milagros",
                "rol": "supervisor",
                "fecha_creacion": datetime.now().strftime("%Y-%m-%d"),
                "avatar": "👩‍💼"
            }
        }
    
    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _guardar_usuarios(self):
        with open(self.archivo_usuarios, 'w') as f:
            json.dump(self.usuarios, f, indent=4)
    
    def autenticar(self, usuario: str, contrasena: str) -> bool:
        if usuario in self.usuarios:
            contrasena_hash = self._hash_password(contrasena)
            if self.usuarios[usuario]["contrasena_hash"] == contrasena_hash:
                return True
        return False
    
    def obtener_datos_usuario(self, usuario: str) -> Dict:
        return self.usuarios.get(usuario, {})
    
    def actualizar_ultimo_acceso(self, usuario: str):
        if usuario in self.usuarios:
            self.usuarios[usuario]["fecha_ultimo_acceso"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._guardar_usuarios()

@st.cache_resource
def get_auth_system():
    return SistemaAutenticacion()

auth = get_auth_system()

# ========== PANTALLA DE LOGIN (ARREGLADA) ==========
def mostrar_login():
    # Columnas para centrar
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # HEADER BLANCO (Título en Negro forzado por CSS)
        st.markdown("""
            <div class="login-header">
                <div style="font-size: 50px; margin-bottom: 10px;">💻</div>
                <h1 style="color: black; margin: 0; font-size: 28px;">TechInventory Pro</h1>
                <p style="color: #666; margin-top: 5px;">Sistema de Gestión TI</p>
            </div>
        """, unsafe_allow_html=True)
        
        # FORMULARIO BLANCO (Inputs en Negro forzado por CSS)
        with st.form("login_form"):
            st.write(" ") # Espaciador
            usuario = st.text_input("Usuario", placeholder="Ingresa tu usuario")
            contrasena = st.text_input("Contraseña", type="password", placeholder="••••••••")
            
            st.markdown("###") # Espaciador
            
            submitted = st.form_submit_button("🚀 INICIAR SESIÓN", type="primary", use_container_width=True)

        # Botón demo
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 ACCESO RÁPIDO (DEMO)", type="secondary", use_container_width=True):
            usuario = "supervisor"
            contrasena = "sup123"
            submitted = True # Simular submit

        if submitted:
            if auth.autenticar(usuario, contrasena):
                st.session_state["autenticado"] = True
                st.session_state["usuario"] = usuario
                st.session_state["datos_usuario"] = auth.obtener_datos_usuario(usuario)
                auth.actualizar_ultimo_acceso(usuario)
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas")

# ========== CONTROL DE SESIÓN ==========
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    mostrar_login()
    st.stop() # DETIENE TODO LO DEMÁS SI NO HAY LOGIN

# ==============================================================================
# 3. APLICACIÓN PRINCIPAL (SOLO CARGA SI HAY LOGIN)
# ==============================================================================

# Header Principal
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white !important; /* Aquí forzamos blanco porque el fondo es oscuro */
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .main-header h1, .main-header p {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_sistema():
    return SistemaInventario()

app = get_sistema()

usuario_actual = st.session_state["usuario"]
datos_usuario = st.session_state["datos_usuario"]
nombre_usuario = datos_usuario.get("nombre", usuario_actual)
rol_usuario = datos_usuario.get("rol", "usuario")

# Sidebar
with st.sidebar:
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem; background: rgba(255,255,255,0.1); border-radius: 10px; margin-bottom: 1rem;">
        <div style="font-size: 3rem;">{datos_usuario.get('avatar', '👤')}</div>
        <h3 style="color: white; margin: 5px 0;">{nombre_usuario}</h3>
        <span style="background: #667eea; color: white; padding: 2px 10px; border-radius: 10px; font-size: 0.8rem;">
            {rol_usuario.upper()}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state["autenticado"] = False
        st.rerun()
    
    st.divider()
    
    menu_opciones = [
        ("🏠 Dashboard", "dashboard"),
        ("📦 Inventario", "inventario"),
        ("🔄 Movimientos", "movimientos"),
        ("➕ Nuevo Producto", "nuevo"),
        ("🧠 Análisis Avanzado", "analisis"),
        ("📋 Historial", "historial"),
    ]
    
    if rol_usuario == "admin":
        menu_opciones.append(("⚙️ Configuración", "config"))
        menu_opciones.append(("👥 Usuarios", "usuarios"))
    
    selected = st.selectbox("Navegación", [op[0] for op in menu_opciones])
    menu = dict(menu_opciones)[selected]

# Contenido Principal
st.markdown(f"""
<div class="main-header">
    <h1 style="margin:0">TechInventory Pro</h1>
    <p style="margin:0; opacity:0.8">Panel: {selected} | Usuario: {usuario_actual}</p>
</div>
""", unsafe_allow_html=True)

if menu == "dashboard":
    col1, col2, col3, col4 = st.columns(4)
    try:
        kpis = app.obtener_kpis()
        # Metric cards tienen fondo de color, así que usamos texto blanco
        st.markdown("""
        <style>
            .metric-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white !important;
                padding: 1.5rem;
                border-radius: 15px;
                text-align: center;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }
            .metric-card h2, .metric-card h3, .metric-card p { color: white !important; }
        </style>
        """, unsafe_allow_html=True)
        
        with col1:
            st.markdown(f"""<div class="metric-card"><h2>💰</h2><h3>S/. {kpis.get('total_valor', 0):,.2f}</h3><p>Valor Inventario</p></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="metric-card"><h2>📦</h2><h3>{kpis.get('total_items', 0)}</h3><p>Productos Totales</p></div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class="metric-card"><h2>⚠️</h2><h3>{kpis.get('alertas', 0)}</h3><p>Stock Crítico</p></div>""", unsafe_allow_html=True)
        with col4:
            st.markdown(f"""<div class="metric-card"><h2>🏷️</h2><h3>{len(app.df)}</h3><p>Referencias</p></div>""", unsafe_allow_html=True)
            
        st.divider()
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="card"><h3>📊 Stock por Categoría</h3></div>', unsafe_allow_html=True)
            df = app.df
            if not df.empty:
                fig = px.bar(df, x='categoria', y='stock', color='categoria')
                st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown('<div class="card"><h3>💰 Valor por Marca</h3></div>', unsafe_allow_html=True)
            if not df.empty:
                df['total_val'] = df['precio_compra'] * df['stock']
                fig2 = px.pie(df, values='total_val', names='marca')
                st.plotly_chart(fig2, use_container_width=True)
                
    except Exception as e:
        st.error(f"Error cargando dashboard: {e}")

elif menu == "inventario":
    st.markdown('<div class="card"><h3>📦 Inventario General</h3></div>', unsafe_allow_html=True)
    busqueda = st.text_input("🔍 Buscar...", placeholder="Nombre, SKU, Marca...")
    df = app.buscar_funcional(busqueda)
    st.dataframe(df, use_container_width=True, height=500)
    
    if st.button("📥 Descargar CSV", use_container_width=True):
        df.to_csv("inventario.csv")
        st.success("Archivo guardado localmente (en servidor)")

elif menu == "nuevo":
    st.markdown('<div class="card"><h3>➕ Registrar Nuevo Producto</h3></div>', unsafe_allow_html=True)
    with st.form("nuevo_prod"):
        c1, c2 = st.columns(2)
        with c1:
            sku = st.text_input("SKU *")
            nombre = st.text_input("Nombre *")
            cat = st.selectbox("Categoría", ["Procesadores", "RAM", "Discos", "Video", "Fuentes", "Otros"])
        with c2:
            marca = st.text_input("Marca")
            p_compra = st.number_input("Precio Compra", 0.0)
            p_venta = st.number_input("Precio Venta", 0.0)
            stock = st.number_input("Stock Inicial", 0, step=1)
            
        if st.form_submit_button("Guardar Producto", type="primary"):
            if sku and nombre:
                ok, msg = app.registrar_producto(sku, nombre, cat, marca, p_compra, p_venta, stock)
                if ok: st.success(msg)
                else: st.error(msg)
            else:
                st.warning("SKU y Nombre son obligatorios")

elif menu == "movimientos":
    st.markdown('<div class="card"><h3>🔄 Registrar Movimiento</h3></div>', unsafe_allow_html=True)
    with st.form("mov"):
        sku = st.text_input("SKU Producto")
        tipo = st.selectbox("Tipo", ["Entrada", "Salida"])
        cant = st.number_input("Cantidad", 1, step=1)
        motivo = st.text_input("Motivo")
        
        if st.form_submit_button("Registrar", type="primary"):
            ok, msg = app.registrar_movimiento(sku, cant, tipo, motivo)
            if ok: st.success(msg)
            else: st.error(msg)
            
    st.divider()
    st.subheader("Historial Reciente")
    st.dataframe(pd.DataFrame(app.obtener_historial_movimientos()), use_container_width=True)

elif menu == "analisis":
    st.markdown('<div class="card"><h3>🧠 Análisis Avanzado</h3></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["NumPy Analytics", "Reportes"])
    
    with tab1:
        if st.button("Ejecutar Análisis de Precios"):
            res = app.analizar_precios_numpy()
            st.json(res)
            
    with tab2:
        if st.button("Ver Outliers"):
            out = app.identificar_outliers_numpy()
            if out: st.dataframe(out)
            else: st.info("No se detectaron outliers")

elif menu == "historial":
    st.markdown('<div class="card"><h3>📋 Bitácora del Sistema</h3></div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(app.obtener_historial_completo()), use_container_width=True)

elif menu == "usuarios" and rol_usuario == "admin":
    st.markdown('<div class="card"><h3>👥 Gestión de Usuarios</h3></div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(auth.usuarios.values()), use_container_width=True)

# Footer
st.markdown("---")
st.markdown("<div style='text-align:center; color:#333'>TechInventory Pro v3.0 | 2025</div>", unsafe_allow_html=True)