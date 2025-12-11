import json
import hashlib
from datetime import datetime

def crear_usuarios_iniciales():
    """Crea el archivo de usuarios inicial"""
    
    usuarios = {
        "admin": {
            "contrasena_hash": hashlib.sha256("admin123".encode()).hexdigest(),
            "nombre": "Administrador Principal",
            "rol": "admin",
            "avatar": "👑",
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d"),
            "fecha_ultimo_acceso": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "supervisor": {
            "contrasena_hash": hashlib.sha256("sup123".encode()).hexdigest(),
            "nombre": "Supervisor de Inventario TI",
            "rol": "supervisor",
            "avatar": "👨‍💼",
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d"),
            "fecha_ultimo_acceso": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "milagros": {
            "contrasena_hash": hashlib.sha256("mila123".encode()).hexdigest(),
            "nombre": "Milagros",
            "rol": "supervisor",
            "avatar": "👩‍💼",
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d"),
            "fecha_ultimo_acceso": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    
    with open("usuarios.json", "w") as f:
        json.dump(usuarios, f, indent=4)
    
    print("✅ Archivo de usuarios creado exitosamente!")
    print("\n🔑 Credenciales iniciales:")
    print("   👑 Administrador: usuario: admin | contraseña: admin123")
    print("   👨‍💼 Supervisor: usuario: supervisor | contraseña: sup123")
    print("   👩‍💼 Milagros: usuario: milagros | contraseña: mila123")
    print("   👩‍💼 Gabriel: usuario: gabo | contraseña: gabo123")

if __name__ == "__main__":
    crear_usuarios_iniciales()