# 23 — APIView vs ViewSet, y cómo funciona el Router (Módulo 62 de la plataforma)

Temas: la diferencia real entre `APIView` (control total, manual) y `ViewSet`
(automatizado), y cómo el `Router` de DRF traduce un `ViewSet` en un mapa de URLs sin
que tengas que escribirlas a mano. Este módulo formaliza una decisión que ya tomamos
al construir Hound Express sin explicarla del todo — aquí queda completa.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **API View** | Vista de DRF con un método por verbo HTTP, control total | [APIView: control total, a mano](#apiview-control-total-a-mano) |
| **Contenedor Docker** | Una imagen en ejecución | Ya cubierto en [docs/12](12-fundamentos-linux-docker-django.md#contenedor-vs-imagen-vs-dockerfile) |
| **CRUD** | Create, Read, Update, Delete | Ya cubierto en [docs/13](13-vistas-crud-y-consultas.md#crud) |
| **Endpoint** | URL específica de la API | Ya cubierto en [docs/22](22-rest-apis-fundamentos.md#endpoint-lo-que-ya-tenemos) |
| **Router** | Mapea las acciones de un ViewSet a URLs automáticamente | [Router: de dónde salen nuestras URLs](#router-de-dónde-salen-nuestras-urls) |
| **Serializador** | Valida y transforma datos de entrada/salida | Ya cubierto en [docs/13](13-vistas-crud-y-consultas.md) y en `serializers.py` |
| **ViewSet** | Enfoque automatizado, ideal para CRUD simple/prototipos | [ViewSet: lo que ya usamos](#viewset-lo-que-ya-usamos) |

---

## `APIView`: control total, a mano

Ya la vimos brevemente en [docs/22](22-rest-apis-fundamentos.md#apiview-la-pieza-de-la-que-en-realidad-heredan-nuestros-viewsets).
El ejemplo completo de este módulo, con `GET` y `POST` en la misma clase:

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class ExampleAPIView(APIView):
    def get(self, request, format=None):
        data = {"message": "Hello, World!"}
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        data = request.data
        return Response(data, status=status.HTTP_201_CREATED)
```

Con `APIView`, **tú** escribes cada método (`get`, `post`, `put`, `patch`, `delete`) y
**tú** decides exactamente qué hace cada uno — no hay ninguna operación "gratis". El
parámetro `format=None` es un detalle de DRF para negociación de contenido (permitir
que la misma vista responda `.json` o `.api` navegable, entre otros formatos).

## `ViewSet`: lo que ya usamos

Todo `shipments/views.py` de este proyecto está construido con `ModelViewSet` — la
versión más automatizada, que **no** define métodos por verbo HTTP, sino **acciones**:

```python
class GuiaViewSet(viewsets.ModelViewSet):
    queryset = Guia.objects.all()
    serializer_class = GuiaSerializer
```

Con solo esas dos líneas, ya tenemos las 6 acciones estándar resueltas: `list`,
`create`, `retrieve`, `update`, `partial_update`, `destroy` — cada una mapeada
internamente a su verbo HTTP correspondiente (`list`→`GET` a la lista,
`create`→`POST`, etc.), sin que hayamos escrito ni un `def get(...)`.

### Lo que costaría reescribir `GuiaViewSet` como `APIView`

Para ver exactamente cuánto nos ahorra `ModelViewSet`, así se vería el mismo CRUD de
`Guia` escrito a mano con `APIView` (necesitarías **dos** clases, porque `APIView` no
distingue automáticamente "toda la lista" de "un objeto específico" — eso también lo
resuelve `ViewSet` por ti):

```python
class GuiaListCreateAPIView(APIView):
    def get(self, request):
        guias = Guia.objects.all()
        serializer = GuiaSerializer(guias, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = GuiaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GuiaDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(Guia, pk=pk)   # ver docs/13

    def get(self, request, pk):
        guia = self.get_object(pk)
        return Response(GuiaSerializer(guia).data)

    def patch(self, request, pk):
        guia = self.get_object(pk)
        serializer = GuiaSerializer(guia, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        guia = self.get_object(pk)
        guia.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

Y encima necesitarías registrar **dos** rutas a mano en `urls.py` (una para
`/guias/` y otra para `/guias/<pk>/`). Todo eso es exactamente lo que
`GuiaViewSet(viewsets.ModelViewSet)` + el `Router` resuelven en 2 líneas.

### Entonces, ¿para qué existe `APIView` si `ViewSet` hace todo esto solo?

Porque no todo endpoint es CRUD sobre un modelo. Nuestro propio proyecto ya tiene un
ejemplo de "necesito algo que no es CRUD estándar": la acción `estatus_history` en
`GuiaViewSet` (ver [shipments/views.py](../shipments/views.py)), resuelta con
`@action` **dentro** del ViewSet en vez de crear una `APIView` aparte — DRF permite
mezclar ambos mundos así. Pero si un endpoint no tiene *nada* que ver con un modelo
específico (como el `HelloWorldAPIView` de [docs/22](22-rest-apis-fundamentos.md), o
un endpoint que solo hace un cálculo, llama a una API externa, o valida algo sin
guardar nada), `APIView` sola —sin `ViewSet` de por medio— es la opción más clara.

**Regla práctica del módulo**: `ViewSet` para CRUD simple/prototipos rápidos
(nuestro caso con `Guia`/`Estatus`/`Usuario`); `APIView` cuando necesitas
personalización total o estás conectando con algo externo que no encaja en el molde
CRUD.

## `Router`: de dónde salen nuestras URLs

Ya usamos esto sin explicarlo a fondo en [shipments/urls.py](../shipments/urls.py):

```python
from rest_framework.routers import DefaultRouter

from .views import EstatusViewSet, GuiaViewSet, UsuarioViewSet

router = DefaultRouter()
router.register('guias', GuiaViewSet, basename='guia')
router.register('estatus', EstatusViewSet, basename='estatus')
router.register('usuarios', UsuarioViewSet, basename='usuario')

urlpatterns = router.urls
```

`router.register('guias', GuiaViewSet, ...)` le dice al router: "por cada acción
estándar que tenga `GuiaViewSet`, genera la URL correspondiente bajo `guias/`". El
resultado, sin que hayamos escrito ni un `path()`:

| Acción del ViewSet | URL generada | Verbo HTTP |
|----------------------|-----------------|--------------|
| `list` | `guias/` | `GET` |
| `create` | `guias/` | `POST` |
| `retrieve` | `guias/{pk}/` | `GET` |
| `update` | `guias/{pk}/` | `PUT` |
| `partial_update` | `guias/{pk}/` | `PATCH` |
| `destroy` | `guias/{pk}/` | `DELETE` |
| `estatus_history` (nuestra `@action`) | `guias/{pk}/estatus_history/` | `GET` (definido con `methods=['get']` en el decorador) |

`DefaultRouter` (el que usamos) además genera automáticamente una vista raíz de la
API (`/api/`, listando todos los endpoints registrados) y soporta sufijos de formato
(`.json`). La alternativa más simple, `SimpleRouter`, hace lo mismo pero sin esa
vista raíz — casi siempre `DefaultRouter` es la opción cómoda mientras desarrollas.

**Ventaja concreta que ya vivimos**: cuando en su momento agregamos `EstatusViewSet`
y `UsuarioViewSet`, no tocamos ni una línea de `hound_express/urls.py` — solo
agregamos `router.register(...)` en `shipments/urls.py` y las URLs nuevas
aparecieron solas. Sin router, tendrías que mantener a mano cada `path()` sincronizado
con cada acción de cada ViewSet — exactamente el trabajo manual que evitamos.

## Práctica: los 6 métodos aplicados a un modelo real de este proyecto

La actividad del módulo pide implementar todos los métodos de un `ViewSet` "haciendo
cambios reales en un modelo que esté almacenado en la Base de Datos" — eso es
exactamente lo que `GuiaViewSet` ya hace sobre `Guia` (ver
[shipments/views.py](../shipments/views.py)), probado contra la base real a lo largo
de este proyecto. No hace falta un modelo de e-commerce aparte: el mismo patrón de
`ModelViewSet` aplica igual a cualquier modelo — aquí está cada una de las 6
acciones, con su verbo/URL real y un ejemplo ya verificado en este proyecto:

| Acción | Verbo + URL real | Ejemplo probado en este proyecto |
|--------|---------------------|--------------------------------------|
| `create` | `POST /api/guias/` | Crear la guía `HE0000001` (ver [DOCUMENTACION.md](../DOCUMENTACION.md#6-ejemplo-de-flujo-completo-paso-a-paso)) |
| `list` | `GET /api/guias/` | Listar todas las guías, paginado |
| `retrieve` | `GET /api/guias/{id}/` | Consultar la guía `1` |
| `update` | `PUT /api/guias/{id}/` | Reemplazar todos los campos editables de una guía |
| `partial_update` | `PATCH /api/guias/{id}/` | Actualizar solo `currentStatus` |
| `destroy` | `DELETE /api/guias/{id}/` | Eliminar una guía |

Las 6 quedan resueltas con las mismas 2 líneas de siempre:

```python
class GuiaViewSet(viewsets.ModelViewSet):
    queryset = Guia.objects.all()
    serializer_class = GuiaSerializer
```

Y si el ejercicio pidiera **personalizar** alguna acción en vez de dejarlas todas por
default (como se vio en el ejemplo de `destroy()` explorado en esta misma sesión,
que respondía un mensaje de confirmación en vez del `204` vacío), el patrón exacto
sería sobreescribir solo esa acción:

```python
def destroy(self, request, *args, **kwargs):
    instance = self.get_object()
    pk = instance.pk
    self.perform_destroy(instance)
    return Response({'detail': f'Guía {pk} eliminada correctamente.'})
```

dejando las otras 5 acciones intactas y automáticas — exactamente el balance entre
"automatizado" y "control puntual" que contrasta `ViewSet` con `APIView` en este
módulo.

---

## Autoevaluación (Módulo 62)

1. **¿Qué es Django REST Framework?**
   La librería sobre Django que agrega serialización, autenticación, permisos y
   vistas orientadas a API — lo que usa este proyecto entero.

2. **¿Qué son las API Views?**
   Vistas con un método por verbo HTTP (`get`, `post`, etc.), control total sobre la
   lógica — sin comportamiento CRUD heredado automáticamente. → [APIView: control total, a mano](#apiview-control-total-a-mano)

3. **¿Cómo se configuran las URLs para una API View?**
   A mano, con `path()` apuntando a `.as_view()` de la clase — a diferencia de un
   `ViewSet`, no hay router que las genere solas.

4. **¿Qué es un serializador?**
   Valida y transforma datos entre representación externa (JSON) y objetos Python —
   ya lo usamos en los 3 serializers de [shipments/serializers.py](../shipments/serializers.py).

5. **¿Qué son los ViewSets?**
   Enfoque automatizado: en vez de métodos por verbo, defines *acciones*
   (`list`, `create`, `retrieve`...) y DRF las conecta solo. → [ViewSet: lo que ya usamos](#viewset-lo-que-ya-usamos)

6. **¿Cómo se diferencian ViewSets de API Views?**
   ViewSet no requiere `get()`/`post()` manuales ni URLs manuales (usa un Router);
   APIView requiere ambos, a cambio de control total. → toda la sección de [comparación](#entonces-para-qué-existe-apiview-si-viewset-hace-todo-esto-solo)

7. **¿Cuándo conviene usar ViewSets sobre API Views?**
   CRUD simple sobre un modelo, o prototipos rápidos — exactamente el caso de
   `Guia`/`Estatus`/`Usuario` en este proyecto.

8. **¿Cómo se prueban las APIs en DRF?**
   Con el servidor local corriendo (`runserver` o `docker compose up`) y peticiones
   reales — `curl` o Postman, como ya hicimos en [docs/22](22-rest-apis-fundamentos.md#probar-la-api-con-postman).

9. **¿Qué ventajas da el Router con ViewSets?**
   Genera automáticamente todas las URLs de las acciones de un ViewSet — agregar un
   modelo nuevo es una línea (`router.register(...)`), sin tocar `path()` a mano. → [Router](#router-de-dónde-salen-nuestras-urls)

10. **¿Qué considerar al implementar APIs con DRF?**
    Estructura de la API (¿ViewSet o APIView según el caso?), validación con
    serializers, configuración correcta de URLs, y pruebas de cada verbo HTTP antes
    de darla por terminada.

## Ejemplo de uso en el mercado laboral

- **Backend para apps móviles**: DRF como capa de API para que una app iOS/Android
  consuma los mismos datos que un frontend web — exactamente el rol que cumpliría
  Hound Express si mañana hay una app de rastreo.
- **Prototipado rápido**: `ViewSet` + `Router` para levantar un CRUD completo en
  minutos durante la fase de validar una idea, antes de invertir en personalizarlo
  con `APIView` si hace falta.
