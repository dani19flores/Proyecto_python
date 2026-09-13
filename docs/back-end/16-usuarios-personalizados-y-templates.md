# 16 — Usuario personalizado, vistas protegidas y templates (Módulo 55 de la plataforma)

Temas: clonar repos por SSH, `AbstractBaseUser` + `UserManager` (modelo de usuario a la
medida), `LoginRequiredMixin` (repaso), `TemplateView` aplicado a una vista real
(`SalesView`), templates base (`layout.html`) y meta tags.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **AbstractBaseUser** | Clase base de Django para construir un modelo de usuario propio, sin los campos de fábrica de `User` | [Usuario personalizado](#usuario-personalizado-abstractbaseuser--usermanager) |
| **LoginRequiredMixin** | Mixin que exige sesión iniciada para acceder a una vista | Ya cubierto a fondo en [docs/15](15-cbv-mixins-formularios.md#loginrequiredmixin) — aquí solo el repaso rápido |
| **Meta tags** | Etiquetas HTML con metadatos de la página (SEO, redes sociales) | [Meta tags y layout.html](#meta-tags-y-el-template-base-layouthtml) |
| **SalesView** | Vista de ejemplo del módulo: `TemplateView` protegida con `LoginRequiredMixin` | [TemplateView protegida: el patrón SalesView](#templateview-protegida-el-patrón-salesview) |
| **SSH** | Protocolo para administración remota segura y clonado de repos | [Clonar repos por SSH](#clonar-repos-por-ssh) |
| **TemplateView** | CBV que renderiza un template sin lógica de modelo | Ya cubierto en [docs/15](15-cbv-mixins-formularios.md#templateview) — aquí se usa en un caso real |
| **UserManager** | Manager personalizado que sabe crear usuarios/superusuarios para un modelo `AbstractBaseUser` | [Usuario personalizado](#usuario-personalizado-abstractbaseuser--usermanager) |

---

## Clonar repos por SSH

Ya vimos SSH en [docs/12](12-fundamentos-linux-docker-django.md#ssh) como protocolo
para conectarte de forma segura a una máquina remota. Clonar por SSH es un uso
específico de eso: en vez de que Git te pida usuario/contraseña (o un token) cada vez
que subes/bajas cambios, usas un par de llaves criptográficas (pública/privada).

```bash
# 1. Generar un par de llaves (si no tienes una)
ssh-keygen -t ed25519 -C "tu_correo@ejemplo.com"

# 2. Copiar la llave pública y agregarla en GitHub
#    (Settings → SSH and GPG keys → New SSH key)
cat ~/.ssh/id_ed25519.pub

# 3. Clonar usando la URL SSH (no la de https://)
git clone git@github.com:usuario/repositorio.git
```

La diferencia frente a clonar por HTTPS (`git clone https://github.com/...`): con
HTTPS necesitas un token o que Git Credential Manager tenga guardada la sesión (como
ya vimos que pasa en esta máquina con tu repo `hellodjango`); con SSH, la llave
privada en tu máquina *es* la credencial — nunca viaja
por la red, solo se usa para firmar la conexión.

## Usuario personalizado: `AbstractBaseUser` + `UserManager`

Django ya trae un modelo `User` completo (`django.contrib.auth.models.User`, el mismo
que vimos registrado de fábrica en el admin en [docs/14](14-modelos-y-migraciones.md#django-admin-refleja-tus-modelos-automáticamente)).
Cuando ese `User` de fábrica no encaja con tu proyecto (por ejemplo, quieres loguear
por correo en vez de `username`, o necesitas campos distintos), Django te deja
**reemplazarlo por completo** con `AbstractBaseUser`.

```python
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El usuario debe tener un correo electrónico')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)   # nunca guardar la contraseña en texto plano
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    objects = UserManager()

    USERNAME_FIELD = 'email'          # con qué campo se hace login
    REQUIRED_FIELDS = ['first_name', 'last_name']   # además de USERNAME_FIELD y password

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name
```

Pieza por pieza:

- **`AbstractBaseUser`** te da lo mínimo indispensable para autenticación: el campo
  `password` (ya hasheado) y el método `set_password()`/`check_password()`. **No**
  trae `email`, `username`, ni permisos — eso lo defines tú.
- **`UserManager`** (heredando de `BaseUserManager`) es el que sabe **crear**
  instancias correctamente: normaliza el email, y sobre todo, usa `set_password()`
  en vez de guardar la contraseña tal cual — así nunca queda en texto plano en la
  base de datos.
- **`USERNAME_FIELD`** le dice a Django qué campo usar para el login (aquí, `email`
  en vez del `username` de fábrica).
- **`REQUIRED_FIELDS`** son los campos que además se piden al crear un superusuario
  por consola (`createsuperuser`), sin contar `USERNAME_FIELD` ni `password` (esos ya
  se piden siempre).

### Cómo se compara con nuestro propio `Usuario`

En [shipments/models.py](../shipments/models.py) ya tenemos una clase `Usuario` — pero
es un `models.Model` normal, **no** un `AbstractBaseUser`. Guarda `name`, `email` y
`password` como datos, pero **no puede iniciar sesión**: no tiene `set_password()`,
no lo reconoce `request.user`, y no funciona con `LoginRequiredMixin` ni con
`permission_classes = [IsAuthenticated]` de DRF. Es, literalmente, una tabla más de
datos — cumple con lo que pedía esa entrega (una tabla `User` con esos campos), pero
no es lo mismo que "el sistema de autenticación de Django".

Si más adelante el proyecto necesita que estos usuarios **sí** puedan loguearse (por
ejemplo, para que un operador inicie sesión y solo así pueda crear `Estatus`), ahí es
donde entraría este patrón: convertir `Usuario` en un `AbstractBaseUser` con su
`UserManager`, y configurar `AUTH_USER_MODEL = 'shipments.Usuario'` en
[settings.py](../hound_express/settings.py). Es un cambio de fondo (no solo agregar
campos), así que vale la pena tenerlo claro como *el paso siguiente*, no algo que ya
esté hecho.

## `TemplateView` protegida: el patrón `SalesView`

Ya vimos `TemplateView` en [docs/15](15-cbv-mixins-formularios.md#templateview) para
páginas estáticas. El ejemplo de este módulo lo combina con `LoginRequiredMixin` —
el mismo mixin que ya documentamos, aplicado a una vista real de "ventas":

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class SalesView(LoginRequiredMixin, TemplateView):
    template_name = 'sales.html'
    login_url = '/login/'
```

Nada nuevo conceptualmente (mixin antes que la CBV, como ya vimos en
[docs/15](15-cbv-mixins-formularios.md#mixins-el-verdadero-superpoder-de-las-cbv)) —
lo interesante es que es el ejemplo mínimo de "página protegida que solo muestra
datos, sin CRUD": ni lista, ni detalle, ni formulario — un dashboard o reporte que
solo pinta lo que ya calculaste en `get_context_data()`.

## Meta tags y el template base (`layout.html`)

Cuando trabajas con templates HTML (a diferencia de nuestra API, que solo devuelve
JSON), casi siempre conviene un **template base** del que heredan todos los demás,
para no repetir `<head>`, navegación, pie de página, etc. en cada página:

```html
{# templates/layout.html #}
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="Hound Express — rastreo de envíos">
  <meta property="og:title" content="Hound Express">
  <title>{% block title %}Hound Express{% endblock %}</title>
  {% load static %}
  <link rel="stylesheet" href="{% static 'css/base.css' %}">
</head>
<body>
  <header>...</header>
  <main>{% block content %}{% endblock %}</main>
  <footer>...</footer>
</body>
</html>
```

```html
{# templates/sales.html #}
{% extends "layout.html" %}
{% block title %}Ventas — Hound Express{% endblock %}
{% block content %}
  <h1>Panel de ventas</h1>
{% endblock %}
```

- **Meta tags** (`<meta name="description">`, `og:title`, etc.) no se ven en la
  página, pero son lo que buscadores y redes sociales leen para mostrar tu link con
  título/descripción/imagen correctos al compartirlo — por eso van en el `<head>`
  del layout base, una sola vez, en vez de repetirlas en cada template.
- `{% extends %}` + `{% block %}` es cómo un template "hereda" del base: define solo
  lo que cambia (`title`, `content`), todo lo demás (header, footer, meta tags,
  estáticos) lo hereda tal cual.

**Nota para este proyecto**: como Hound Express es API pura (JSON, no HTML), no
tenemos ni necesitamos un `layout.html` — esto aplica si en algún momento se
construye un panel propio con vistas de plantilla (como `SalesView` arriba) en vez de
solo consumir la API desde otro frontend.

---

## Autoevaluación (Módulo 55)

1. **¿Cómo se clona un repositorio desde GitHub usando SSH?**
   Configurando una llave SSH en tu cuenta de GitHub y usando
   `git clone git@github.com:usuario/repo.git` en vez de la URL `https://`. → [Clonar repos por SSH](#clonar-repos-por-ssh)

2. **¿Qué es un `UserManager` personalizado?**
   Clase que controla cómo se crean usuarios/superusuarios de un modelo
   `AbstractBaseUser`, incluyendo validación (email obligatorio) y hasheo de
   contraseña vía `set_password()`. → [Usuario personalizado](#usuario-personalizado-abstractbaseuser--usermanager)

3. **¿Cómo se implementan vistas protegidas?**
   Heredando de `LoginRequiredMixin` (antes de la CBV genérica en la lista de
   herencia) — ver [docs/15](15-cbv-mixins-formularios.md#loginrequiredmixin).

4. **¿Qué es un template base y por qué importa?**
   Un archivo (`layout.html`) del que heredan los demás templates vía
   `{% extends %}`/`{% block %}`, compartiendo header/footer/meta tags/estáticos sin
   repetirlos. → [Meta tags y el template base](#meta-tags-y-el-template-base-layouthtml)

5. **¿Cómo se configuran las rutas en Django?**
   Con `urls.py` por app + inclusión en el `urls.py` raíz del proyecto vía
   `include()` — como ya hicimos con [shipments/urls.py](../shipments/urls.py) y
   [hound_express/urls.py](../hound_express/urls.py).

6. **¿Qué es Docker y cómo ayuda con Django?**
   Empaqueta código + dependencias en contenedores reproducibles — ya lo cubrimos a
   fondo en [docs/12](12-fundamentos-linux-docker-django.md#contenedor-vs-imagen-vs-dockerfile)
   y [COMANDOS_DOCKER.md](../COMANDOS_DOCKER.md).

7. **¿Cómo se manejan permisos de acceso en Django?**
   Con mixins (`LoginRequiredMixin`), decoradores (`@login_required`,
   `@permission_required`) y `permission_classes` en DRF — distintas capas para el
   mismo problema, según si es vista clásica o API.

8. **¿Qué es un `TemplateView`?**
   CBV que renderiza un template sin necesitar modelo ni lógica adicional — solo
   `template_name` (y opcionalmente `get_context_data`). → [docs/15](15-cbv-mixins-formularios.md#templateview)

9. **¿Por qué importa validar el email en modelos de usuario?**
   Para garantizar que el dato sea único, correcto y contactable — `normalize_email()`
   en `UserManager` es parte de esa validación, antes de guardar el usuario.

10. **¿Cómo se corrigen errores comunes de estructura en templates?**
    Revisando que `{% load static %}` esté presente si usas `{% static %}`, que
    `template_name`/rutas de `TEMPLATES['DIRS']` apunten a donde realmente están los
    archivos, y leyendo el mensaje de error de Django (casi siempre dice
    exactamente qué template no encontró y dónde buscó).

## Ejemplo de uso en el mercado laboral

- **E-commerce**: modelos de usuario personalizados (`AbstractBaseUser` + email como
  login) son el estándar cuando el checkout no debe depender de un `username`
  separado del correo.
- **Portales de analítica**: vistas protegidas (`LoginRequiredMixin` o
  `permission_classes` en una API) son obligatorias cuando los dashboards muestran
  datos sensibles que no todos los usuarios deben ver.
