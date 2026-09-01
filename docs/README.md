# Bitácora de aprendizaje — EBAC Full Stack Python

Esta carpeta es tu cuaderno de teoría, ligado al código real de Hound Express. La idea
es que cada bloque de lecciones del curso tenga su propio archivo aquí, explicando el
*por qué* de las cosas y apoyándose en ejemplos del propio proyecto — no solo copiar
comandos, sino entender qué hacen y cuándo usarlos.

## Índice

- [12 — Fundamentos: Linux, Docker y Django (Módulo 51)](12-fundamentos-linux-docker-django.md):
  Linux/terminal/SSH, contenedor vs imagen vs Dockerfile, YAML, estructura de un
  proyecto Django y una primera mirada al ORM. Buen punto de partida si algo de los
  otros dos módulos no quedó claro.
- [13 — Vistas, CRUD y consultas (Módulo 52)](13-vistas-crud-y-consultas.md): CRUD,
  vistas genéricas (`ListView`, `DetailView`/`RetrieveView`, `UpdateView`), `render`,
  `get_object_or_404`, `login_required`, Middleware y consultas complejas con `Q`.
  Cada concepto contrastado con su equivalente real en `ShipmentViewSet`.
- [14 — Modelos y migraciones (Módulo 53)](14-modelos-y-migraciones.md): cómo cambiar
  modelos, qué son las migraciones, Shell de Django, opciones de campos, modelos
  abstractos, creación a granel, SlugField, señales, fixtures y llaves foráneas.
  Incluye glosario del módulo y autoevaluación con preguntas de repaso.
- [15 — CBV, Mixins y formularios (Módulo 54)](15-cbv-mixins-formularios.md): FBV vs
  CBV, las vistas genéricas (`TemplateView`, `ListView`, `DetailView`, `CreateView`,
  `UpdateView`, `DeleteView`, `RedirectView`), Mixins, `LoginRequiredMixin` y Model
  Forms.
- [16 — Usuario personalizado, vistas protegidas y templates (Módulo 55)](16-usuarios-personalizados-y-templates.md):
  clonar repos por SSH, `AbstractBaseUser` + `UserManager`, `TemplateView` protegida
  (`SalesView`), template base (`layout.html`) y meta tags. Incluye comparación con
  el `Usuario` real de este proyecto (por qué no es lo mismo que un modelo de
  autenticación).
- [17 — Órdenes, facturación y señales (Módulo 56)](17-ordenes-facturacion-y-senales.md):
  el dominio de ejemplo (`Order`, `Address`, `Billing`, `Carts`, `Product`),
  `ForeignKey` en un caso real, `pre_save`/`post_save` a fondo con `Order`, y
  `get_absolute_url`. Contrasta el `ForeignKey` real de `Order` con el
  `IntegerField` suelto que usamos en `Estatus.guideId`.
- [18 — Migraciones avanzadas, OneToOneField y errores comunes (Módulo 57)](18-migraciones-avanzadas-y-onetoone.md):
  las 7 opciones de `on_delete`, `OneToOneField` vs `ForeignKey`, Pillow y
  `ImageField`, y los errores más comunes al trabajar con migraciones (imports
  desactualizados, dependencias entre modelos, revertir/reaplicar).
- [19 — AJAX, Chart.js y OrderManager a fondo (Módulo 58)](19-ajax-charts-y-order-manager.md):
  la CBV base `View`, `JsonResponse` vs `Response` de DRF, AJAX/jQuery, Chart.js vía
  CDN, `timedelta` para rangos de fecha, y los métodos reales de `OrderManager`
  (`total_data`, `by_weeks_range`, `get_sales_breakdown`). Incluye cómo se vería
  aplicado a Hound Express.
- [20 — Django Forms, campos, widgets y Formsets (Módulo 59)](20-django-forms.md):
  `forms.Form` vs `ModelForm`, tipos de campo (`CharField`, `BooleanField`,
  `IntegerField`, `EmailField`), widgets (`CheckboxSelectMultiple`), `clean_<campo>`
  y `Formsets`. Cierra con el paralelo exacto: Django Forms para HTML ↔ Serializers
  de DRF para JSON.

Cuando avances a un tema nuevo, dime qué lección/número toca y te agrego un archivo
nuevo aquí siguiendo el mismo formato.
