# 24 — Paginación y seguridad en DRF (Módulo 63 de la plataforma)

Temas: los 3 tipos de paginación de Django REST Framework (`PageNumberPagination`,
`LimitOffsetPagination`, `CursorPagination`), cómo personalizarlas, y por qué la
configuración de `Renders` importa para la seguridad de una API en producción. Este
proyecto ya usa paginación desde el inicio — aquí queda explicada a fondo.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **CursorPagination** | Pagina con un cursor opaco en vez de números de página | [CursorPagination](#cursorpagination) |
| **JSON Render** | Renderer que solo muestra JSON plano, sin la interfaz navegable | [Renders y seguridad de API](#renders-y-seguridad-de-api) |
| **LimitOffsetPagination** | Pagina con `limit` (tamaño) y `offset` (cuántos saltar) | [LimitOffsetPagination](#limitoffsetpagination) |
| **max_page_size** | Tope máximo que un cliente puede pedir como tamaño de página | [Personalizar PageNumberPagination](#personalizar-pagenumberpagination) |
| **page_query_param** | Nombre del parámetro de query para el número de página | [Personalizar PageNumberPagination](#personalizar-pagenumberpagination) |
| **page_size** | Cuántos elementos por página, por default | [Lo que ya tenemos: PageNumberPagination](#lo-que-ya-tenemos-pagenumberpagination) |
| **page_size_query_param** | Nombre del parámetro que deja al cliente elegir el tamaño de página | [Personalizar PageNumberPagination](#personalizar-pagenumberpagination) |
| **PageNumberPagination** | Pagina con números de página (`?page=2`) | [Lo que ya tenemos: PageNumberPagination](#lo-que-ya-tenemos-pagenumberpagination) |
| **Renders** | Qué formato(s) puede devolver la API | [Renders y seguridad de API](#renders-y-seguridad-de-api) |
| **Seguridad de API** | Prácticas para proteger la API de accesos indebidos | [Renders y seguridad de API](#renders-y-seguridad-de-api) |

---

## Por qué pagina la API en primer lugar

Sin paginación, `GET /api/guias/` regresaría **todos** los registros de la tabla en
una sola respuesta — bien con 5 guías, un problema real con 500,000. Paginar reparte
esos resultados en bloques manejables, reduciendo lo que el servidor procesa/envía y
lo que el cliente tiene que recibir/parsear de una sola vez.

## Lo que ya tenemos: `PageNumberPagination`

Está configurado a nivel de proyecto en
[hound_express/settings.py](../hound_express/settings.py):

```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

Esto **ya está afectando** cada `GET /api/guias/` desde el día uno del proyecto —
por eso la respuesta de un `list` nunca es un arreglo plano, sino un objeto con
`count`/`next`/`previous`/`results` (lo vimos, sin explicarlo, cuando probamos la API
por primera vez):

```json
{
  "count": 25,
  "next": "http://127.0.0.1:8000/api/guias/?page=2",
  "previous": null,
  "results": [ /* hasta 20 guías */ ]
}
```

El cliente navega con `?page=2`, `?page=3`, etc. — el parámetro de página, por
default, se llama `page`.

## Personalizar `PageNumberPagination`

El ejemplo del módulo agrega control fino sobre el tamaño de página:

```python
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'links': {
               'next': self.get_next_link(),
               'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'results': data
        })
```

- **`page_size`**: el default si el cliente no especifica nada (reemplaza el
  `PAGE_SIZE` global solo para las vistas que usen esta clase).
- **`page_size_query_param`**: al ponerlo, el cliente puede pedir
  `?page_size=5` y anular el default — sin esto, `PAGE_SIZE` es fijo y el cliente no
  puede cambiarlo.
- **`max_page_size`**: el tope — aunque el cliente pida `?page_size=10000`, nunca
  regresa más de 100. **Esto es tanto una mejora de UX como una medida de
  seguridad/rendimiento**: sin un tope, cualquiera podría pedir toda la tabla de un
  golpe pasando un `page_size` enorme, anulando el propósito de paginar.
- **`page_query_param`**: (no usado en este ejemplo, pero existe) permite renombrar
  `?page=` a otra cosa, por si ese nombre choca con otro uso en tu API.
- **`get_paginated_response`**: sobreescrito aquí solo para anidar `next`/`previous`
  dentro de un objeto `links` — cosmético, la lógica de paginar no cambia.

Si quisiéramos esto en Hound Express, se vería así en
[shipments/views.py](../shipments/views.py) — dejando el resto del `ViewSet` igual:

```python
class GuiaViewSet(viewsets.ModelViewSet):
    queryset = Guia.objects.all()
    serializer_class = GuiaSerializer
    pagination_class = CustomPageNumberPagination   # anula el default global solo aquí
```

`pagination_class` a nivel de `ViewSet` **anula** el `DEFAULT_PAGINATION_CLASS`
global únicamente para ese ViewSet — útil si, por ejemplo, `Estatus` (que puede crecer
mucho más rápido que `Guia`) necesitara una página más chica que el resto de la API.

## `LimitOffsetPagination`

En vez de páginas numeradas, el cliente controla directamente cuántos registros
quiere (`limit`) y desde dónde empezar (`offset`):

```python
from rest_framework.pagination import LimitOffsetPagination

class EstatusLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 20
    max_limit = 100
```

```
GET /api/estatus/?limit=10&offset=20
```

Trae 10 resultados, empezando en el registro 21. Es más flexible que
`PageNumberPagination` para un cliente que quiere control preciso (por ejemplo,
"dame los siguientes 5, no los siguientes 20"), pero también más "manual" —
el cliente tiene que calcular el `offset` correcto, en vez de solo incrementar un
número de página.

## `CursorPagination`

En vez de un número (página u offset), usa un **cursor opaco** — un identificador
codificado que apunta a una posición exacta en un orden específico (normalmente por
fecha):

```python
from rest_framework.pagination import CursorPagination

class EstatusCursorPagination(CursorPagination):
    page_size = 20
    ordering = '-timestamp'   # obligatorio: sobre qué campo se ordena
```

```json
{
  "next": "http://.../api/estatus/?cursor=cD0yMDI2LTA3LTE5",
  "previous": null,
  "results": [ /* ... */ ]
}
```

**Por qué existe, si ya hay dos formas de paginar**: `PageNumberPagination` y
`LimitOffsetPagination` tienen un problema con datos que cambian constantemente —
si alguien está viendo la página 2 y mientras tanto se insertan 5 registros nuevos
arriba, "la página 2" ya no es lo que esperaba (algunos registros se repiten o se
saltan). `CursorPagination` no tiene ese problema porque el cursor apunta a una
posición relativa a un registro específico (por ejemplo, "todo lo que viene después
de este timestamp exacto"), no a un número fijo. Por eso el módulo lo recomienda para
"visualizar elementos nuevos" — un feed de eventos ordenados por fecha de creación
(como nuestro propio `Estatus`, ordenado por `-timestamp`) es el caso de uso de
libro de texto.

**Trade-off**: no puedes "saltar" a una página arbitraria (no existe "ir a la página
7") — solo avanzar/retroceder con `next`/`previous`. Para un catálogo de productos
donde el usuario quiere ver "página 5 de 20", `PageNumberPagination` sigue siendo
mejor; para un feed que crece constantemente, `CursorPagination` es más correcto.

## Renders y seguridad de API

Un **Renderer** en DRF decide en qué formato sale la respuesta. Por default, DRF trae
dos activados a la vez:

```python
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}
```

`BrowsableAPIRenderer` es la interfaz HTML navegable de DRF (la que verías si abres
`/api/guias/` directo en el navegador, con botones y formularios para probar la API a
mano) — muy cómoda en desarrollo, pero en producción expone estructura de la API
(qué campos existen, qué acciones acepta) a cualquiera que la visite desde un
navegador, sin necesidad de herramientas como Postman. La recomendación del módulo es
dejar **solo** `JSONRenderer` en producción:

```python
import os

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': (
        ['rest_framework.renderers.JSONRenderer']
        if not os.environ.get('DEBUG', 'true') == 'true'
        else ['rest_framework.renderers.JSONRenderer', 'rest_framework.renderers.BrowsableAPIRenderer']
    ),
}
```

Esto no es autenticación ni autorización — es "no le muestres a un explorador casual
más de lo necesario". Reducir superficie de exposición es una capa más de
**seguridad de API**, junto con (esto no lo cubre este módulo a fondo, pero ya lo
señalamos como pendiente en [docs/13](13-vistas-crud-y-consultas.md#login_required-y-autenticación-en-una-api)
y [docs/15](15-cbv-mixins-formularios.md#loginrequiredmixin)) agregar
`permission_classes` para exigir autenticación real — algo que **Hound Express
todavía no tiene** en ningún `ViewSet`. Paginar y limitar renders ayuda, pero no
reemplaza requerir autenticación si la API va a exponerse fuera de una red de
confianza.

---

## Autoevaluación (Módulo 63)

1. **¿Por qué es importante la paginación?**
   Evita procesar/enviar conjuntos de datos completos de golpe, mejorando tiempo de
   respuesta y uso de recursos tanto en servidor como cliente.

2. **¿Qué tipos de paginación ofrece DRF?**
   `PageNumberPagination`, `LimitOffsetPagination`, `CursorPagination` — cada uno
   personalizable. → todas las secciones de este documento

3. **¿Cómo se personaliza `PageNumberPagination`?**
   Con `page_size` (default), `page_size_query_param` (deja elegir al cliente),
   `max_page_size` (tope) y `page_query_param` (renombrar `?page=`). → [Personalizar PageNumberPagination](#personalizar-pagenumberpagination)

4. **¿Cuándo es útil `LimitOffsetPagination`?**
   Cuando el cliente necesita control granular exacto sobre cuántos registros trae y
   desde dónde, no solo "la siguiente página". → [LimitOffsetPagination](#limitoffsetpagination)

5. **¿Qué es `CursorPagination` y cuándo se recomienda?**
   Pagina con un cursor opaco atado a un orden específico — ideal para feeds que
   cambian constantemente (nuevos elementos insertados), evitando duplicados/saltos
   que sí sufren las otras dos. → [CursorPagination](#cursorpagination)

6. **¿Cómo mejora la seguridad la configuración de Renders?**
   Quitando `BrowsableAPIRenderer` en producción, para no exponer una interfaz
   navegable de la API a cualquiera con un navegador. → [Renders y seguridad de API](#renders-y-seguridad-de-api)

7. **¿Qué prácticas de seguridad se recomiendan para e-commerce?**
   `JSONRenderer` solo en producción, paginación con `max_page_size` para evitar
   pedir la tabla completa de un golpe, y autenticación/permisos reales en los
   endpoints sensibles.

8. **¿Cómo se configura la paginación en DRF?**
   Globalmente en `settings.py` (`DEFAULT_PAGINATION_CLASS`/`PAGE_SIZE`, como ya
   tenemos), o por `ViewSet` con el atributo `pagination_class`, que anula el
   default global solo ahí.

9. **¿Qué beneficios da la paginación a la experiencia de usuario?**
   Carga más rápida y navegación organizada, en vez de esperar a que baje todo el
   conjunto de datos de una vez.

10. **¿Cómo afecta la paginación al rendimiento del servidor?**
    Menos filas que consultar/serializar/enviar por petición — reduce carga de CPU,
    memoria y ancho de banda, especialmente notable con tablas grandes.

## Ejemplo de uso en el mercado laboral

- **E-commerce**: catálogos de productos paginados (`PageNumberPagination`) para no
  cargar miles de productos de golpe al abrir una categoría.
- **Redes sociales**: feeds (publicaciones, comentarios) casi siempre usan
  `CursorPagination` — nuevos posts se insertan constantemente arriba, y necesitas
  que "cargar más" no repita ni salte contenido.
