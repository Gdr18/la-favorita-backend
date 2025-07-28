# 🍻 Back end de La Favorita Bar

API desarrollada con **Python + Flask + MongoDB** para gestionar productos y pedidos en línea del bar _La Favorita_.
Esta aplicación permite a usuarios con distintos roles consultar y modificar la base de datos de forma segura,
facilitando tanto la realización de pedidos por parte de los clientes como su gestión por parte del personal del bar,
entre otras funcionalidades.

---

## 🚀 Tecnologías utilizadas

- **Python**
- **Flask**
- **MongoDB (PyMongo)**
- **Pydantic** – Validación de datos
- **JWT (Flask-JWT-Extended)** – Autenticación basada en tokens
- **OAuth** – Autenticación de terceros (Google)
- **SendGrid** – Envío de correos electrónicos
- **pytest** – Testing automatizado
- **python-dotenv** – Variables de entorno

---

## ✨ Funcionalidades principales

- Registro e inicio de sesión con JWT y Google OAuth
- Gestión de productos, usuarios, pedidos y platos (crear, listar, editar, eliminar)
- Sistema de roles para restringir el acceso a ciertas acciones para garantizar la seguridad
- Envío de correos electrónicos (bienvenida y confirmación de usuario)

___

## ⚙️ Instalación local

1. Clona este repositorio:

```
git clone https://github.com/Gdr18/la_favorita_backend.git
cd la_favorita_backend
```

2. Crea y activa un entorno virtual:

```
python -m venv venv
venv\Scripts\activate
```

3. Instala las dependencias:

```
pip install -r requirements.txt
```

4. Crea un archivo `.env` en la raíz del proyecto con las siguientes variables de entorno:

```
MONGO_DB_URI = "mongodburi"
CONFIG = config.DevelopmentConfig
JWT_SECRET_KEY = "jwtsecretkey"
CLIENT_ID = "googleclientid"
CLIENT_SECRET = "googleclientsecret"
SECRET_KEY = "secretkey"
SENDGRID_API_KEY = "sendgridapikey"
DEFAULT_SENDER_EMAIL = "senderemail"
```

- `MONGO_DB_URI`: URI de conexión a la base de datos MongoDB.
- `CONFIG`: Configuración de la aplicación (desarrollo/producción).
- `JWT_SECRET_KEY`: Clave secreta para la autenticación JWT.
- `CLIENT_ID` y `CLIENT_SECRET`: Credenciales de OAuth para autenticación con Google.
- `SECRET_KEY`: Clave secreta para la aplicación Flask.
- `SENDGRID_API_KEY`: Clave API de SendGrid para el envío de correos electrónicos.
- `DEFAULT_SENDER_EMAIL`: Correo electrónico del remitente por defecto.

5. Ejecuta la aplicación:

```
python run.py
```

___

## 🧪 Tests

Este proyecto incluye pruebas automáticas con pytest, pytest-mock y pytest-cov.

Para ejecutarlas:

```
python -m pytest
```

En consola aparecerá el código que ha pasado y fallado las pruebas, junto con la cobertura de cada archivo.

---

## 📓 Documentación de la API

Puedes consultar y probar todos los endpoints desde la colección de Postman:

🔗 [Colección de Postman](https://www.postman.com/maintenance-participant-28116252/workspace/gdor-comparte/collection/26739293-51b9ab63-6047-487f-a538-17276126744f?action=share&creator=26739293)

Incluye:

- Endpoints protegidos y públicos
- Headers, query params y body requeridos
- Respuestas esperadas y posibles errores
- Documentación embebida en cada endpoint

> 💡 Asegúrate de iniciar sesión primero con una cuenta de prueba para obtener un `access_token` válido.

---

## 🧪 Cuentas de prueba

Puedes iniciar sesión con las siguientes credenciales para obtener tokens JWT válidos. Estos te permitirán acceder a los
endpoints según el rol asignado:

### 👩‍💻 Developer

- Email: `developer_user@outlook.com`
- Contraseña: `Developer_user123`

### 👑 Admin

- Email: `admin_user@outlook.com`
- Contraseña: `Admin_user123`

### 🧑‍🔧 Staff

- Email: `staff_user@outlook.com`
- Contraseña: `Staff_user123`

> Los tokens de acceso son temporales. Puedes obtener uno nuevo en cualquier momento repitiendo el login.

### 👤 Cliente

El rol `cliente` se asigna automáticamente a cualquier usuario que se registre a través del endpoint de
`/auth/register`. No necesitas permisos especiales para registrarte.

### 🧾 Equivalencia de roles (internos)

| Rol (nomenclatura) | Valor en base de datos |
|--------------------|------------------------|
| `customer`         | `3`                    |
| `staff`            | `2`                    |
| `admin`            | `1`                    |
| `developer`        | `0`                    |

---

## 🔐 Acceso a endpoints por rol

Cada endpoint protegido requiere un determinado nivel de rol (`developer`, `admin`, `staff`). Estos niveles
están definidos en la lógica del backend y limitan el acceso a funciones como:

La documentación en Postman especifica, donde corresponde, qué rol es necesario.

___

## 👩‍💻 Autor

Desarrollado por **Gádor García Martínez**  
[GitHub](https://github.com/Gdr18) · [LinkedIn](https://www.linkedin.com/in/g%C3%A1dor-garc%C3%ADa-mart%C3%ADnez-99a33717b/)  

