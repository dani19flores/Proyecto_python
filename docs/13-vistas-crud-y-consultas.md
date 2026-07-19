# 13 — Vistas, CRUD y consultas (Módulo 52 de la plataforma)

Temas: CRUD, vistas genéricas basadas en clases (`ListView`, `RetrieveView`/`DetailView`,
`UpdateView`), `render`, `get_object_or_404`, `login_required`, Middleware y consultas
complejas con `Q`.

**Contexto importante para este módulo**: Django tiene dos "mundos" de vistas que
resuelven lo mismo de forma distinta:

1. **Vistas clásicas** (`django.views.generic`): devuelven **HTML**, combinando una
   plantilla (`.html`) con datos, pensadas para que las vea un navegador directamente.
2. **Vistas de API** (Django REST Framework, lo que usa este proyecto): devuelven
   **JSON**, pensadas para que las consuma otro programa (un frontend, una app móvil,
   otro backend).

Este módulo enseña la vía clásica (1). Nuestro proyecto Hound Express usa la vía de
API (2) porque el encargo es "backend puro sin frontend". A lo largo del documento
marco el equivalente de cada concepto en nuestro código real, para que veas que es
**la misma idea, aplicada distinto**.

## Glosario del módulo

| Término | Definición corta | Equivalente en este proyecto |
|---------|--------------------|----------------------------------|
| **CRUD** | Crear, Leer, Actualizar, Eliminar — las 4 operaciones básicas sobre datos | [CRUD](#crud) — lo implementa `ShipmentViewSet` |
| **`login_required`** | Decorador que exige sesión iniciada para ver una vista | [login_required](#login_required-y-autenticación-en-una-api) — equivalente DRF: `permission_classes` |
| **`get_object_or_404`** | Trae un objeto o corta con un 404 si no existe | [get_object_or_404](#get_object_or_404) |
| **`ListView`** | Vista genérica que muestra una lista de objetos | [ListView](#listview-listar-objetos) — equivalente: acción `list` de `ShipmentViewSet` |
| **Middleware** | Código que se ejecuta en cada request/response, antes/después de la vista | [Middleware](#middleware) — ya lo tenemos en `settings.py` |
| **`Q`** | Clase para armar filtros complejos con AND/OR | [Consultas complejas con Q](#consultas-complejas-con-q) |
| **`render`** | Combina una plantilla HTML + datos → `HttpResponse` | [render vs Response](#render-vs-response) |
| **`RetrieveView` / `DetailView`** | Vista genérica que muestra el detalle de un objeto | [DetailView](#retrieveview--detailview-detalle-de-un-objeto) — equivalente: acción `retrieve` de `ShipmentViewSet` |
| **`startapp`** | Comando que crea una app nueva dentro del proyecto | [startapp](#startapp) — así se creó `shipments` |
| **`UpdateView`** | Vista genérica que actualiza un objeto existente | [UpdateView](#updateview-actualizar-un-objeto) — equivalente: `PATCH`/`PUT` en `ShipmentViewSet` |

---

## CRUD

CRUD = **C**reate, **R**ead, **U**pdate, **D**elete. Es el patrón detrás de casi
cualquier pantalla de administración de datos: dar de alta, consultar, modificar,
borrar. En Hound Express, el CRUD de envíos **ya está completo**, pero implementado
con un solo `ViewSet` de DRF en vez de 4-5 vistas separadas (ver
[shipments/views.py](../shipments/views.py)):

| Operación CRUD | HTTP | Método que lo resuelve en `ShipmentViewSet` |
|-----------------|------|-------------------------------------------------|
| Create | `POST /api/shipments/` | `create()` (heredado de `ModelViewSet`) |
| Read (lista) | `GET /api/shipments/` | `list()` |
| Read (detalle) | `GET /api/shipments/{id}/` | `retrieve()` |
| Update | `PATCH`/`PUT /api/shipments/{id}/` | `update()` / `partial_update()` |
| Delete | `DELETE /api/shipments/{id}/` | `destroy()` |

Esto es justo la ventaja de heredar de `viewsets.ModelViewSet`: las 5 operaciones CRUD
vienen ya resueltas, y nosotros solo tuvimos que decirle *qué* modelo/serializer usar.
En la vía "clásica" (con HTML), estas mismas 5 operaciones se resuelven con vistas
genéricas separadas — que es justo lo que sigue.

## `ListView`: listar objetos

Vista genérica clásica que muestra una lista de objetos de un modelo, renderizando una
plantilla. Ejemplo (fuera de este proyecto, con HTML):

```python
from django.views.generic import ListView
from shipments.models import Shipment

class ShipmentListView(ListView):
    model = Shipment
    template_name = "shipments/shipment_list.html"
    context_object_name = "shipments"   # así se llama la variable en el template
    paginate_by = 20
```

Con solo esas 4 líneas, Django ya sabe: consultar `Shipment.objects.all()`, paginar de
20 en 20, y pasarle el resultado a la plantilla como `shipments`. **Es el mismo trabajo**
que hace la acción `list` de `ShipmentViewSet` en nuestro proyecto — la diferencia es
que ahí el resultado sale como JSON (vía `ShipmentSerializer`), no como HTML.

## `RetrieveView` / `DetailView`: detalle de un objeto

Django, en su librería estándar (`django.views.generic`), le llama `DetailView` a esto
(no existe una clase llamada literalmente `RetrieveView` ahí — si en el curso la
llaman `RetrieveView` probablemente sea por su equivalente en Django REST Framework,
`RetrieveAPIView`, que es exactamente el mismo concepto aplicado a una API). Ambas
resuelven lo mismo: mostrar **un solo** objeto, buscado por su `pk` (o `slug`).

```python
from django.views.generic import DetailView

class ShipmentDetailView(DetailView):
    model = Shipment
    template_name = "shipments/shipment_detail.html"
    context_object_name = "shipment"
```

En nuestro proyecto, el equivalente exacto es la acción `retrieve` de
`ShipmentViewSet`, que además devuelve el historial completo de estatus gracias a
`ShipmentDetailSerializer` (ver [serializers.py](../shipments/serializers.py)).

## `UpdateView`: actualizar un objeto

Vista genérica que muestra un formulario prellenado con los datos actuales de un
objeto y, al enviarlo, lo actualiza:

```python
from django.views.generic.edit import UpdateView
from shipments.models import Shipment

class ShipmentUpdateView(UpdateView):
    model = Shipment
    fields = ["recipient_name", "recipient_address", "weight_kg"]
    template_name = "shipments/shipment_form.html"
    success_url = "/shipments/"
```

Nota algo importante: aquí **sí** limitamos `fields` a lo que se puede editar desde
afuera — igual que en nuestro `ShipmentSerializer`, donde `read_only_fields` protege
`tracking_number`, `current_status`, etc. para que nadie los cambie a mano por la API
(el estatus solo cambia creando un `ShipmentStatusEvent`, como vimos en el módulo
anterior). Es la misma precaución, aplicada en dos capas distintas (formulario vs
serializer).

## `render` vs `Response`

`render()` es la función clásica de Django para vistas basadas en funciones:

```python
from django.shortcuts import render

def shipment_list(request):
    shipments = Shipment.objects.all()
    return render(request, "shipments/shipment_list.html", {"shipments": shipments})
```

Hace 3 cosas en una línea: toma la plantilla, le inyecta el contexto (el diccionario),
y arma un `HttpResponse` con el HTML resultante — evitándote escribir eso a mano.

En una API con DRF, no hay plantilla HTML que renderizar: en vez de `render()`,
usamos `Response()` (lo trae `rest_framework.response`), que arma directamente una
respuesta JSON. Aunque no lo escribimos explícitamente en `ShipmentViewSet` (lo hace
`ModelViewSet` por debajo), sí lo usamos explícitamente en la acción personalizada
`status_history`:

```python
from rest_framework.response import Response

@action(detail=True, methods=['get'])
def status_history(self, request, pk=None):
    ...
    return Response(serializer.data)   # el "render" del mundo API
```

## `get_object_or_404`

Atajo para el patrón "busca este objeto, y si no existe, corta con un 404" — sin tener
que escribir el `try/except` a mano:

```python
from django.shortcuts import get_object_or_404
from shipments.models import Shipment

def shipment_detail(request, pk):
    shipment = get_object_or_404(Shipment, pk=pk)
    # si no existe, esta línea nunca se alcanza: Django ya respondió 404
    return render(request, "shipments/shipment_detail.html", {"shipment": shipment})
```

Sin este atajo, tendrías que escribir:

```python
try:
    shipment = Shipment.objects.get(pk=pk)
except Shipment.DoesNotExist:
    raise Http404("Envío no encontrado")
```

**En nuestro proyecto no lo escribimos a mano, pero lo estamos usando igual**: por
dentro, `self.get_object()` de `ShipmentViewSet` (usado en `retrieve`, `update`,
`destroy`, y en nuestra acción `status_history`) hace exactamente este patrón —
`get_object_or_404` es, literalmente, la pieza que usan los generics de DRF para
resolver "tráeme este objeto o responde 404".

## `login_required` y autenticación en una API

`login_required` es un decorador para vistas clásicas basadas en función: si no hay
sesión iniciada, redirige al login en vez de ejecutar la vista.

```python
from django.contrib.auth.decorators import login_required

@login_required
def shipment_list(request):
    ...
```

(Para vistas basadas en clase, el equivalente es el mixin `LoginRequiredMixin`.)

**El problema**: eso funciona con sesiones de navegador (cookies), que es el modelo de
autenticación de las vistas clásicas. Una API pensada para que la consuman otros
programas normalmente no usa sesiones de navegador, así que DRF no reutiliza
`login_required` — usa su propio mecanismo: `permission_classes`.

```python
from rest_framework.permissions import IsAuthenticated

class ShipmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]   # equivalente API de login_required
    ...
```

Ahora mismo `ShipmentViewSet` **no** tiene esto — está abierto sin autenticación (por
eso pudimos probarlo con `curl` sin loguearnos). Es algo a considerar como mejora
futura si Hound Express va a exponer esta API a otros sistemas y no quieres que
cualquiera pueda crear/borrar envíos.

## Middleware

Un middleware es una capa de código que Django ejecuta **en cada** request y response,
antes de que llegue a tu vista y después de que tu vista responde — como una cadena de
filtros por la que pasa todo.

Ya tenemos una lista de ellos, activados por defecto, en
[hound_express/settings.py](../hound_express/settings.py):

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',      # cabeceras de seguridad HTTP
    'django.contrib.sessions.middleware.SessionMiddleware', # habilita request.session
    'django.middleware.common.CommonMiddleware',            # normaliza URLs, etc.
    'django.middleware.csrf.CsrfViewMiddleware',             # protección CSRF en forms
    'django.contrib.auth.middleware.AuthenticationMiddleware', # habilita request.user
    'django.contrib.messages.middleware.MessageMiddleware',     # framework de mensajes
    'django.middleware.clickjacking.XFrameOptionsMiddleware',    # anti-clickjacking
]
```

El orden importa: cada request pasa de arriba hacia abajo por esta lista antes de
llegar a la vista, y la respuesta la vuelve a atravesar de abajo hacia arriba. Un
middleware propio se vería así (por ejemplo, uno que mida cuánto tarda cada request):

```python
import time

class TiempoDeRespuestaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        inicio = time.time()
        response = self.get_response(request)   # aquí se ejecuta la vista
        duracion = time.time() - inicio
        response["X-Tiempo-Respuesta"] = f"{duracion:.3f}s"
        return response
```

(Se registraría agregando su ruta de import a la lista `MIDDLEWARE` de `settings.py`.)

## Consultas complejas con `Q`

`.filter(a=1, b=2)` siempre combina condiciones con **AND**. Para armar condiciones con
**OR**, o mezclar AND/OR entre sí, se usa la clase `Q`:

```python
from django.db.models import Q
from shipments.models import Shipment

# Envíos cuyo remitente O destinatario contenga "CDMX"
Shipment.objects.filter(
    Q(sender_address__icontains="CDMX") | Q(recipient_address__icontains="CDMX")
)

# Envíos entregados en CDMX, o cancelados en cualquier lado (AND + OR combinados)
Shipment.objects.filter(
    Q(current_status="delivered", recipient_address__icontains="CDMX")
    | Q(current_status="cancelled")
)
```

`|` es OR, `&` es AND (aunque para AND normalmente ya te basta con pasar varios
argumentos a `.filter()`), y `~Q(...)` es NOT. Es exactamente lo que necesitarías si,
por ejemplo, quisiéramos agregar un endpoint de "búsqueda" que revise varios campos de
texto a la vez en `ShipmentViewSet` — ahora mismo `get_queryset` en
`ShipmentStatusEventViewSet` filtra por un solo campo (`shipment`); con `Q` se podría
extender a buscar por varios criterios opcionales al mismo tiempo.

## `startapp`

Comando de `manage.py` que genera la estructura mínima de una app nueva dentro del
proyecto (una "app" en Django es un módulo con su propio conjunto de modelos, vistas,
migraciones, etc. — un proyecto puede tener varias).

```bash
python manage.py startapp shipments
```

Así se creó la carpeta [shipments/](../shipments/) de este proyecto: generó
`models.py`, `views.py`, `admin.py`, `apps.py`, `tests.py` y la carpeta `migrations/`
vacíos, listos para llenar. Después hay que registrar la app en `INSTALLED_APPS`
(en [hound_express/settings.py](../hound_express/settings.py)) para que Django la
reconozca — paso que hicimos al agregar `'shipments'` a esa lista.
