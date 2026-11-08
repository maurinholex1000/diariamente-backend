# DIAriaMENTE -- Backend

API de **DIAriaMENTE**, desarrollada con FastAPI y PostgreSQL.

Este documento describe cómo preparar el entorno local, ejecutar la API,
conectarse a PostgreSQL, administrar migraciones, utilizar Docker y
consultar logs.

## Tecnologías

-   Python
-   FastAPI
-   SQLAlchemy
-   PostgreSQL
-   Alembic
-   Firebase Authentication
-   Firebase Cloud Messaging (FCM)
-   Docker

## Requisitos previos

-   Python instalado.
-   PostgreSQL instalado y en ejecución.
-   Git.
-   Docker Desktop, si se va a ejecutar el backend en contenedor.
-   Archivo de configuración `.env` local.
-   Credenciales de Firebase para el entorno de desarrollo.

> No publiques el archivo `.env`, `firebase-service-account.json` ni
> ninguna credencial privada.

## Ubicación del proyecto

En el entorno de desarrollo utilizado:

``` bash
cd ~/OneDrive/Desktop/DiariamenteBackend/diariamente-backend
```

Ajustá la ruta si clonaste el repositorio en otra ubicación.

## Preparar el entorno Python

Crear un entorno virtual (solo la primera vez):

``` bash
python -m venv venv
```

Activarlo en Git Bash:

``` bash
source venv/Scripts/activate
```

Instalar dependencias:

``` bash
pip install -r requirements.txt
```

Desactivar el entorno:

``` bash
deactivate
```

## Variables de entorno

La aplicación utiliza un archivo `.env` para la configuración local.
Debe contener las variables requeridas por la configuración del backend,
por ejemplo:

``` dotenv
DATABASE_URL=postgresql+psycopg://USUARIO:CONTRASEÑA@localhost:5433/diariamente_db
FIREBASE_CREDENTIALS=firebase-service-account.json
APP_NAME=DIAriaMENTE API
APP_VERSION=3.0.0
DEBUG=True
```

Completá los valores con las credenciales de tu entorno. No copies
contraseñas reales ni claves privadas a este README.

## Ejecutar la API

Con el entorno virtual activo:

``` bash
python run.py
```

Direcciones locales habituales:

-   API: http://localhost:8000
-   Swagger UI: http://localhost:8000/docs
-   OpenAPI: http://localhost:8000/openapi.json

Para detener el servidor, presioná `Ctrl+C`.

## PostgreSQL

En el entorno local utilizado, PostgreSQL está instalado directamente en
Windows y escucha en el puerto `5433`. La base de datos se llama
`diariamente_db`.

Conectarse desde Git Bash:

``` bash
psql -h localhost -p 5433 -U diariamente_user -d diariamente_db
```

PostgreSQL solicitará la contraseña del usuario configurado.

Salir de `psql`:

``` sql
\q
```

### Comandos útiles dentro de psql

Listar tablas:

``` sql
\dt
```

Ver la estructura de una tabla:

``` sql
\d users
```

Consultar usuarios:

``` sql
SELECT id, email, username, role, license_number
FROM users
ORDER BY id;
```

Comprobar si los usuarios tienen token FCM, sin mostrar el token:

``` sql
SELECT
    id,
    email,
    role,
    CASE
        WHEN fcm_token IS NOT NULL AND fcm_token <> ''
        THEN 'Sí'
        ELSE 'No'
    END AS tiene_token
FROM users
ORDER BY id;
```

Consultar solo un prefijo y la longitud del token para diagnóstico:

``` sql
SELECT
    email,
    role,
    LEFT(fcm_token, 20) AS inicio_token,
    LENGTH(fcm_token) AS longitud_token
FROM users
ORDER BY id;
```

> No compartas ni publiques el valor completo de ningún token FCM.

Comprobar la versión aplicada de Alembic:

``` sql
SELECT * FROM alembic_version;
```

### Diagnóstico de PostgreSQL desde Git Bash

Comprobar si hay un proceso escuchando en el puerto `5433`:

``` bash
netstat -ano | grep 5433
```

Localizar el cliente `psql`:

``` bash
where psql
```

## Alembic -- Migraciones

Ejecutar desde la carpeta raíz del backend, con el entorno virtual
activo.

Consultar la revisión actual:

``` bash
alembic current
```

Consultar el historial:

``` bash
alembic history
```

Generar una migración a partir de los modelos:

``` bash
alembic revision --autogenerate -m "descripcion del cambio"
```

Aplicar migraciones pendientes:

``` bash
alembic upgrade head
```

Retroceder una revisión:

