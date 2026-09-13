# 22 — Fundamentos de APIs REST (Módulo 61 de la plataforma)

Temas: qué es REST y sus 5 principios, JSON vs diccionarios de Python, `APIView` de
DRF (la pieza de la que en realidad heredan los `ViewSet` que ya usamos), y cómo
probar una API con Postman. Este módulo es la teoría que explica **por qué**
construimos Hound Express como lo hicimos desde el principio — vale la pena leerlo
aunque el proyecto ya esté funcionando.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **API** | Conjunto de definiciones/protocolos para que dos programas se comuniquen | [Qué es una API REST](#qué-es-una-api-rest) |
| **Cliente-Servidor** | El cliente pide, el servidor responde — arquitectura separada | [Los 5 principios de REST](#los-5-principios-de-rest) |
| **Docker** | Contenedores para el entorno de desarrollo | Ya cubierto en [docs/12](12-fundamentos-linux-docker-django.md) |
| **Endpoint** | Una URL específica de la API donde se hacen operaciones | [Endpoint: lo que ya tenemos](#endpoint-lo-que-ya-tenemos) |
| **JSON** | Formato de intercambio de datos, ligero y legible | [JSON vs diccionarios de Python](#json-vs-diccionarios-de-python) |
| **Postman** | Herramienta para probar APIs enviando peticiones HTTP | [Probar la API con Postman](#probar-la-api-con-postman) |
| **REST** | Estilo arquitectónico para diseñar servicios web | [Qué es una API REST](#qué-es-una-api-rest) |
| **RESTful** | Un servicio que cumple los principios de REST | [Los 5 principios de REST](#los-5-principios-de-rest) |
| **Serialización** | Convertir un objeto a un formato transmisible (JSON) y viceversa | Ya cubierto en [docs/13](13-vistas-crud-y-consultas.md) y `serializers.py` de este proyecto |
| **Stateless** | Cada petición debe traer toda la info necesaria, sin depender de estado guardado en el servidor | [Los 5 principios de REST](#los-5-principios-de-rest) |

---

## Qué es una API REST

Una **API** es, en general, cualquier forma en que dos programas se comunican
siguiendo reglas acordadas — no tiene que ser web (una librería también tiene una
"API": sus funciones públicas). **REST** es un estilo *específico* para APIs que
viven en la web, usando HTTP tal como ya lo hemos usado todo este tiempo: verbos
(`GET`/`POST`/`PATCH`/`DELETE`), URLs que identifican recursos, y JSON como formato
de intercambio. **RESTful** es el adjetivo — decimos que una API "es RESTful" cuando
cumple los principios de REST.

**Hound Express ya es una API RESTful**, sin que lo hayamos llamado así hasta ahora:
`/api/guias/` identifica el recurso "guías", y los verbos HTTP dicen qué operación
hacer sobre él — es literalmente la definición.

## Los 5 principios de REST

| Principio | Qué significa | Cómo lo cumple Hound Express |
|-----------|-----------------|----------------------------------|
| **Cliente-Servidor** | El cliente (frontend, Postman, `curl`) y el servidor (Django) están separados; cada uno evoluciona independiente | Nuestra API no sabe (ni le importa) qué la consume — podría ser un frontend web, una app móvil, o `curl` como hicimos en las pruebas |
| **Stateless** (sin estado) | Cada petición trae **todo** lo necesario para procesarla; el servidor no recuerda peticiones anteriores | Cada `POST /api/estatus/` incluye `guideId` explícito — el servidor no "recuerda" a qué guía te referías en la petición anterior |
| **Cacheable** | Las respuestas pueden marcarse como cacheables o no, para no repetir trabajo innecesario | No lo configuramos explícitamente hoy (sería vía cabeceras HTTP `Cache-Control`) — una mejora posible a futuro |
| **Sistema de capas** | El cliente no necesita saber si habla directo con el servidor o con algo en medio (balanceador, proxy, caché) | Al correr con Docker ([docs/12](12-fundamentos-linux-docker-django.md)), ya hay una capa (el contenedor) entre tu máquina y el proceso de Django, y el cliente ni se entera |
| **Interfaz uniforme** | Los recursos se identifican por URL, se manipulan con representaciones (JSON), y los mensajes son autodescriptivos | `/api/guias/{id}/` identifica **una** guía; el body JSON es su representación completa; el código de estado HTTP (200, 201, 404) autodescribe el resultado |

**Por qué "stateless" fue una decisión de diseño, no un accidente**: si nuestra API
dependiera de "recordar" en qué guía estabas trabajando entre una petición y otra
(como una sesión de navegador clásica), dejaría de ser RESTful — cualquier cliente
tendría que mantener esa sesión viva, complicando todo. Por eso cada petición a
`/api/estatus/` es autosuficiente: trae `guideId`, `status`, todo lo necesario, sin
depender de nada anterior.

## JSON vs diccionarios de Python

Se parecen mucho (por diseño — JSON nació inspirado en la sintaxis de objetos de
JavaScript, muy cercana a los diccionarios de Python), pero **no son lo mismo**:

| | JSON | Diccionario de Python |
|---|------|--------------------------|
| Comillas de claves/strings | Solo dobles: `"clave"` | Simples o dobles: `'clave'` o `"clave"` |
| Booleano | minúsculas: `true`, `false` | Capitalizado: `True`, `False` |
| Valor nulo | `null` | `None` |
| Comentarios | No se permiten | N/A (es código, no datos) |
| Tipo de dato en Python | Es texto (`str`) hasta que se parsea | Ya es un objeto Python nativo |

Django (con `json.loads`/`json.dumps`, o automáticamente vía DRF) es quien traduce
entre ambos mundos. Cuando probamos la API con `curl` y vimos respuestas como:

```json
{"id":1,"trackingNumber":"HE0000001","currentStatus":"created"}
```

eso es **texto JSON** — DRF lo generó a partir de un diccionario Python real
(`{'id': 1, 'trackingNumber': 'HE0000001', 'currentStatus': 'created'}`) al pasar por
el `GuiaSerializer`. Ese paso (objeto Python → texto JSON) es la **serialización**
que ya vimos como término en [docs/13](13-vistas-crud-y-consultas.md); el camino
inverso (JSON recibido → objeto Python) es la deserialización, y es lo que pasa
automáticamente cuando mandas un `POST` con body JSON y DRF lo convierte en
`validated_data` dentro del serializer.

## `APIView`: la pieza de la que en realidad heredan nuestros ViewSets

Ya usamos `viewsets.ModelViewSet` en todo el proyecto (ver
[shipments/views.py](../shipments/views.py)) sin ver la pieza de más abajo. La
cadena completa de herencia de DRF:

```
View (Django, ver docs/19)
  └── APIView (DRF — le agrega manejo de autenticación, permisos, parseo de JSON)
        └── GenericAPIView (le agrega queryset/serializer_class genéricos)
              └── ViewSet / ModelViewSet (le agrega list/create/retrieve/update/destroy)
```

`APIView` por sí sola, sin nada de lo genérico, se ve así — el ejemplo exacto del
módulo:

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class HelloWorldAPIView(APIView):
    def get(self, request):
        return Response({"message": "Hello, world!"}, status=status.HTTP_200_OK)
```

Es el mismo patrón de "un método por verbo HTTP" que ya vimos con `View` normal de
Django en [docs/19](19-ajax-charts-y-order-manager.md#la-cbv-base-view) — la
diferencia es que `APIView` ya sabe hablar JSON de forma nativa (negocia el formato
de respuesta, parsea el body de la petición, maneja autenticación/permisos de DRF)
sin que tengas que usar `JsonResponse` a mano.

**Cuándo usarías `APIView` en vez de `ModelViewSet`**: cuando el endpoint no
corresponde a operaciones CRUD normales sobre un modelo — por ejemplo, un endpoint de
"health check" (`GET /api/status/` que solo responde `{"status": "ok"}`), o un
cálculo que no mapea 1:1 a un modelo, similar a como usamos `View` (no `APIView`,
pero mismo razonamiento) para el dashboard de ventas en
[docs/19](19-ajax-charts-y-order-manager.md).

## `Endpoint`: lo que ya tenemos

Un endpoint es, literalmente, cada URL de la API sobre la que se puede operar. Ya
tenemos una tabla completa en el [README.md](../README.md#endpoints-de-la-api) —
por ejemplo, `GET /api/guias/{id}/` y `POST /api/estatus/` son dos endpoints
distintos, aunque ambos vivan dentro de la misma app `shipments`. Cada fila de esa
tabla es, en el vocabulario de este módulo, un endpoint.

## Probar la API con Postman

Ya probamos todo con `curl` a lo largo del proyecto — Postman hace lo mismo pero con
interfaz gráfica, guardando las peticiones para reusarlas:

1. Abre Postman, crea una petición nueva.
2. Método `POST`, URL `http://127.0.0.1:8000/api/guias/` (con el servidor corriendo,
   local o vía `docker compose up`).
3. Pestaña **Body** → `raw` → `JSON`, y pega:
   ```json
   {
     "id": 2,
     "trackingNumber": "HE0000002",
     "origin": "CDMX",
     "destination": "Puebla",
     "currentStatus": "created"
   }
   ```
4. **Send** — deberías ver `201 Created` y la guía de vuelta en la respuesta.
5. Guarda la petición en una **Collection** (una carpeta de peticiones relacionadas)
   para no reescribirla cada vez — típicamente se arma una colección completa con
   una petición por endpoint (crear guía, listar guías, crear estatus, etc.), que
   además sirve como documentación viva de la API para quien la vaya a consumir.

Ventaja sobre `curl` para este propósito: no tienes que reescribir el comando cada
vez, puedes guardar variables (como la URL base) para cambiar entre local/Docker sin
editar cada petición, y ver la respuesta formateada sin pelear con la terminal.

---

## Autoevaluación (Módulo 61)

1. **¿Qué es REST y por qué importa?**
   Un estilo arquitectónico para diseñar APIs web usando HTTP y JSON de forma
   estandarizada — hace que las APIs sean predecibles, escalables y fáciles de
   consumir por cualquier cliente. → [Qué es una API REST](#qué-es-una-api-rest)

2. **¿Cuáles son los principios fundamentales de REST?**
   Cliente-servidor, stateless, cacheable, sistema de capas, interfaz uniforme. → [Los 5 principios de REST](#los-5-principios-de-rest)

3. **¿Cómo se usa JSON en el contexto de REST?**
   Es el formato en el que viajan los datos entre cliente y servidor — el body de
   los `POST`/`PATCH` y el de las respuestas. → [JSON vs diccionarios de Python](#json-vs-diccionarios-de-python)

4. **¿Diferencias entre JSON y diccionarios de Python?**
   Comillas dobles obligatorias, `true`/`false`/`null` en minúsculas (vs
   `True`/`False`/`None`), y JSON siempre es texto hasta que se parsea. → [JSON vs diccionarios de Python](#json-vs-diccionarios-de-python)

5. **¿Cómo facilita Django la conversión JSON ↔ Python?**
   Con DRF y sus `Serializer`s (`GuiaSerializer`, etc.) — automatizan la
   serialización/deserialización sin que escribas `json.loads`/`dumps` a mano.

6. **¿Qué es Docker y cómo se usa con Django?**
   Empaqueta la app y sus dependencias en un contenedor reproducible. Ya cubierto a
   fondo en [docs/12](12-fundamentos-linux-docker-django.md) y
   [COMANDOS_DOCKER.md](../COMANDOS_DOCKER.md).

7. **¿Cómo se definen vistas con `APIView`?**
   Heredando de `rest_framework.views.APIView` y definiendo un método por verbo
   HTTP (`get`, `post`, etc.), regresando `Response(...)`. → [APIView](#apiview-la-pieza-de-la-que-en-realidad-heredan-nuestros-viewsets)

8. **¿Cómo se configuran URLs para distintos métodos HTTP?**
   En Django REST Framework, una misma URL (ej. `/api/guias/{id}/`) maneja varios
   verbos porque el `ViewSet`/`APIView` define un método por verbo — no necesitas
   una URL distinta por operación, a diferencia de vistas función por función.

9. **¿Qué es Postman y para qué sirve?**
   Herramienta para armar, guardar y enviar peticiones HTTP a una API, ver las
   respuestas, y organizarlas en colecciones reutilizables. → [Probar la API con Postman](#probar-la-api-con-postman)

## Ejemplo de uso en el mercado laboral

- **Microservicios**: REST es el lenguaje común entre servicios independientes —
  cada uno expone su propia API y no necesita saber cómo están construidos los demás,
  solo su contrato de endpoints.
- **Integración de sistemas**: empresas conectan su sistema interno con
  proveedores/clientes externos vía APIs REST — es, literalmente, lo que hace Hound
  Express al exponer `/api/guias/` para que un frontend externo consuma el estado de
  los envíos.
