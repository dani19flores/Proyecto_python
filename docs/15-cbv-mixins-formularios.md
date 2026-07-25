# 15 — Vistas basadas en clases, Mixins y formularios (Módulo 54 de la plataforma)

Temas: CBV vs FBV, las vistas genéricas más comunes (`TemplateView`, `ListView`,
`DetailView`, `CreateView`, `UpdateView`, `DeleteView`, `RedirectView`), Mixins,
`LoginRequiredMixin` y Model Forms.

Este módulo profundiza en las vistas clásicas de Django que ya empezamos a ver en
[docs/13](13-vistas-crud-y-consultas.md) (`ListView`, `DetailView`, `UpdateView`). Ahí
vimos *qué hacen*; aquí vemos *cómo se combinan entre sí* (mixins) y *cómo lucen las 5
operaciones CRUD completas* como clases.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **CBV (Class-Based Views)** | Vistas implementadas como clases, heredando comportamiento predefinido | [FBV vs CBV](#fbv-vs-cbv-la-comparación-central-del-módulo) |
| **FBV (Function-Based Views)** | Vistas implementadas como funciones simples | [FBV vs CBV](#fbv-vs-cbv-la-comparación-central-del-módulo) |
| **`TemplateView`** | CBV para páginas estáticas, sin lógica de modelo | [Las CBV genéricas](#las-cbv-genéricas-una-por-una) |
| **`ListView`** | CBV que lista objetos de un modelo | [Las CBV genéricas](#las-cbv-genéricas-una-por-una) |
| **`DetailView`** | CBV que muestra el detalle de un objeto | [Las CBV genéricas](#las-cbv-genéricas-una-por-una) |
| **`CreateView`** | CBV que crea un objeto nuevo vía formulario | [Las CBV genéricas](#las-cbv-genéricas-una-por-una) |
| **`RedirectView`** | CBV que solo redirige a otra URL | [Las CBV genéricas](#las-cbv-genéricas-una-por-una) |
| **Mixins** | Clases que encapsulan comportamiento reutilizable entre varias CBV | [Mixins](#mixins-el-verdadero-superpoder-de-las-cbv) |
| **`LoginRequiredMixin`** | Mixin que exige sesión iniciada para acceder a una vista | [LoginRequiredMixin](#loginrequiredmixin) |
| **Model Forms** | Formularios generados automáticamente a partir de un modelo | [Model Forms](#model-forms) |

---

## FBV vs CBV: la comparación central del módulo

Ya vimos en [docs/13](13-vistas-crud-y-consultas.md) `render()` y `get_object_or_404`
usados **dentro de una función** — eso es una **FBV** (*Function-Based View*): una
función normal de Python que recibe `request` y regresa una respuesta.

```python
# FBV — todo el control es explícito, todo el código es tuyo
def shipment_list(request):
    shipments = Shipment.objects.all()
    return render(request, "shipments/shipment_list.html", {"shipments": shipments})
```

Una **CBV** (*Class-Based View*) resuelve lo mismo heredando de una clase de Django
que ya trae la lógica común resuelta:

```python
# CBV — la misma funcionalidad, heredada
from django.views.generic import ListView

class ShipmentListView(ListView):
    model = Shipment
    template_name = "shipments/shipment_list.html"
```

| | FBV | CBV |
|---|-----|-----|
| **Control** | Total, explícito, tú escribes cada línea | Implícito, heredado — tú solo *ajustas* lo que cambia |
| **Repetición** | Alta si tienes muchas vistas similares (list, detail, create...) | Baja — la lógica común vive en la clase padre |
| **Curva de aprendizaje** | Más fácil de leer de un tirón al inicio | Requiere entender qué hace la clase padre "por debajo" |
| **Extensibilidad** | Copiar/pegar y modificar | Sobreescribir un método puntual (`get_queryset`, etc.) |
| **Cuándo conviene** | Lógica única, poco reutilizable, o muy simple | CRUD estándar, o cuando quieres compartir comportamiento (mixins) |

**Nuestro propio proyecto ya tomó esta misma decisión, un nivel más arriba**: en vez de
elegir entre FBV y CBV para HTML, usamos `viewsets.ModelViewSet` de DRF (ver
[shipments/views.py](../shipments/views.py)) — que es el equivalente "CBV" del mundo
API: una sola clase que combina el trabajo de `ListView` + `DetailView` + `CreateView`
+ `UpdateView` + `DeleteView` juntas.

## Las CBV genéricas, una por una

Todas viven en `django.views.generic` y siguen el mismo patrón: heredas, defines unos
cuantos atributos de clase, y opcionalmente sobreescribes un método puntual.

### `TemplateView`

La más simple: solo renderiza un template, sin modelo de por medio. Para páginas
estáticas ("Acerca de", "Términos y condiciones"):

```python
from django.views.generic import TemplateView

class AcercaDeView(TemplateView):
    template_name = "paginas/acerca_de.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["version"] = "1.0"
        return context
```

### `ListView` y `DetailView`

Ya los vimos en [docs/13](13-vistas-crud-y-consultas.md#listview-listar-objetos) con
`Shipment`. Su equivalente API en este proyecto son las acciones `list` y `retrieve`
de `ShipmentViewSet`.

### `CreateView`

Muestra un formulario y, al enviarlo válido, crea el objeto:

```python
from django.views.generic.edit import CreateView
from shipments.models import Shipment

class ShipmentCreateView(CreateView):
    model = Shipment
    fields = ["sender_name", "sender_address", "recipient_name",
              "recipient_address", "weight_kg"]
    template_name = "shipments/shipment_form.html"
    success_url = "/shipments/"
```

Nota que `fields` es exactamente la misma idea que los campos *escribibles* de
`ShipmentSerializer` (ver [serializers.py](../shipments/serializers.py)) — en ambos
mundos, decides explícitamente qué puede llenar quien usa el formulario/API, dejando
fuera `tracking_number` o `current_status` (esos se calculan solos). El equivalente
API de `CreateView` es la acción `create` de `ShipmentViewSet`.

### `UpdateView` y `DeleteView`

`UpdateView` ya se vio en [docs/13](13-vistas-crud-y-consultas.md#updateview-actualizar-un-objeto).
`DeleteView` sigue el mismo patrón, pero pide **confirmación** antes de borrar:

```python
from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy
from shipments.models import Shipment

class ShipmentDeleteView(DeleteView):
    model = Shipment
    template_name = "shipments/shipment_confirm_delete.html"  # página "¿seguro?"
    success_url = reverse_lazy("shipment-list")
```

Equivalente API: la acción `destroy` de `ShipmentViewSet` — con la diferencia de que
una API normalmente no pide "confirmación" con una página intermedia; el cliente
(frontend, app) es quien decide mostrar ese diálogo antes de mandar el `DELETE`.

### `RedirectView`

La más chica de todas: solo redirige, sin lógica ni template.

```python
from django.views.generic.base import RedirectView

class TrackingLegacyRedirectView(RedirectView):
    pattern_name = "shipment-detail"   # redirige al nombre de otra URL
    permanent = False                   # False = 302, True = 301
```

Útil, por ejemplo, si algún día cambias `/rastreo/<id>/` por `/envios/<id>/` y quieres
que los links viejos (guardados en favoritos, correos ya enviados) sigan funcionando.

---

## Mixins: el verdadero superpoder de las CBV

Un **mixin** es una clase que **no se usa sola** — se combina con una CBV genérica
para agregarle un comportamiento, sin tener que reescribirlo en cada vista. Python
permite herencia múltiple, y las CBV de Django están diseñadas justo para
aprovecharla:

```python
class ShipmentUpdateView(LoginRequiredMixin, UpdateView):
    #                     ^ mixin primero      ^ CBV genérica después
    model = Shipment
    ...
```

**Regla de oro del orden**: los mixins van **antes** que la clase genérica en la
lista de herencia. Esto importa por cómo Python resuelve la herencia múltiple (MRO —
*Method Resolution Order*): busca los métodos de izquierda a derecha, así que el
mixin necesita "interceptar" antes de que la CBV genérica haga su trabajo (por
ejemplo, `LoginRequiredMixin` necesita frenar la petición *antes* de que `UpdateView`
intente mostrar el formulario).

### `LoginRequiredMixin`

El mixin más común: exige sesión iniciada, si no, redirige al login.

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

class ShipmentListView(LoginRequiredMixin, ListView):
    model = Shipment
    login_url = "/accounts/login/"      # a dónde mandar si no hay sesión
    redirect_field_name = "next"          # para regresar aquí tras loguearse
```

Es el equivalente CBV del decorador `@login_required` que vimos en
[docs/13](13-vistas-crud-y-consultas.md#login_required-y-autenticación-en-una-api)
para FBV. En nuestra API, el equivalente es `permission_classes = [IsAuthenticated]`
en `ShipmentViewSet` — que **hoy no tenemos configurado** (la API está abierta sin
autenticación). Es el mismo hueco de seguridad señalado en docs/13, visto ahora desde
el lado de mixins.

### Un mixin propio

Para entender que un mixin es "solo una clase con métodos", uno hecho a mano que
agregue un título de página a cualquier CBV:

```python
class TemplateTitleMixin:
    page_title = "Hound Express"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        return context


class ShipmentListView(TemplateTitleMixin, ListView):
    model = Shipment
    page_title = "Envíos activos"   # sobreescribe el default del mixin
```

Cualquier CBV que herede de `TemplateTitleMixin` gana automáticamente un
`page_title` en su contexto, sin copiar/pegar ese método en cada vista — esa es la
razón de ser de los mixins: lógica compartida, escrita una sola vez.

## Model Forms

Un `ModelForm` genera un formulario **a partir de un modelo**, sin tener que declarar
cada campo a mano (eso sería un `forms.Form` normal). Es la pieza que usan por debajo
`CreateView`/`UpdateView` cuando les das `fields = [...]` en vez de un `form_class`
explícito — pero se puede (y a veces conviene) declararlo aparte para agregarle
validaciones propias:

```python
from django import forms
from shipments.models import Shipment

class ShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = ["sender_name", "sender_address", "recipient_name",
                  "recipient_address", "weight_kg"]

    def clean_weight_kg(self):
        peso = self.cleaned_data["weight_kg"]
        if peso <= 0:
            raise forms.ValidationError("El peso debe ser mayor a cero.")
        return peso


class ShipmentCreateView(CreateView):
    model = Shipment
    form_class = ShipmentForm   # usamos el form explícito, con su validación extra
    template_name = "shipments/shipment_form.html"
```

`clean_weight_kg` es el lugar donde pondrías una regla de negocio que no se puede
expresar solo con opciones de campo (`max_length`, `choices`, etc. — ver
[docs/14](14-modelos-y-migraciones.md#opciones-de-campo-más-importantes)). El
equivalente exacto en nuestra API es un método `validate_weight_kg` en
`ShipmentSerializer` (DRF sigue el mismo patrón de "un `clean_<campo>`/`validate_<campo>`
por campo" que los Model Forms de Django).

## Personalizar `get_queryset` y `get_success_url`

Dos de los métodos que más vas a sobreescribir en la práctica:

```python
class ShipmentListView(ListView):
    model = Shipment

    def get_queryset(self):
        # Filtra: solo los envíos del usuario actual, no todos
        return Shipment.objects.filter(created_by=self.request.user)


class ShipmentCreateView(CreateView):
    model = Shipment
    fields = [...]

    def get_success_url(self):
        # A dónde ir después de crear el envío exitosamente
        return reverse("shipment-detail", kwargs={"pk": self.object.pk})
```

`get_queryset` cambia **qué datos** ve la vista (piénsalo como el `.filter(...)` que
ya usamos en `ShipmentStatusEventViewSet.get_queryset()` de nuestro proyecto real,
para filtrar eventos por `?shipment=<id>` — ver [views.py](../shipments/views.py)).
`get_success_url` decide **a dónde redirigir** tras una acción exitosa — algo que en
una API no aplica igual (una API regresa el objeto creado en JSON, con `Response`, en
vez de redirigir a otra página).

---

## Autoevaluación (Módulo 54)

1. **¿Qué son las CBV?**
   Vistas implementadas como clases que heredan comportamiento predefinido de Django,
   facilitando reutilización y mantenimiento. → [FBV vs CBV](#fbv-vs-cbv-la-comparación-central-del-módulo)

2. **¿Cómo se comparan CBV con FBV?**
   CBV: más estructura y reutilización vía herencia; FBV: más directas y fáciles de
   leer para tareas simples, pero repetitivas si hay muchas vistas parecidas.

3. **¿Qué es `ListView` y cómo se usa?**
   CBV que lista objetos de un modelo, resolviendo consulta + paginación + render
   automáticamente. → [ListView y DetailView](#listview-y-detailview)

4. **¿Qué hace `DetailView`?**
   Muestra el detalle de un solo objeto, buscándolo por `pk`/`slug` automáticamente.

5. **¿Cómo se implementa `RedirectView`?**
   Con `pattern_name` (o `url`) y `permanent` (302 vs 301), sin lógica ni template
   propios. → [RedirectView](#redirectview)

6. **¿Qué son los mixins?**
   Clases con comportamiento reutilizable que se combinan (herencia múltiple) con una
   CBV genérica; van **antes** que la CBV en la lista de herencia. → [Mixins](#mixins-el-verdadero-superpoder-de-las-cbv)

7. **¿Cómo protege `LoginRequiredMixin`?**
   Verifica sesión iniciada antes de ejecutar la vista; si no hay, redirige a
   `login_url`. Equivalente de `@login_required` para CBV. → [LoginRequiredMixin](#loginrequiredmixin)

8. **¿Qué son los Model Forms?**
   Formularios generados desde un modelo (`class Meta: model = ...`), con validación
   por campo vía `clean_<campo>`. → [Model Forms](#model-forms)

9. **¿Cómo se usan `CreateView`, `UpdateView` y `DeleteView`?**
   Cada uno resuelve una operación CRUD con formulario/confirmación ya armados;
   normalmente se combinan con `LoginRequiredMixin` para exigir autenticación. → [Las CBV genéricas](#las-cbv-genéricas-una-por-una)

10. **¿Por qué personalizar `get_queryset` y `get_success_url`?**
    `get_queryset` controla qué datos ve la vista (filtrado); `get_success_url`
    controla a dónde va el usuario tras una acción exitosa. → [Personalizar get_queryset y get_success_url](#personalizar-get_queryset-y-get_success_url)

## Ejemplo de uso en el mercado laboral

- **Paneles de administración**: CBV + mixins son el patrón estándar para construir
  paneles internos a medida (más flexibles que el Django Admin de fábrica, pero sin
  reescribir CRUD desde cero).
- **E-commerce**: `ListView`/`DetailView` para catálogos y fichas de producto son
  prácticamente el ejemplo de libro de texto — el `ProductoListView` del material del
  curso es ese caso exacto.
