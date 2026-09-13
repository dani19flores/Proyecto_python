# 17 — Órdenes, facturación y señales (Módulo 56 de la plataforma)

Temas: el proyecto de ejemplo del módulo (apps `Order`, `Address`, `Billing`, `Carts`,
`Product`), consistencia de tipos de campo, `ForeignKey` en un caso real de e-commerce,
`pre_save`/`post_save` a fondo con `Order`, y métodos como `get_absolute_url`.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **BillingProfile** | Modelo de perfil de facturación (`user`, `email`) | [Las apps del módulo](#las-apps-del-módulo-order-address-billing-carts-product) |
| **Cart** | Modelo de carrito de compra, `ManyToMany` con productos | [Las apps del módulo](#las-apps-del-módulo-order-address-billing-carts-product) |
| **CharField** | Campo de texto de longitud fija | [Consistencia de tipos](#consistencia-de-tipos-y-longitudes) |
| **Docker** | Contenedores para el entorno de desarrollo | Ya cubierto en [docs/12](12-fundamentos-linux-docker-django.md) y [COMANDOS_DOCKER.md](../COMANDOS_DOCKER.md) |
| **ForeignKey** | Relación de clave foránea entre modelos | [ForeignKey en un caso real](#foreignkey-en-un-caso-real-order--billingprofile) |
| **get_absolute_url** | Método que devuelve la URL "canónica" de un objeto | [get_absolute_url](#get_absolute_url) |
| **Order** | Modelo de orden (`billing_profile`, `order_id`, `status`) | [pre_save y post_save con Order](#pre_save-y-post_save-a-fondo-con-order) |
| **post_save** | Señal disparada después de guardar | [pre_save y post_save con Order](#pre_save-y-post_save-a-fondo-con-order) |
| **pre_save** | Señal disparada antes de guardar | [pre_save y post_save con Order](#pre_save-y-post_save-a-fondo-con-order) |
| **Product** | Modelo de producto (`title`, `price`, `image`) | [Las apps del módulo](#las-apps-del-módulo-order-address-billing-carts-product) |

---

## Las apps del módulo: `Order`, `Address`, `Billing`, `Carts`, `Product`

Este módulo arma, paso a paso, el esqueleto de datos de una tienda en línea —el mismo
tipo de dominio que ya vimos parcialmente en el ejemplo de `ProductoListView` del
[Módulo 54](15-cbv-mixins-formularios.md). Cada pieza del negocio es **su propia app**
(recordando `startapp` de [docs/13](13-vistas-crud-y-consultas.md#startapp)), igual
que nuestro proyecto tiene `shipments` como su única app hasta ahora:

- **`Product`**: `title`, `price`, `image` — el catálogo.
- **`Address`**: `billing_profile`, `name`, `NIN` (o similar), con un campo tipo
  "elige una opción" (`billing`/`shipping`) usando el patrón de tuplas que ya vimos
  en [docs/14](14-modelos-y-migraciones.md#modeltextchoices) —hoy con `TextChoices`
  en vez de tuplas sueltas, que es la forma moderna de resolver lo mismo.
- **`BillingProfile`**: `user`, `email` — a quién se le factura.
- **`Cart`**: relación `ManyToMany` con `Product` (un carrito tiene muchos productos,
  y un producto puede estar en muchos carritos — a diferencia de `ForeignKey`, que es
  "muchos a uno"), más `subtotal`/`total`.
- **`Order`**: la orden final, con `billing_profile` (`ForeignKey`), `order_id` y
  `status`.

Es la misma filosofía de "una app por responsabilidad" que ya aplicamos: en Hound
Express, `shipments` concentra `Guia`/`Estatus`/`Usuario` porque es un dominio
pequeño; un proyecto más grande (como este ejemplo de e-commerce) separa cada
entidad de negocio en su propia app para poder evolucionarlas por separado.

## Consistencia de tipos y longitudes

El punto que remarca el módulo — mantener tipos y longitudes de campo consistentes —
ya lo aplicamos sin pensarlo dos veces en [shipments/models.py](../shipments/models.py):
`Guia.trackingNumber` es `CharField(max_length=15)` y en ningún otro lado del código
se trunca o compara ese valor con otra longitud distinta. La regla práctica: si un
mismo dato lógico (un ID externo, un código, un estatus) aparece en más de un modelo,
usa el mismo `max_length` en todos — evita bugs sutiles donde un valor cabe en una
tabla pero se trunca silenciosamente en otra.

## `ForeignKey` en un caso real: `Order` → `BillingProfile`

Ya explicamos `ForeignKey` a fondo en
[docs/14](14-modelos-y-migraciones.md#llaves-foráneas-foreignkey-para-seleccionar-modelos-relacionados)
con `ShipmentStatusEvent → Shipment`. Aquí el mismo patrón aplicado a facturación:

```python
class Order(models.Model):
    billing_profile = models.ForeignKey('BillingProfile', on_delete=models.CASCADE)
    order_id = models.CharField(max_length=120)
    status = models.CharField(max_length=120, default='created')
```

Nota la forma de referenciar el modelo: `'BillingProfile'` **como string**, no la
clase directamente. Django permite esto quiere para dos casos comunes: cuando el
modelo referenciado se define **después** en el mismo archivo (evita el problema de
"la clase todavía no existe" en tiempo de import), o cuando vive en otra app —
entonces el string es `'nombre_app.NombreModelo'`.

**Contraste con nuestro propio proyecto**: en `Estatus`, el campo `guideId` es un
`IntegerField()` simple, *no* un `ForeignKey` a `Guia` — fue una decisión explícita de
la consigna de esa entrega (replicar un esquema de base de datos tal cual, sin
relaciones a nivel Django). La diferencia práctica: con `ForeignKey` como aquí, Django
te da integridad referencial automática (`on_delete=CASCADE` borra en cascada,
`.billing_profile.email` navega la relación directo) — con un `IntegerField` suelto,
como en `Estatus.guideId`, esa navegación y esas garantías las tienes que manejar tú
a mano (como hicimos con el filtro manual `Estatus.objects.filter(guideId=guia.id)`
en [shipments/views.py](../shipments/views.py)).

## `pre_save` y `post_save` a fondo, con `Order`

Ya usamos `pre_save` en [docs/14](14-modelos-y-migraciones.md#señales-signals) para
generar un slug único, y mencionamos `post_save` como alternativa a sobreescribir
`.save()`. Este módulo trae el ejemplo "de libro" de `pre_save`: generar un
identificador legible a partir del `id` autogenerado.

```python
from django.db.models.signals import pre_save


class Order(models.Model):
    billing_profile = models.ForeignKey('BillingProfile', on_delete=models.CASCADE)
    order_id = models.CharField(max_length=120)
    status = models.CharField(max_length=120, default='created')

    def get_absolute_url(self):
        return f"/orders/{self.order_id}/"

    def get_status(self):
        return self.status


def pre_save_order_receiver(sender, instance, *args, **kwargs):
    if not instance.order_id:
        instance.order_id = 'ORD' + str(instance.id)


pre_save.connect(pre_save_order_receiver, sender=Order)
```

Un detalle sutil que vale la pena notar (y que no es obvio la primera vez que lo ves):
`pre_save` se dispara **antes** de que el registro se guarde, pero si es un objeto
**nuevo** (todavía sin `id`), `instance.id` en ese momento sigue siendo `None` en
bases de datos como PostgreSQL — este patrón de `'ORD' + str(instance.id)` solo
funciona de forma confiable en motores donde el `id` ya está disponible antes del
`INSERT` final, o si aceptas que el `order_id` se asigne en un **segundo** guardado
(el primer `save()` obtiene el `id`, y recién ahí puedes fijar `order_id` y guardar
de nuevo). Es el mismo tipo de sutileza que ya vimos con nuestro propio
`Shipment.save()` (en versiones anteriores de este proyecto): generar el
`tracking_number` con un `uuid` en vez de depender del `id` evita justo este problema,
porque no necesita esperar a que exista un `id`.

Comparando las dos formas que ya conocemos de resolver "calcula este campo solo":

| | Sobreescribir `save()` | Señal `pre_save`/`post_save` |
|---|---|---|
| Dónde vive la lógica | Dentro del propio modelo | Función aparte, conectada por fuera |
| Se ejecuta si usas `bulk_create` | No (ver [docs/14](14-modelos-y-migraciones.md#creación-a-granel-bulk)) | Tampoco — ninguna de las dos se dispara con `bulk_create` |
| Se puede desconectar/reemplazar sin tocar el modelo | No | Sí (`pre_save.disconnect(...)`) |
| Ejemplo ya usado en este proyecto | `AutoDateTimeField.pre_save()` en [models.py](../shipments/models.py) | El slug de [docs/14](14-modelos-y-migraciones.md#señales-signals) |

`post_save` (la otra señal del glosario) es idéntica en mecánica pero se dispara
**después** de guardar — típica para acciones que necesitan que el registro ya tenga
`id` garantizado, como mandar un correo de confirmación o crear un registro
relacionado (ej.: crear automáticamente un `BillingProfile` vacío cada vez que se crea
un `Order` sin uno). La señal `created` en sus argumentos (`def receiver(sender,
instance, created, **kwargs)`) te dice si fue un `INSERT` nuevo o solo una
actualización — útil para no repetir esa acción en cada edición del objeto.

## `get_absolute_url`

Método (por convención, no magia de Django) que regresa la URL donde se puede ver
*ese* objeto específico:

```python
def get_absolute_url(self):
    return f"/orders/{self.order_id}/"
```

Más robusto usando `reverse()` (para no hardcodear la ruta, y que se actualice sola
si cambias `urls.py`):

```python
from django.urls import reverse

def get_absolute_url(self):
    return reverse('order-detail', kwargs={'order_id': self.order_id})
```

¿Para qué lo usa Django automáticamente, sin que tú lo llames?
- El botón **"Ver en el sitio"** del admin, en la página de detalle de un objeto.
- El `success_url` por defecto de `CreateView`/`UpdateView` (ver
  [docs/15](15-cbv-mixins-formularios.md#personalizar-get_queryset-y-get_success_url)):
  si no defines `get_success_url()`, Django intenta usar `get_absolute_url()` del
  objeto recién guardado.

**En nuestro proyecto no lo necesitamos**: `get_absolute_url()` es un concepto de
sitios que sirven HTML (una URL que un navegador puede visitar y ver ese objeto). Una
API JSON como la nuestra no tiene "una página para ver el objeto" — el equivalente
más cercano es simplemente la URL del endpoint, que DRF ya arma solo
(`/api/guias/{id}/`), sin necesitar este método.

---

## Autoevaluación (Módulo 56)

1. **¿Cómo se inicia la creación de una app para gestionar órdenes?**
   Configurando el entorno (Docker) y usando `python manage.py startapp` para crear
   la app, luego definiendo el modelo `Order` con sus campos. → [docs/13 — startapp](13-vistas-crud-y-consultas.md#startapp)

2. **¿Qué modelos se definen en la app "Address"?**
   `Address`, con `billing_profile`, `name`, y un campo de tipo con opciones
   (`billing`/`shipping`) — el mismo patrón de `TextChoices` que usamos en
   [docs/14](14-modelos-y-migraciones.md#modeltextchoices).

3. **¿Qué apps se introducen para facturación y carritos?**
   `Billing` (modelo `BillingProfile`: `user`, `email`) y `Carts` (modelo `Cart`:
   `ManyToMany` con `Product`, `subtotal`, `total`). → [Las apps del módulo](#las-apps-del-módulo-order-address-billing-carts-product)

4. **¿Cómo se gestiona la información de productos?**
   Con la app `Product` y su modelo homónimo (`title`, `price`, `image`).

5. **¿Por qué importa la consistencia de tipos y longitudes?**
   Evita truncamientos silenciosos y errores de integración cuando el mismo dato
   lógico aparece en varios modelos con `max_length` distintos. → [Consistencia de tipos](#consistencia-de-tipos-y-longitudes)

6. **¿Qué métodos/propiedades adicionales se destacan?**
   `get_absolute_url`, `get_status`, `get_short_address` — métodos de conveniencia
   que envuelven lógica de representación directamente en el modelo. → [get_absolute_url](#get_absolute_url)

7. **¿Qué importancia tienen `pre_save` y `post_save`?**
   Permiten ejecutar código automáticamente antes/después de guardar, para
   validación, cálculo de campos derivados (como `order_id`), o acciones
   relacionadas — sin ensuciar el `.save()` del modelo. → [pre_save y post_save con Order](#pre_save-y-post_save-a-fondo-con-order)

## Ejemplo de uso en el mercado laboral

- **E-commerce**: exactamente el dominio de este módulo — `Order`, `Address`,
  `BillingProfile` — es el esqueleto mínimo de cualquier tienda en línea real.
- **Automatización administrativa**: señales `post_save` para actualizar inventario o
  enviar confirmaciones por correo son el patrón estándar para no mezclar esa lógica
  con las vistas que crean el pedido.
