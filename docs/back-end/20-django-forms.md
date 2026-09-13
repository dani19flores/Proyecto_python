# 20 — Django Forms, campos, widgets y Formsets (Módulo 59 de la plataforma)

Temas: `forms.Form` vs `ModelForm`, tipos de campo (`CharField`, `BooleanField`,
`IntegerField`, `EmailField`), widgets (`CheckboxSelectMultiple`), validaciones con
`clean_<campo>`, y `Formsets` para manejar varios formularios a la vez.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **BooleanField** | Campo de formulario para `True`/`False` (checkbox) | [Tipos de campo](#tipos-de-campo-de-formulario) |
| **CharField** | Campo de formulario para texto | [Tipos de campo](#tipos-de-campo-de-formulario) |
| **CheckboxSelectMultiple** | Widget para elegir varias opciones con checkboxes | [Widgets](#widgets-cómo-se-ve-un-campo) |
| **clean_** | Prefijo de método para validación personalizada por campo | [Validación personalizada](#validación-personalizada-clean_campo) |
| **EmailField** | Campo de formulario que valida formato de correo | [Tipos de campo](#tipos-de-campo-de-formulario) |
| **Formsets** | Varios formularios agrupados como una sola unidad | [Formsets](#formsets-varios-formularios-a-la-vez) |
| **IntegerField** | Campo de formulario para números enteros | [Tipos de campo](#tipos-de-campo-de-formulario) |
| **ModelForms** | Formulario generado a partir de un modelo | Ya cubierto en [docs/15](15-cbv-mixins-formularios.md#model-forms) |
| **POST** | Método HTTP para enviar datos al servidor | [GET vs POST](#get-vs-post) |
| **SearchForm** | Ejemplo de formulario simple, no ligado a un modelo | [forms.Form vs ModelForm](#formsform-vs-modelform-cuándo-usar-cada-uno) |

---

## `GET` vs `POST`

Ya usamos ambos verbos HTTP en la API (`GET /api/guias/`, `POST /api/guias/`), pero
aquí el matiz es sobre **formularios HTML**, no endpoints de API:

| | `GET` | `POST` |
|---|---|---|
| Dónde van los datos | En la URL (`?q=paquete&page=2`) | En el cuerpo de la petición, no visible en la URL |
| Uso típico | Búsquedas, filtros — no cambia nada en el servidor | Crear/modificar datos — un formulario de contacto, un login |
| Se puede repetir sin efectos secundarios | Sí (recargar la página relanza la misma búsqueda) | No debería (reenviar un `POST` duplicaría la acción — de ahí el aviso del navegador "¿reenviar formulario?") |
| Tamaño de datos | Limitado (largo de URL) | Prácticamente sin límite práctico |

Un `SearchForm` (el ejemplo del glosario) normalmente se procesa con `GET` —
justamente porque buscar no modifica nada y quieres que la URL resultante
(`?q=...`) se pueda compartir o guardar en favoritos. Un formulario de contacto o de
creación de una guía, en cambio, va por `POST`.

## `forms.Form` vs `ModelForm`: cuándo usar cada uno

Ya vimos `ModelForm` en [docs/15](15-cbv-mixins-formularios.md#model-forms) —
generado a partir de un modelo (`class Meta: model = Shipment`). Pero no todo
formulario representa una fila de la base de datos. Un `SearchForm`, por ejemplo, no
crea ni edita nada — solo captura un criterio de búsqueda:

```python
from django import forms


class SearchForm(forms.Form):
    q = forms.CharField(label='Buscar', max_length=255, required=False)
```

**Regla práctica**: si el formulario existe para crear/editar una instancia de un
modelo → `ModelForm` (te ahorra declarar cada campo a mano, ver
[docs/15](15-cbv-mixins-formularios.md#model-forms)). Si el formulario existe para
otra cosa (buscar, filtrar, iniciar sesión, subir un archivo suelto) → `forms.Form`
normal, donde declaras cada campo tú mismo.

## Tipos de campo de formulario

Los mismos nombres que ya conoces de los modelos (ver
[docs/14](14-modelos-y-migraciones.md#opciones-de-campo-más-importantes)), pero acá
viven en `forms.py` y validan **entrada de usuario**, no la base de datos:

```python
from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(label='Nombre', max_length=100)
    email = forms.EmailField(label='Correo Electrónico')
    age = forms.IntegerField(label='Edad', min_value=0, required=False)
    subscribe = forms.BooleanField(label='Suscribirme al boletín', required=False)
    message = forms.CharField(label='Mensaje', widget=forms.Textarea)
```

- **`CharField`**: texto — `max_length` limita caracteres, igual que en modelos.
- **`EmailField`**: valida automáticamente que el texto tenga forma de correo
  (`algo@algo.algo`) — sin que tú escribas esa expresión regular.
- **`IntegerField`**: solo acepta enteros; `min_value`/`max_value` acotan el rango.
- **`BooleanField`**: se renderiza como checkbox — importante: **`required=False`**
  casi siempre, porque un checkbox sin marcar no manda ningún valor al servidor, y
  Django lo interpretaría como "campo faltante" si lo dejas `required=True` por
  default.

## Widgets: cómo se *ve* un campo

El **tipo de campo** (`CharField`) controla la validación; el **widget** controla
cómo se dibuja en HTML. Por defecto cada campo ya trae un widget razonable
(`CharField` → `<input type="text">`), pero lo puedes cambiar:

```python
class EventoForm(forms.Form):
    ESTATUS_CHOICES = [
        ('picked_up', 'Recolectado'),
        ('in_transit', 'En tránsito'),
        ('delivered', 'Entregado'),
    ]
    estatus_permitidos = forms.MultipleChoiceField(
        choices=ESTATUS_CHOICES,
        widget=forms.CheckboxSelectMultiple,   # en vez de un <select multiple>
    )
```

`CheckboxSelectMultiple` dibuja una lista de casillas (una por opción) en vez del
`<select>` múltiple por defecto — mejor cuando hay pocas opciones y quieres que el
usuario las vea todas de un vistazo, sin tener que hacer `Ctrl+clic` dentro de un
`<select>`.

## Validación personalizada: `clean_<campo>`

Ya usamos este patrón exacto en
[docs/15](15-cbv-mixins-formularios.md#model-forms) con `clean_weight_kg` en un
`ModelForm` — funciona igual en un `forms.Form` normal. El ejemplo del módulo:

```python
from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(label='Nombre', max_length=100)
    email = forms.EmailField(label='Correo Electrónico')
    message = forms.CharField(label='Mensaje', widget=forms.Textarea)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@example.com'):
            raise forms.ValidationError('Por favor, use un correo de @example.com')
        return email
```

Cómo funciona: Django llama automáticamente a `clean_<nombre_del_campo>()` para
**cada** campo que tenga ese método definido, después de la validación automática
del tipo de campo (`EmailField` ya validó que *parece* un correo; `clean_email`
agrega la regla extra de negocio: que además termine en `@example.com`). El método
**debe** regresar el valor (limpio o corregido) — si no regresas nada, el campo queda
en `None` aunque la validación haya "pasado".

Para validaciones que dependen de **varios campos a la vez** (no uno solo), el
método es `clean()` (sin sufijo), sobre todo el formulario:

```python
def clean(self):
    cleaned_data = super().clean()
    password = cleaned_data.get('password')
    confirm = cleaned_data.get('confirm_password')
    if password and confirm and password != confirm:
        raise forms.ValidationError('Las contraseñas no coinciden')
    return cleaned_data
```

## Formsets: varios formularios a la vez

Un `Formset` agrupa **N copias** del mismo formulario, para crear/editar varias
instancias en un solo `POST` — por ejemplo, agregar 3 productos a la vez en vez de
uno por uno:

```python
from django.forms import formset_factory
from myapp.forms import ProductoForm

ProductoFormSet = formset_factory(ProductoForm, extra=3)  # 3 formularios vacíos

formset = ProductoFormSet(request.POST or None)
if formset.is_valid():
    for form in formset:
        if form.cleaned_data:   # ignora formularios vacíos que no se llenaron
            # guardar cada producto...
            pass
```

`extra=3` dice cuántos formularios vacíos mostrar de entrada (el usuario puede dejar
algunos en blanco). `formset.is_valid()` valida **todos** los formularios del grupo a
la vez — si uno solo falla, el formset completo se considera inválido. Para
`ModelForm`s específicamente existe `modelformset_factory`, que además sabe guardar
cada formulario válido como una fila nueva (o actualizada) del modelo.

**Dónde encajaría esto en Hound Express**: si quisiéramos un formulario HTML (no
API) para registrar varios eventos de estatus de golpe —por ejemplo, marcar 5 guías
distintas como "entregadas" en una sola pantalla— un
`modelformset_factory(EstatusForm, extra=5)` sería exactamente la herramienta. Hoy no
lo necesitamos porque la API ya permite `POST /api/estatus/` una vez por cada evento
desde el cliente que la consuma.

---

## Autoevaluación (Módulo 59)

1. **¿Qué es un formulario en Django y para qué sirve?**
   Herramienta para recolectar, validar y procesar datos de usuario de forma
   estructurada, antes de que lleguen a la lógica de negocio.

2. **¿Diferencia entre `GET` y `POST` en formularios?**
   `GET` manda datos en la URL (para búsquedas/filtros, repetible sin efectos
   secundarios); `POST` los manda en el cuerpo (para crear/modificar datos). → [GET vs POST](#get-vs-post)

3. **¿Cómo se crean formularios en Django?**
   Una clase en `forms.py` que hereda de `forms.Form` (o `forms.ModelForm`), con los
   campos como atributos de clase. → [forms.Form vs ModelForm](#formsform-vs-modelform-cuándo-usar-cada-uno)

4. **¿Qué son las validaciones personalizadas?**
   Métodos `clean_<campo>()` (por campo) o `clean()` (por todo el formulario) que
   agregan reglas de negocio más allá de lo que valida el tipo de campo solo. → [Validación personalizada](#validación-personalizada-clean_campo)

5. **¿Cómo se personalizan los formularios?**
   Cambiando `label`, `widget`, `initial` (valor por default) por campo, y usando
   widgets como `CheckboxSelectMultiple` o `Select` para controlar cómo se ven. → [Widgets](#widgets-cómo-se-ve-un-campo)

6. **¿Qué es un `ModelForm`?**
   Formulario generado a partir de un modelo (`class Meta: model = ...`), que evita
   declarar cada campo a mano. Ver [docs/15](15-cbv-mixins-formularios.md#model-forms).

7. **¿Por qué importan las migraciones al trabajar con `ModelForm`?**
   Porque el formulario refleja los campos del modelo *tal como están definidos en
   código* — si el modelo cambió pero no corriste `makemigrations`/`migrate`, la
   base de datos real puede no coincidir con lo que el formulario intenta guardar.

8. **¿Qué es un `Formset`?**
   Un grupo de N copias del mismo formulario, manejadas y validadas como una sola
   unidad, para crear/editar varios objetos en un solo envío. → [Formsets](#formsets-varios-formularios-a-la-vez)

9. **¿Cómo se configuran y validan los Formsets?**
   Con `formset_factory(FormClass, extra=N)` (o `modelformset_factory` para
   `ModelForm`s), y `formset.is_valid()` que valida todos los formularios del grupo
   a la vez.

10. **¿Qué beneficios ofrece Django Forms?**
    Simplifica recolección + validación de datos, permite personalizar la
    presentación sin tocar la lógica de validación, y se integra directo con
    modelos vía `ModelForm` — todo en un solo lugar en vez de validar a mano en cada
    vista.

## Ejemplo de uso en el mercado laboral

- **E-commerce**: formularios de checkout (dirección, pago) con validación estricta
  antes de procesar una transacción — el mismo patrón `clean_<campo>` para reglas
  como "la tarjeta no debe estar vencida".
- **CMS / plataformas de contenido**: formularios de creación de artículos con
  validaciones de calidad (longitud mínima, palabras prohibidas) vía `clean()`.

## Nota: el equivalente de todo esto en nuestra API

Hound Express no usa `forms.Form`/`ModelForm` en ningún lado — es API pura con DRF.
Pero el concepto es el mismo, solo con otro nombre: un `Serializer` de DRF
(`GuiaSerializer`, ver [shipments/serializers.py](../shipments/serializers.py)) hace
exactamente lo que un `ModelForm` haría para HTML — define campos, valida tipos, y el
método de validación por campo se llama `validate_<campo>` en vez de
`clean_<campo>`. Si quisieras replicar la validación de correo del `ContactForm` de
este módulo en un serializer de DRF, se vería así:

```python
class UsuarioSerializer(serializers.ModelSerializer):
    ...
    def validate_email(self, value):
        if not value.endswith('@example.com'):
            raise serializers.ValidationError('Use un correo de @example.com')
        return value
```

Mismo patrón, mismo propósito — Django Forms para HTML, Serializers para JSON.
