# 14 — Modelos y migraciones (Módulo 53 de la plataforma)

Temas: cambios en modelos y migraciones, Shell de Django, opciones robustas de campos,
modelos abstractos, creación a granel, SlugField, señales, fixtures y llaves foráneas.

Todos los ejemplos usan los modelos reales de este proyecto:
[shipments/models.py](../shipments/models.py).

## Glosario del módulo (con dónde verlo en este proyecto)

| Término | Definición corta | Dónde está en este documento / proyecto |
|---------|-------------------|-------------------------------------------|
| **Bulk Creation** | Insertar muchos registros en una sola operación, en vez de uno por uno, para mejorar el rendimiento | [14.3 — Creación a granel](#creación-a-granel-bulk) |
| **Fixtures** | Archivos (JSON) con datos predefinidos para cargar/descargar de la base de datos | [14.4 — Fixtures](#fixtures) |
| **Llaves Foráneas** | Campo que relaciona un modelo con otro | [14.4 — ForeignKey](#llaves-foráneas-foreignkey-para-seleccionar-modelos-relacionados), ya usado en `ShipmentStatusEvent.shipment` |
| **Model.TextChoices** | Clase para definir opciones (choices) de forma legible y sin duplicar código | [14.3 — Model.TextChoices](#modeltextchoices), ya usado en `ShipmentStatus` |
| **Modelos Abstractos** | Modelos que no generan tabla propia, solo comparten campos/métodos con sus hijos | [14.3 — Modelos abstractos](#modelos-abstractos) |
| **Querysets** | Conjuntos de consultas para recuperar/filtrar/manipular datos | [14.2 — Querysets](#querysets) |
| **Slug Fields** | Campos para URLs amigables y optimizadas para SEO, con unicidad garantizada | [14.4 — SlugField](#slugfield) |
| **Shell de Django** | Consola interactiva para crear objetos, hacer consultas y validar datos | [14.2 — Shell de Django](#142-shell-de-django-validar-y-probar-opciones-de-campos) |

---

## 14.1 Cambios en los modelos y qué son las migraciones

### La idea central

Django separa dos cosas que parecen la misma pero no lo son:

1. **Tus modelos** (`models.py`): código Python que describe cómo *quieres* que sea
   tu base de datos.
2. **La base de datos real**: las tablas que existen de verdad en `db.sqlite3` (o
   Postgres, MySQL, etc.).

Una **migración** es el "traductor" entre esas dos cosas: un archivo Python generado
por Django que dice, paso a paso, qué cambios hay que aplicarle a la base de datos
para que quede igual a lo que describen tus modelos en este momento.

Nunca editas la base de datos a mano. El flujo siempre es:

```
1. Edito models.py
2. python manage.py makemigrations   → Django compara models.py contra el
                                        estado anterior y genera un archivo
                                        de migración con las diferencias
3. python manage.py migrate          → Django ejecuta ese archivo y aplica
                                        los cambios reales a la base de datos
```

### Ejemplo real de este proyecto

Cuando corrí `makemigrations shipments` la primera vez (con `Shipment` y
`ShipmentStatusEvent` ya escritos en `models.py`), Django generó
[shipments/migrations/0001_initial.py](../shipments/migrations/0001_initial.py).
Ábrelo y vas a ver que es puro Python: una clase `Migration` con una lista de
`operations` (`CreateModel`, y si editaras un modelo existente verías `AddField`,
`AlterField`, `RemoveField`, etc.).

**Punto clave para principiantes**: el archivo de migración *no es* el modelo. Es la
"orden de trabajo" para llegar de un estado de la base de datos al siguiente. Por eso
las migraciones se numeran (`0001_initial`, `0002_...`) y cada una sabe de cuál
depende (`dependencies = [...]`) — es un historial, como los commits de git pero para
el esquema de tu base de datos.

### Comandos que vas a usar seguido

```bash
python manage.py makemigrations          # genera migraciones nuevas si hay cambios
python manage.py makemigrations shipments # solo para una app específica
python manage.py migrate                  # aplica todas las migraciones pendientes
python manage.py showmigrations           # muestra cuáles están aplicadas ([X]) y cuáles no ([ ])
python manage.py sqlmigrate shipments 0001 # te enseña el SQL real que ejecutaría esa migración
```

`sqlmigrate` es muy útil para *entender* qué está pasando de verdad, en vez de
confiar ciegamente en la magia de Django.

### ¿Qué pasa si me equivoco?

Si ya corriste `migrate` y te das cuenta de que el modelo estaba mal, casi siempre lo
más simple (en desarrollo, con datos que no importa perder) es:

1. Corregir el modelo.
2. `makemigrations` de nuevo (esto crea una migración *adicional* que corrige la
   anterior, Django no reescribe el archivo viejo).

Revertir una migración específica es posible (`migrate shipments 0001` te regresa a
ese punto), pero mientras aprendes, lo más importante es entender que **cada cambio
en `models.py` necesita su migración correspondiente** — si se te olvida correr
`makemigrations`, Django te va a avisar con una advertencia al iniciar el servidor.

### Optimización con migraciones: comprimirlas (`squashmigrations`)

En un proyecto que lleva mucho tiempo, terminas con decenas de archivos de migración
(`0001_initial`, `0002_...`, `0003_...`). Son útiles como historial, pero después de
un tiempo ya no importa el detalle de cada paso intermedio — solo el resultado final.
Django permite "comprimirlos" en uno solo:

```bash
python manage.py squashmigrations shipments 0001 0009
```

Esto genera **una** migración nueva que logra el mismo resultado final que las 9
originales combinadas. Es útil en proyectos colaborativos para simplificar el
historial y acelerar `migrate` en instalaciones nuevas (menos archivos que aplicar
uno por uno). No lo necesitamos todavía en Hound Express (solo tenemos `0001_initial`),
pero es bueno saber que existe para cuando el proyecto crezca.

---

## 14.2 Shell de Django: validar y probar opciones de campos

El shell es una consola interactiva de Python, pero con tu proyecto Django ya cargado
(los modelos, la configuración, todo). Sirve para probar cosas rápido sin tener que
pasar por la API o el admin.

```bash
python manage.py shell
# o, si tienes django-extensions instalado:
python manage.py shell_plus
```

### Ejemplos con los modelos de este proyecto

```python
from shipments.models import Shipment, ShipmentStatus

# Crear un objeto en memoria (todavía NO se guarda en la base de datos)
s = Shipment(
    sender_name="Hound Express HQ",
    sender_address="CDMX",
    recipient_name="Ana López",
    recipient_address="Monterrey",
    weight_kg="3.20",
)

# full_clean() corre las validaciones del modelo (choices, max_length, etc.)
# sin necesidad de guardarlo — ideal para "probar" opciones de campos
s.full_clean()

# Ahora sí, guardarlo de verdad
s.save()
print(s.tracking_number)   # se generó solo, gracias al save() personalizado
print(s.current_status)    # 'created', el default

# Consultar lo que ya existe
Shipment.objects.all()
Shipment.objects.filter(current_status="picked_up")
Shipment.objects.get(id=1)
```

**Por qué importa `full_clean()`**: cuando guardas con `.save()` a secas, Django **no**
valida automáticamente cosas como `choices` o `max_length` a nivel de Python (sí lo
hace la base de datos para algunas cosas, pero no todas). `full_clean()` es la forma
de probar, desde el shell, si un dato cumpliría las reglas del modelo antes de
guardarlo — muy útil para practicar qué significa cada *field option*.

### Querysets

Un `QuerySet` es lo que regresa Django cada vez que le pides datos a un modelo — no
es una lista de objetos "ya traída" de la base de datos, sino una **consulta armada
pero todavía no ejecutada**. Django la ejecuta hasta el último momento posible
(*evaluación perezosa* / *lazy evaluation*), y la puedes seguir encadenando antes de
eso:

```python
from shipments.models import Shipment

qs = Shipment.objects.filter(current_status="in_transit")   # todavía no toca la DB
qs = qs.exclude(recipient_address__icontains="CDMX")          # se sigue armando
qs = qs.order_by("-created_at")[:5]                            # sigue sin ejecutarse

for envio in qs:        # AQUÍ es cuando Django por fin dispara el SQL
    print(envio.tracking_number)
```

Métodos de queryset que vas a usar seguido:

| Método | Qué hace |
|--------|-----------|
| `.filter(**kwargs)` | Filtra por condiciones (`current_status="delivered"`) |
| `.exclude(**kwargs)` | Lo contrario de `filter` |
| `.get(**kwargs)` | Trae **un solo** objeto; lanza error si hay 0 o más de 1 |
| `.order_by("campo")` / `"-campo"` | Ordena ascendente / descendente |
| `.values("campo")` | Regresa diccionarios en vez de instancias del modelo |
| `.count()` | Cuenta resultados sin traer los objetos completos |
| `.exists()` | `True`/`False`, más eficiente que `if qs:` cuando no necesitas los datos |
| `.select_related("fk")` | Trae la relación `ForeignKey` en la misma consulta SQL (JOIN) — lo usamos en `ShipmentStatusEventViewSet` |
| `.prefetch_related("relacion")` | Trae relaciones inversas/muchos-a-muchos en consultas separadas pero eficientes — lo usamos en `ShipmentViewSet` para traer `status_events` |

Esto último ya lo estás usando sin quizás notarlo: en
[shipments/views.py](../shipments/views.py), `Shipment.objects.prefetch_related('status_events')`
existe justo para evitar el problema clásico de "N+1 consultas" (una consulta por
cada envío para traer sus eventos, en vez de una sola consulta optimizada).

---

## 14.3 Opciones robustas en campos de modelos, modelos abstractos y creación a granel

### Opciones de campo más importantes

Ya usamos varias en [shipments/models.py](../shipments/models.py). Aquí el porqué de
cada una:

| Opción | Para qué sirve | Ejemplo en este proyecto |
|--------|-----------------|----------------------------|
| `max_length` | Obligatorio en `CharField`, límite de caracteres | `sender_name = CharField(max_length=150)` |
| `null=True` | Permite `NULL` en la **base de datos** | No lo usamos todavía — pensado para campos numéricos/fecha opcionales |
| `blank=True` | Permite dejar el campo vacío en **formularios/validación** (no afecta la DB) | `location = CharField(blank=True)` |
| `default=...` | Valor si no se especifica nada | `current_status = CharField(default=ShipmentStatus.CREATED)` |
| `choices=...` | Restringe los valores válidos a una lista fija | `status = CharField(choices=ShipmentStatus.choices)` |
| `unique=True` | No puede haber dos filas con el mismo valor | `tracking_number = CharField(unique=True)` |
| `editable=False` | El campo no aparece en formularios/admin para editarlo a mano | `tracking_number = CharField(editable=False)` |
| `auto_now_add=True` | Se llena solo, **una vez**, al crear el registro | `created_at = DateTimeField(auto_now_add=True)` |
| `auto_now=True` | Se actualiza solo **cada vez** que se guarda | `updated_at = DateTimeField(auto_now=True)` |

**Regla práctica para no confundirte con `null` vs `blank`**: `null` es sobre la base
de datos (¿puede la columna estar vacía en SQL?), `blank` es sobre validación de
formularios (¿puedo dejar el campo vacío al llenarlo?). En campos de texto casi nunca
usarás `null=True` (se prefiere guardar `""` en vez de `NULL`); en campos de fecha,
número o `ForeignKey` opcional, sí es común usar ambos juntos.

### Model.TextChoices

Antes de `TextChoices`, definir las opciones de un `CharField` se hacía con una lista
de tuplas suelta (`STATUS_CHOICES = [("created", "Creado"), ...]`), fácil de
desincronizar del resto del código. `TextChoices` (y su prima `IntegerChoices`) las
convierte en una clase con nombres legibles, autocompletables y reutilizables — es
justo lo que usamos para los estatus de envío:

```python
class ShipmentStatus(models.TextChoices):
    CREATED = 'created', 'Creado'          # CREATED.value == 'created'
    PICKED_UP = 'picked_up', 'Recolectado' # CREATED.label == 'Creado'
    ...

# En el modelo:
current_status = models.CharField(
    max_length=20, choices=ShipmentStatus.choices, default=ShipmentStatus.CREATED
)
```

Ventajas frente a la lista de tuplas suelta:

- `ShipmentStatus.CREATED` es una constante con autocompletado en el editor — ya no
  escribes el string `"created"` a mano en once lugares distintos (con riesgo de
  errores de dedo).
- `ShipmentStatus.choices` genera automáticamente la lista `[(value, label), ...]`
  que Django necesita para `choices=`.
- Se reutiliza igual en `Shipment.current_status` y en `ShipmentStatusEvent.status`
  (ver [models.py](../shipments/models.py)) sin duplicar la definición.
- En el shell: `ShipmentStatus.labels` (todas las etiquetas), `ShipmentStatus.values`
  (todos los valores) — útil para poblar un `<select>` de un frontend o validar datos.

### Modelos abstractos

Sirven para no repetir campos entre modelos. Si en este proyecto quisiéramos que
`Shipment` y `ShipmentStatusEvent` compartieran una forma estándar de manejar
`created_at`/`updated_at`, en vez de escribirlos dos veces haríamos:

```python
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True   # clave: Django NO crea una tabla para este modelo


class Shipment(TimeStampedModel):
    ...  # hereda created_at y updated_at automáticamente
```

`abstract = True` le dice a Django "esto es una plantilla para heredar, no un modelo
real" — no genera tabla ni migración propia; los campos se copian a cada modelo hijo.

### Creación a granel (bulk)

Cuando necesitas insertar muchos registros de una vez, hacerlo uno por uno con `.save()`
es lento (una consulta SQL por objeto). Django ofrece:

```python
Shipment.objects.bulk_create([
    Shipment(sender_name="A", sender_address="CDMX", recipient_name="B",
             recipient_address="GDL", weight_kg="1.0"),
    Shipment(sender_name="C", sender_address="CDMX", recipient_name="D",
             recipient_address="MTY", weight_kg="2.5"),
])
```

Esto hace **una sola consulta** para insertar varios registros. La trampa:
`bulk_create` **no llama a `.save()`** de cada objeto, así que cualquier lógica
personalizada que tengamos ahí (como el `tracking_number` autogenerado en
`Shipment.save()`) **no se ejecuta**. Es algo a tener muy presente: `bulk_create` es
rápido pero se salta las señales y el `save()` custom, a menos que generes esos
valores antes de mandarlos.

---

## 14.4 SlugField, señales, fixtures y llaves foráneas

### SlugField

Un slug es una versión "amigable para URL" de un texto: minúsculas, sin espacios ni
acentos, con guiones. Por ejemplo `"Hound Express HQ"` → `"hound-express-hq"`. Sirve
para URLs legibles y mejores para SEO (`/envios/hound-express-hq/` en vez de
`/envios/1/`). No lo usamos todavía en este proyecto (nuestro identificador público es
el `tracking_number`), pero es un patrón muy común, así que vale la pena entenderlo
completo — incluyendo el problema real que resuelve: **¿qué pasa si dos registros
generarían el mismo slug?** (dos envíos con el mismo remitente, por ejemplo). Un
`SlugField(unique=True)` a secas fallaría al guardar el segundo. La solución estándar
es generar el slug y, si ya existe, agregarle un sufijo hasta que sea único:

```python
from django.db import models
from django.db.models.signals import pre_save
from django.utils.text import slugify


class Shipment(models.Model):
    ...
    slug = models.SlugField(unique=True, blank=True)


def generar_slug(instance, base=None, nuevo_slug=None):
    slug = slugify(base or instance.sender_name)
    if nuevo_slug is not None:
        slug = nuevo_slug

    # ¿Ya existe otro Shipment con este slug (que no sea el mismo objeto)?
    qs = Shipment.objects.filter(slug=slug).exclude(pk=instance.pk)
    if qs.exists():
        # Si existe, le pegamos el id del más reciente y probamos de nuevo (recursivo)
        nuevo_slug = f"{slug}-{qs.order_by('-id').first().id}"
        return generar_slug(instance, nuevo_slug=nuevo_slug)
    return slug


def shipment_pre_save_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = generar_slug(instance)


pre_save.connect(shipment_pre_save_receiver, sender=Shipment)
```

Este es el mismo patrón que viste en el ejemplo del módulo (`Article` / `create_slug` /
`pre_save_article_receiver`), adaptado a `Shipment`. Lo importante para entenderlo,
paso a paso:

1. `slugify()` limpia el texto (minúsculas, sin acentos/espacios).
2. Se busca si ya hay **otro** registro (`.exclude(pk=instance.pk)` — importante para
   no chocar contra sí mismo cuando edites un registro existente) con ese mismo slug.
3. Si sí existe, se le agrega un sufijo (aquí, el id del conflicto) y se **vuelve a
   llamar a la misma función** (recursión) para verificar que *ese* nuevo slug tampoco
   choque con nada más.
4. Todo esto pasa **antes de guardar** (`pre_save`, no `post_save` como en el ejemplo
   de estatus más abajo) porque el slug tiene que existir ya *dentro* del objeto que
   se está a punto de insertar.

### Señales (signals)

Una señal es una forma de decir "cuando pase X en cualquier parte del sistema, ejecuta
esta función" — sin tener que modificar el código que dispara el evento. Es una
alternativa a sobreescribir `.save()`.

**Ejemplo relevante para este proyecto**: ahora mismo, la lógica de "cuando se crea un
`ShipmentStatusEvent`, actualiza el `current_status` del `Shipment`" vive **dentro**
de `ShipmentStatusEvent.save()` (ver [models.py](../shipments/models.py)). Es válido,
pero una forma alternativa —y más "desacoplada"— sería usar una señal `post_save`:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=ShipmentStatusEvent)
def actualizar_estatus_envio(sender, instance, created, **kwargs):
    if created:
        instance.shipment.current_status = instance.status
        instance.shipment.save(update_fields=['current_status', 'updated_at'])
```

**Cuándo usar cada una**: si la lógica es parte esencial de "qué significa guardar
este modelo", sobreescribir `save()` (lo que hicimos) suele ser más claro y fácil de
seguir. Las señales brillan cuando quieres reaccionar a eventos de un modelo *desde
otra app*, sin acoplarlas directamente (por ejemplo, una futura app de
"notificaciones" que escuche cuando cambia el estatus de un envío, sin que
`shipments` tenga que saber que esa app existe).

### Fixtures

Son archivos (normalmente JSON) con datos "de ejemplo" o "iniciales" que puedes cargar
a la base de datos con un comando, en vez de crearlos a mano cada vez.

```bash
python manage.py dumpdata shipments --indent 2 > shipments/fixtures/ejemplo.json
python manage.py loaddata ejemplo.json
```

Útiles para tener datos de prueba consistentes en el equipo (o para que el profesor/
evaluador levante el proyecto y ya tenga envíos de ejemplo sin capturarlos a mano).

### Llaves foráneas (ForeignKey) para "seleccionar" modelos relacionados

Ya usamos una: `ShipmentStatusEvent.shipment` es un `ForeignKey` a `Shipment`. Esto
crea una relación "muchos a uno": muchos eventos pueden apuntar al mismo envío.

```python
shipment = models.ForeignKey(
    Shipment,
    on_delete=models.CASCADE,      # qué hacer si se borra el Shipment
    related_name='status_events',  # cómo se llama el acceso "hacia atrás"
)
```

- `on_delete=CASCADE`: si borras el `Shipment`, se borran también todos sus eventos.
  Otras opciones comunes: `PROTECT` (impide borrar si hay relacionados),
  `SET_NULL` (requiere `null=True`).
- `related_name='status_events'`: gracias a esto podemos hacer
  `shipment.status_events.all()` para obtener todos los eventos de un envío
  (lo usamos en [views.py](../shipments/views.py), acción `status_history`). Sin
  `related_name`, Django usaría por defecto `shipment.shipmentstatusevent_set.all()`.

En el admin ([admin.py](../shipments/admin.py)), la clase `ShipmentStatusEventInline`
es justo una forma de "seleccionar" y editar los eventos relacionados a un envío desde
la misma pantalla del envío — otra manera práctica de trabajar con llaves foráneas sin
tener que ir modelo por modelo.

---

## Puntos clave adicionales del módulo

### Django Admin refleja tus modelos automáticamente

Cuando registras un modelo en `admin.py` (como hicimos con `@admin.register(Shipment)`
en [shipments/admin.py](../shipments/admin.py)), Django genera solo con eso una
interfaz completa de listar/crear/editar/borrar — sin escribir HTML ni vistas a mano.
Si mañana le agregas un campo nuevo a `Shipment` y corres su migración, ese campo
aparece solo en el formulario del admin (a menos que lo excluyas explícitamente).

Esto también aplica, desde el primer momento, a **usuarios y grupos**: Django trae de
fábrica los modelos `User` y `Group` (de `django.contrib.auth`, ya en
`INSTALLED_APPS` — ver [hound_express/settings.py](../hound_express/settings.py)) ya
registrados en `/admin/`, sin que tengamos que hacer nada. Ahí es donde crearías, por
ejemplo, una cuenta de "operador de sucursal" que solo pueda gestionar
`ShipmentStatusEvent` pero no borrar envíos — usando permisos y grupos, sin escribir
código de autenticación desde cero.

### Ejemplo de uso en el mercado laboral

- **Gestión de contenido**: empresas usan el Django Admin (tal cual, o poco
  personalizado) para que su equipo de operaciones/soporte actualice datos —en este
  caso, estatus de envíos— sin depender de un desarrollador para cada cambio.
- **SEO**: los Slug Fields son la base de URLs amigables (`/blog/mi-articulo/` en vez
  de `/blog/?id=482`), algo que buscan casi todos los sitios con contenido público.

---

## Autoevaluación (Módulo 53)

Antes de leer la respuesta corta, tápala e intenta responder tú mismo en voz alta o
por escrito — es la forma más efectiva de fijar el concepto (así lo recomienda el
propio material del curso). Cada respuesta enlaza a la explicación completa de arriba
por si quieres profundizar.

1. **¿Qué es el Django Admin y por qué es importante?**
   Interfaz integrada que gestiona modelos, usuarios y grupos con mínimo código,
   reflejando los modelos automáticamente. → [Django Admin refleja tus modelos](#django-admin-refleja-tus-modelos-automáticamente)

2. **¿Cómo se aplican los cambios en la base de datos?**
   `makemigrations` genera el archivo de cambios comparando modelos contra el estado
   anterior; `migrate` lo ejecuta contra la base de datos real. → [14.1](#141-cambios-en-los-modelos-y-qué-son-las-migraciones)

3. **¿Qué es el shell de Django?**
   Consola interactiva con tu proyecto cargado, para crear/consultar/actualizar/borrar
   objetos y validar datos sin pasar por la API o el admin. → [14.2](#142-shell-de-django-validar-y-probar-opciones-de-campos)

4. **¿Qué son los modelos abstractos?**
   Clases base con `Meta.abstract = True`: no generan tabla propia, solo comparten
   campos/métodos con los modelos que los heredan. → [Modelos abstractos](#modelos-abstractos)

5. **¿Cómo se usan Slug Fields y señales juntos?**
   Una señal (`pre_save`) genera el slug automáticamente a partir de otro campo,
   agregando un sufijo numérico si ya existe uno igual, sin ensuciar `save()`. → [SlugField](#slugfield)

6. **¿Qué son las fixtures?**
   Archivos (JSON/XML/YAML) con datos de la base de datos, para cargarlos/descargarlos
   con `loaddata`/`dumpdata` — útiles para datos de prueba o migrar entre entornos. → [Fixtures](#fixtures)

7. **¿Cómo se gestionan las relaciones entre modelos?**
   Con `ForeignKey` (y variantes `ManyToMany`/`OneToOne`), definiendo `on_delete` y
   `related_name` para acceder a la relación en ambos sentidos. → [Llaves foráneas](#llaves-foráneas-foreignkey-para-seleccionar-modelos-relacionados)

8. **¿Qué es la compresión de migraciones?**
   `squashmigrations` combina varias migraciones en una sola, simplificando el
   historial en proyectos colaborativos largos. → [Optimización con migraciones](#optimización-con-migraciones-comprimirlas-squashmigrations)

9. **¿Qué es la inserción masiva (Bulk Creation) y por qué es útil?**
   `bulk_create()` inserta muchos registros en una sola consulta SQL en vez de una por
   objeto — mucho más rápido, pero se salta `.save()` y las señales. → [Creación a granel](#creación-a-granel-bulk)

10. **¿Cómo se definen opciones dinámicas en los modelos?**
    Con clases que heredan de `Model.TextChoices` (o `IntegerChoices`): opciones
    legibles, autocompletables y reutilizables, sin listas de tuplas sueltas. → [Model.TextChoices](#modeltextchoices)
