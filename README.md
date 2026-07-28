# Hound Express — API de estatus de envíos

Proyecto backend construido con Django y Django REST Framework para el manejo de las
entidades de base de datos de Hound Express: guías (envíos), su historial de estatus
y los usuarios que los actualizan. Los datos se almacenan en la base de datos para que
la aplicación Front pueda consultarlos y presentar el detalle de cada envío.

## Requisitos

- Python 3.11+
- pip

## Instalación local

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser   # opcional, para entrar al admin
python manage.py runserver
```

La aplicación quedará disponible en `http://127.0.0.1:8000/`.

## Modelo de datos

- **Guia** (tabla `Guide`): representa un envío — número de rastreo, origen, destino
  y estatus actual.
- **Estatus** (tabla `StatusHistory`): representa un evento del historial de estatus
  de una guía (referenciada por `guideId`), quién lo actualizó y cuándo.
- **Usuario** (tabla `User`): representa a quien puede actualizar estatus — nombre,
  correo y contraseña (nunca se expone en la API).

Los nombres de campo siguen `camelCase` (no el `snake_case` habitual de Python) a
propósito, para coincidir con el modelo de datos que consume el Front.

## Endpoints de la API

| Método | Endpoint                              | Descripción                                     |
|--------|------------------------------------------|---------------------------------------------------|
| GET    | `/api/guias/`                            | Lista todas las guías                              |
| POST   | `/api/guias/`                            | Crea una guía nueva                                |
| GET    | `/api/guias/{id}/`                       | Detalle de una guía                                |
| PATCH  | `/api/guias/{id}/`                       | Actualiza datos de una guía                        |
| DELETE | `/api/guias/{id}/`                       | Elimina una guía                                   |
| GET    | `/api/guias/{id}/estatus_history/`       | Historial de estatus de esa guía                   |
| GET    | `/api/estatus/`                          | Lista todos los eventos de estatus                 |
| POST   | `/api/estatus/`                          | Crea un evento de estatus                          |
| GET    | `/api/estatus/?guideId={id}`             | Filtra eventos de estatus por guía                 |
| GET    | `/api/usuarios/`                         | Lista usuarios                                     |
| POST   | `/api/usuarios/`                         | Crea un usuario                                    |
| GET    | `/api/usuarios/{id}/`                    | Detalle de un usuario                              |
| PATCH  | `/api/usuarios/{id}/`                    | Actualiza un usuario                               |
| DELETE | `/api/usuarios/{id}/`                    | Elimina un usuario                                 |

También está disponible el panel de administración en `/admin/`.

### Ejemplo: crear una guía

```bash
curl -X POST http://127.0.0.1:8000/api/guias/ \
  -H "Content-Type: application/json" \
  -d '{
        "id": 1,
        "trackingNumber": "HE0000001",
        "origin": "CDMX",
        "destination": "GDL",
        "currentStatus": "created"
      }'
```

### Ejemplo: registrar un evento de estatus

```bash
curl -X POST http://127.0.0.1:8000/api/estatus/ \
  -H "Content-Type: application/json" \
  -d '{
        "id": 1,
        "guideId": 1,
        "status": "picked_up",
        "updatedBy": "operador1"
      }'
```

Nota: `id` es requerido al crear (`IntegerField` como llave primaria, no autoincremental
en estos modelos), a diferencia del `id` autogenerado habitual de Django.

## Estructura del proyecto

```
hound_express/    # Configuración del proyecto Django
shipments/        # App con modelos, serializers, vistas y URLs de la API
manage.py
requirements.txt
```
