# Hound Express — API de estatus de envíos

Proyecto backend construido con Django y Django REST Framework para el manejo de eventos
que crean/actualizan el estatus de los envíos administrados por la paquetería Hound Express.
Los estatus se almacenan en la base de datos para referencia futura.

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

- **Shipment**: representa un envío (remitente, destinatario, peso, número de guía autogenerado
  y estatus actual).
- **ShipmentStatusEvent**: representa un evento del historial de estatus de un envío (creado,
  recolectado, en tránsito, en reparto, entregado, intento fallido, devuelto, cancelado). Cada
  evento nuevo actualiza automáticamente el `current_status` del envío al que pertenece.

## Endpoints de la API

| Método | Endpoint                              | Descripción                                   |
|--------|----------------------------------------|------------------------------------------------|
| GET    | `/api/shipments/`                      | Lista todos los envíos                         |
| POST   | `/api/shipments/`                      | Crea un nuevo envío                            |
| GET    | `/api/shipments/{id}/`                 | Detalle de un envío + su historial de estatus  |
| PATCH  | `/api/shipments/{id}/`                 | Actualiza datos del envío                      |
| DELETE | `/api/shipments/{id}/`                 | Elimina un envío                               |
| GET    | `/api/shipments/{id}/status_history/`  | Historial de estatus de un envío               |
| GET    | `/api/status-events/`                  | Lista todos los eventos de estatus             |
| POST   | `/api/status-events/`                  | Crea un evento de estatus (actualiza el envío) |
| GET    | `/api/status-events/?shipment={id}`    | Filtra eventos por envío                       |

También está disponible el panel de administración en `/admin/`.

### Ejemplo: crear un envío

```bash
curl -X POST http://127.0.0.1:8000/api/shipments/ \
  -H "Content-Type: application/json" \
  -d '{
        "sender_name": "Hound Express HQ",
        "sender_address": "CDMX",
        "recipient_name": "Juan Perez",
        "recipient_address": "GDL",
        "weight_kg": "2.50"
      }'
```

### Ejemplo: registrar un evento de estatus

```bash
curl -X POST http://127.0.0.1:8000/api/status-events/ \
  -H "Content-Type: application/json" \
  -d '{
        "shipment": 1,
        "status": "picked_up",
        "location": "CDMX Sucursal Centro",
        "notes": "Recolectado por el repartidor"
      }'
```

## Estructura del proyecto

```
hound_express/    # Configuración del proyecto Django
shipments/        # App con modelos, serializers, vistas y URLs de la API
manage.py
requirements.txt
```