``` bash
alembic downgrade -1
```

> Revisá el archivo de migración generado antes de aplicarlo. Confirmá
> que `DATABASE_URL` apunta a la base correcta y realizá un respaldo
> antes de cambios importantes.

## Docker

En el entorno utilizado, el contenedor del backend se llama
`diariamente-api`. PostgreSQL corre fuera de Docker, en Windows.

Listar contenedores activos:

``` bash
docker ps
```

Listar también contenedores detenidos:

``` bash
docker ps -a
```

Listar imágenes:

``` bash
docker images
```

Ver logs:

``` bash
docker logs diariamente-api
```

Seguir logs en tiempo real:

``` bash
docker logs -f diariamente-api
```

Ver logs de los últimos diez minutos y continuar en tiempo real:

``` bash
docker logs -f --since 10m diariamente-api
```

Detener el contenedor:

``` bash
docker stop diariamente-api
```

Iniciarlo:

``` bash
docker start diariamente-api
```

Reiniciarlo:

``` bash
docker restart diariamente-api
```

Eliminarlo (debe estar detenido):

``` bash
docker rm diariamente-api
```

Ver uso de recursos:

``` bash
docker stats
```

> Si se reconstruye o recrea el contenedor, verificá las variables de
> entorno, los montajes de archivos y la conectividad hacia PostgreSQL.
> No asumas que la base de datos está dentro del contenedor.

## Notificaciones FCM -- Diagnóstico

Endpoints relacionados con el flujo de notificaciones y consentimiento:

``` text
POST /notifications/register-token
POST /consent/request
```

Para observar los registros del contenedor:

``` bash
docker logs -f --since 10m diariamente-api
```

Interpretación de algunos resultados:

-   `NotRegistered`: el proveedor de mensajería indica que el token
    utilizado ya no está registrado.
-   `SERVICE_NOT_AVAILABLE`: el servicio no está disponible
    temporalmente.
-   `200 OK`: el endpoint HTTP respondió correctamente; no garantiza por
    sí solo que Firebase haya entregado la notificación al dispositivo.

Si una notificación no llega, comprobar: 1. Que el usuario destinatario
tenga un token registrado. 2. Que el token corresponda a una instalación
activa. 3. Que el endpoint que genera el evento invoque el servicio de
notificaciones. 4. Que el envío a Firebase no devuelva un error. 5. Que
el dispositivo tenga permisos y configuración de notificaciones
adecuados.

No imprimas ni compartas tokens FCM completos en logs o capturas.

## Comprobaciones de Python

Compilar los módulos para detectar errores de sintaxis:

``` bash
python -m compileall app
```

Ver dependencias instaladas:

``` bash
pip freeze
```

## Git -- Flujo habitual

Consultar el estado:

``` bash
git status
```

Revisar cambios:

``` bash
git diff
```

Agregar cambios:

``` bash
git add .
```

Crear un commit:

``` bash
git commit -m "Descripción del cambio"
```

Subir a `main`:

``` bash
git push origin main
```

Actualizar la copia local:

``` bash
git pull origin main
```

Consultar historial:

``` bash
git log --oneline -10
```

Ver ramas:

``` bash
git branch
```

Ver repositorios remotos:

``` bash
git remote -v
```

## Comandos generales de Git Bash

Mostrar la carpeta actual:

``` bash
pwd
```

Listar archivos:

``` bash
ls -la
```

Entrar en una carpeta:

``` bash
cd nombre_carpeta
```

Volver una carpeta:

``` bash
cd ..
```

Buscar texto en archivos:

``` bash
grep -Rni "texto" app/
```

Buscar una función con contexto:

``` bash
grep -n -A 30 -B 5 "nombre_funcion" app/archivo.py
```

Limpiar la terminal:

``` bash
clear
```

## Seguridad y buenas prácticas

1.  No subas `.env`, archivos de credenciales Firebase, claves privadas
    ni tokens.
2.  Verificá que `.gitignore` excluya archivos sensibles y entornos
    virtuales.
3.  No ejecutes migraciones sin revisar el cambio generado.
4.  Confirmá que la base de datos configurada sea la correcta antes de
    ejecutar consultas o migraciones.
5.  No compartas contraseñas ni valores completos de tokens en logs o
    capturas.
6.  Mantené commits descriptivos y sincronizá los cambios con GitHub.
7.  En desarrollo local, protegé el acceso a la API y a la base de
    datos.

## Repositorios

-   Backend: https://github.com/maurinholex1000/diariamente-backend
-   Frontend: https://github.com/maurinholex1000/diariamente-frontend
