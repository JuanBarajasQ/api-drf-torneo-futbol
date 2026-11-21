# Plantilla: API con Django REST Framework

Proyecto base para la actividad de API desplegada de Programación Web. Trae resuelta la configuración del entorno y del despliegue; la API la construyes tú.

## Qué trae

- Django 6.1.2 con Django REST Framework, django-filter y drf-spectacular ya instalados y registrados.
- `config/settings.py` preparado para correr igual en tu Codespace y en Render: lee la clave secreta, el modo de depuración y la base de datos de variables de entorno.
- Swagger listo en `/api/docs/` y el esquema OpenAPI en `/api/schema/`.
- Configuración de GitHub Codespaces (`.devcontainer/`), para trabajar desde el navegador.
- Archivos de despliegue para Render: `build.sh`, `render.yaml` y `.python-version`.
- `herramientas/verificar.py`, que revisa tu API desplegada contra el contrato de la actividad.
- Las carpetas `evidencias/` y `colecciones/`, vacías, para tus entregables.

Lo que no trae: tu app, tus modelos, serializadores, vistas ni rutas.

## 1. Crea tu repositorio

1. En la página de esta plantilla, haz clic en **Use this template > Create a new repository**.
2. Créalo en la cuenta de uno de los integrantes, público, con un nombre como `api-grupo-4`.
3. En **Settings > Collaborators**, agrega a los otros dos integrantes. Cada uno acepta la invitación desde su correo o desde github.com.

## 2. Abre tu Codespace

1. En tu repositorio: **Code > Codespaces > Create codespace on main**.
2. Espera a que termine de instalar. La primera vez tarda unos minutos porque instala los paquetes y corre las migraciones.
3. En la terminal:

```bash
python manage.py runserver
```

4. Aparece un aviso para abrir el puerto 8000. Ábrelo. Prueba `/admin/` y `/api/docs/`. `/api/` responde 404 hasta que agregues tu router.

Cuando termines de trabajar, detén el Codespace en github.com/codespaces. La cuenta gratis trae 120 horas de cómputo al mes, y un Codespace de 2 núcleos gasta 2 por cada hora encendido.

## 3. Construye tu API

```bash
python manage.py startapp nombre_de_tu_app
```

- Agrega la app en `INSTALLED_APPS` de `config/settings.py`.
- Crea `nombre_de_tu_app/urls.py` con tu router e inclúyelo en `config/urls.py` con `path("api/", include("nombre_de_tu_app.urls"))`.
- Completa el diccionario `REST_FRAMEWORK` de `settings.py` con lo que pide el contrato, por ejemplo la paginación.
- Cambia `TITLE` en `SPECTACULAR_SETTINGS` por el nombre de tu proyecto.

Haz commits pequeños y frecuentes, y que cada integrante haga los suyos.

## 4. Despliega en Render

1. Crea una cuenta en render.com con tu usuario de GitHub.
2. En el panel: **New > Blueprint**, y elige tu repositorio. Render lee `render.yaml` y crea dos cosas, ambas en plan gratis: la base de datos Postgres y el servicio web.
3. Te pide tres valores para el usuario administrador: `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL` y `DJANGO_SUPERUSER_PASSWORD`. Escríbelos y guárdalos; con ellos entras a `/admin/`.
4. Espera a que el despliegue termine. Tu API queda en una URL como `https://api-drf-xxxx.onrender.com/api/`.

Cada `git push` a `main` vuelve a desplegar.

**Si prefieres hacerlo a mano**, sin Blueprint: crea primero una base **Postgres** gratis y luego un **Web Service** con estos datos:

| Campo | Valor |
|---|---|
| Build Command | `bash build.sh` |
| Start Command | `python -m gunicorn config.wsgi:application` |
| `DATABASE_URL` | la *Internal Database URL* de tu base |
| `SECRET_KEY` | un texto largo y aleatorio |
| `DJANGO_SUPERUSER_*` | los tres valores del administrador |

## 5. Verifica tu API

Desde tu Codespace:

```bash
python herramientas/verificar.py https://tu-api.onrender.com --repo .
```

El script lee el esquema de tu propia API, revisa el contrato mínimo y la carpeta de evidencias, y te dice qué falta. Córrelo cuantas veces quieras.

## Cosas que te pueden pasar

- **La primera petición tarda casi un minuto.** El plan gratis de Render apaga el servicio tras 15 minutos sin uso. Espera a que despierte y vuelve a intentar.
- **`DisallowedHost` o `Bad Request (400)` al abrir tu URL.** El dominio no está en `ALLOWED_HOSTS`. En Render se agrega solo con `RENDER_EXTERNAL_HOSTNAME`; si usas un dominio propio, agrégalo a mano.
- **`CSRF verification failed` al usar los formularios de la API navegable en el Codespace.** Abre la API desde la URL del puerto reenviado, la que termina en `app.github.dev`. `settings.py` ya la registra.
- **La API navegable se ve sin estilos en Render.** Revisa en el log del despliegue que `collectstatic` haya corrido.
- **La base de datos gratis de Render vence a los 30 días.** Alcanza para la actividad. Después de eso tus datos se pierden.
