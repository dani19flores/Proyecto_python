# 18 — Migraciones avanzadas, OneToOneField y errores comunes (Módulo 57 de la plataforma)

"Aplicaciones y Modelos para un e-commerce — Parte 2": continúa el dominio de
[docs/17](17-ordenes-facturacion-y-senales.md) (`Order`, `BillingProfile`, `Product`)
pero centrado en los problemas del día a día — errores comunes de migraciones,
`on_delete` a fondo, `OneToOneField`, e imágenes con Pillow.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **Admin Interface** | Panel de administración de Django | Ya cubierto en [docs/14](14-modelos-y-migraciones.md#django-admin-refleja-tus-modelos-automáticamente) |
| **Cascade Delete** | Borrado en cascada de objetos relacionados | [on_delete a fondo](#on_delete-a-fondo-las-7-opciones) |
| **Docker** | Contenedores para el entorno de desarrollo | Ya cubierto en [docs/12](12-fundamentos-linux-docker-django.md) |
| **ForeignKey** | Relación de uno a muchos | Ya cubierto en [docs/14](14-modelos-y-migraciones.md#llaves-foráneas-foreignkey-para-seleccionar-modelos-relacionados) y [docs/17](17-ordenes-facturacion-y-senales.md#foreignkey-en-un-caso-real-order--billingprofile) |
| **Migraciones** | Archivos que sincronizan modelos ↔ base de datos | Ya cubierto en [docs/14](14-modelos-y-migraciones.md#141-cambios-en-los-modelos-y-qué-son-las-migraciones) — aquí, los errores comunes |
| **OneToOneField** | Relación de uno a uno | [OneToOneField](#onetoonefield-cuando-foreignkey-no-es-suficiente) |
| **Pillow** | Librería de procesamiento de imágenes que necesita `ImageField` | [Pillow y campos de imagen](#pillow-y-campos-de-imagen) |
| **QuerySet** | Consultas encadenables y perezosas | Ya cubierto en [docs/14](14-modelos-y-migraciones.md#querysets) |
| **Template** | Archivo de plantilla HTML | Ya cubierto en [docs/16](16-usuarios-personalizados-y-templates.md#meta-tags-y-el-template-base-layouthtml) |
| **on_delete** | Qué hacer con los relacionados cuando se borra el objeto referenciado | [on_delete a fondo](#on_delete-a-fondo-las-7-opciones) |

---

## `on_delete` a fondo: las 7 opciones

Ya usamos `on_delete=CASCADE` varias veces (`ShipmentStatusEvent.shipment`,
`Order.billing_profile`) sin detenernos a ver las otras opciones. Es un argumento
**obligatorio** en cualquier `ForeignKey`/`OneToOneField` — Django te obliga a decidir
explícitamente qué pasa con los objetos relacionados cuando el objeto al que apuntan
se borra:

| Opción | Qué hace | Cuándo usarla |
|--------|-----------|------------------|
| `CASCADE` | Borra también los objetos relacionados | El relacionado no tiene sentido sin el padre (un `ShipmentStatusEvent` sin `Shipment`) |
| `PROTECT` | Impide el borrado (lanza `ProtectedError`) | Cuando borrar "por accidente" sería grave (ej.: no dejar borrar un `Product` si tiene `Order`s históricas) |
| `RESTRICT` | Como `PROTECT`, pero permite el borrado si es parte de una cascada que ya iba a borrar el relacionado por otro lado | Casos avanzados de cascadas combinadas — poco común al inicio |
| `SET_NULL` | Pone el campo en `NULL` (requiere `null=True` en el campo) | El relacionado puede seguir existiendo "huérfano" (ej.: una orden cuyo repartidor asignado se borró, pero la orden sigue) |
| `SET_DEFAULT` | Pone el campo en su `default=` | Similar a `SET_NULL`, pero con un valor de reemplazo conocido en vez de vacío |
| `SET(valor)` | Pone el campo en un valor o resultado de función específico | Casos a medida, ej. reasignar a un "usuario eliminado" genérico |
| `DO_NOTHING` | No hace nada a nivel Django (puede romper en la base de datos si hay una constraint) | Casi nunca — normalmente indica que quieres manejarlo tú a mano en SQL |

**Por qué `CASCADE` fue la elección correcta en nuestro proyecto**: si tuviéramos
`Estatus.guideId` como un `ForeignKey` real a `Guia` (recordando que hoy es un
`IntegerField` suelto, ver [docs/17](17-ordenes-facturacion-y-senales.md#foreignkey-en-un-caso-real-order--billingprofile)),
`CASCADE` sería lo correcto: un evento de estatus **no tiene sentido** sin la guía a
la que pertenece, así que si se borra la guía, tiene lógica borrar también su
historial completo — el mismo razonamiento que ya aplicamos con
`ShipmentStatusEvent.shipment` en versiones anteriores del modelo.

## `OneToOneField`: cuando `ForeignKey` no es suficiente

`ForeignKey` es "muchos a uno" (muchos `ShipmentStatusEvent` pueden apuntar al mismo
`Shipment`). `OneToOneField` es la versión estricta: **como máximo un** objeto de cada
lado puede estar relacionado con el otro — a nivel base de datos, es un `ForeignKey`
con una restricción `UNIQUE` extra.

```python
from django.db import models
from django.contrib.auth.models import User


class BillingProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField()
```

Aquí, **cada usuario tiene un único perfil de facturación**, y cada perfil de
facturación pertenece a un único usuario — no tendría sentido que dos perfiles de
facturación compartieran el mismo `user`. Si en cambio hubieras usado `ForeignKey`,
Django no impediría que existieran 5 `BillingProfile` distintos apuntando al mismo
`user` — técnicamente válido para la base de datos, pero incorrecto para el negocio.

**Regla práctica para decidir entre los dos**: pregúntate "¿puede haber *varios* del
lado hijo apuntando al mismo padre?". Si sí → `ForeignKey`. Si la relación es
estrictamente 1:1 (una extensión de otro modelo, casi como "agregarle campos" a otro
sin tocar su tabla) → `OneToOneField`. El caso de uso más común de `OneToOneField` es
justo ese: extender el `User` de Django (que no puedes modificar directamente sin
convertirlo en un modelo personalizado, como vimos con `AbstractBaseUser` en
[docs/16](16-usuarios-personalizados-y-templates.md#usuario-personalizado-abstractbaseuser--usermanager))
agregándole un "perfil" aparte con campos extra.

## Pillow y campos de imagen

`Pillow` es una librería de procesamiento de imágenes en Python (fork mantenido de la
antigua `PIL`). Django la necesita **por debajo** para poder usar `models.ImageField`
— sin `Pillow` instalado, cualquier modelo con `ImageField` falla el `system check`
con un error explícito pidiéndola.

```bash
pip install Pillow
```

```python
class Product(models.Model):
    title = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
```

`upload_to='products/'` define la subcarpeta (dentro de `MEDIA_ROOT`) donde se
guardan los archivos subidos. `ImageField` además valida que el archivo subido sea
realmente una imagen válida (a diferencia de `FileField`, que acepta cualquier
archivo) — justo esa validación es la que usa `Pillow` por debajo.

**En Hound Express no usamos `Pillow` hoy** (ningún modelo tiene `ImageField` — ni
está en `requirements.txt`), pero es la pieza que faltaría si, por ejemplo, quisieras
agregarle una foto de evidencia de entrega a un `Estatus`.

## Errores comunes al trabajar con migraciones

Este módulo dedica bastante tiempo a "cosas que truenan" al ir armando el proyecto —
vale la pena tenerlas identificadas de antemano:

- **Rutas de import que cambian entre versiones de Django**: por ejemplo,
  `django.core.urlresolvers` (viejo) vs `django.urls` (moderno). Si copias código de
  un tutorial antiguo, un `ImportError` casi siempre significa que la ruta cambió de
  versión — vale más buscar la ruta actual en la documentación que forzar la vieja.
- **Errores tipográficos en los modelos**: un campo mal escrito no siempre truena de
  inmediato — a veces solo lo notas hasta que intentas usarlo (`AttributeError`) o al
  correr `makemigrations` y ver un campo que no esperabas en el diff.
- **Orden de los campos y migraciones que dependen de otro modelo**: si `Order`
  referencia `BillingProfile` con `ForeignKey`, y ambos son nuevos, Django necesita
  poder resolver esa dependencia — normalmente lo hace solo, pero si defines el
  `ForeignKey` apuntando a un modelo que **todavía no existe en absoluto** (ni como
  string), truena. La solución casi siempre es la referencia por string que ya vimos
  en [docs/17](17-ordenes-facturacion-y-senales.md#foreignkey-en-un-caso-real-order--billingprofile).
- **Revertir y reaplicar migraciones**: si una migración quedó mal, puedes regresar a
  un estado anterior indicando el nombre de la migración a la que quieres volver:

  ```bash
  python manage.py migrate shipments 0001   # regresa hasta esa migración
  # corriges el modelo...
  python manage.py makemigrations shipments  # genera la migración corregida
  python manage.py migrate                    # la aplica
  ```

  (Ya usamos la versión "extrema" de esto en este proyecto: cuando cambiamos por
  completo `Shipment`/`ShipmentStatusEvent` por `Guia`/`Estatus`/`Usuario`, en vez de
  revertir optamos por borrar la migración y la base de datos de desarrollo y generar
  todo de cero — válido cuando, como en ese caso, los datos existentes eran solo de
  prueba y no había nada que preservar.)

## Registrar en el admin (recordatorio rápido)

El ejemplo del módulo es el registro más simple posible — el mismo patrón que ya
dejamos en [shipments/admin.py](../shipments/admin.py):

```python
from django.contrib import admin
from .models import Order

admin.site.register(Order)
```

Sin personalizar nada (sin `list_display`, sin `ModelAdmin`), Django ya te da una
interfaz funcional de listar/crear/editar/borrar — ver el detalle completo en
[docs/14](14-modelos-y-migraciones.md#django-admin-refleja-tus-modelos-automáticamente).

---

## Autoevaluación (Módulo 57)

1. **¿Cómo se manejan los errores comunes en Django?**
   Revisando rutas de import desactualizadas entre versiones, corrigiendo errores
   tipográficos en modelos, y definiendo `on_delete` explícitamente en toda relación
   `ForeignKey`/`OneToOneField`. → [Errores comunes al trabajar con migraciones](#errores-comunes-al-trabajar-con-migraciones)

2. **¿Por qué es importante registrar modelos en el Django Admin?**
   Sin registrarlos en `admin.py`, no aparecen en `/admin/` — el registro es lo que
   activa la interfaz de gestión automática para ese modelo.

3. **¿Qué problemas comunes hay con migraciones?**
   Orden/dependencias entre modelos relacionados, y la necesidad ocasional de
   revertir (`migrate app 000X`) y reaplicar tras corregir el modelo. → [Errores comunes](#errores-comunes-al-trabajar-con-migraciones)

4. **¿Cómo se crean datos de prueba en Django?**
   A mano desde el shell o el admin, o con fixtures (`loaddata`, ver
   [docs/14](14-modelos-y-migraciones.md#fixtures)) — usuarios, direcciones,
   perfiles de facturación y productos, para simular transacciones reales.

5. **¿Qué librería se destaca para manejo de imágenes?**
   Pillow — requerida por Django para que `ImageField` funcione. → [Pillow y campos de imagen](#pillow-y-campos-de-imagen)

## Ejemplo de uso en el mercado laboral

- **Gestión de inventario**: modelos de `Product`/`Order` con Django Admin son
  suficientes, en muchos negocios pequeños/medianos, para gestionar todo el
  inventario sin construir un panel a la medida.
- **Gestión de usuarios y roles**: `OneToOneField` extendiendo el `User` de Django
  (perfil con campos extra) es el patrón más común para agregar roles/permisos sin
  reescribir el sistema de autenticación desde cero.
