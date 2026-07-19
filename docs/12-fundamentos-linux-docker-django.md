# 12 — Fundamentos: Linux, Docker y Django (Módulo 51 de la plataforma)

Temas: Linux y la terminal, contenedores y Docker (imagen, `Dockerfile`, YAML), qué es
Django y cómo se estructura un proyecto, y una primera mirada al ORM.

Es el módulo más "de base" de los tres que llevamos documentados — asienta el
vocabulario que los módulos 52 y 53 (ver [docs/13](13-vistas-crud-y-consultas.md) y
[docs/14](14-modelos-y-migraciones.md)) ya dan por hecho. Vale la pena leerlo primero
si algo de los otros dos no terminó de quedar claro.

## Glosario del módulo

| Término | Definición corta | Dónde lo ves en este proyecto |
|---------|--------------------|-----------------------------------|
| **Contenedor** | Unidad de software en ejecución que empaqueta código + dependencias, aislada del resto del sistema | [Contenedor vs imagen vs Dockerfile](#contenedor-vs-imagen-vs-dockerfile) — `web-1` cuando corres `docker compose up` |
| **Dockerfile** | Archivo de texto con las instrucciones para construir una imagen | [Dockerfile](../Dockerfile) de este proyecto |
| **Imagen de Docker** | Plantilla inmutable (de solo lectura) para crear contenedores | Se genera al correr `docker compose build` / `up --build` |
| **Linux Kernel** | Núcleo del sistema operativo Linux, gestiona hardware/recursos | [Linux](#linux-y-la-terminal) |
| **ORM** | Traduce entre objetos de Python y filas de una base de datos, sin escribir SQL a mano | [El ORM de Django](#el-orm-de-django) — es literalmente `Shipment.objects.all()`, etc. |
| **SSH** | Protocolo para acceder de forma segura a una computadora remota | [SSH](#ssh) |
| **Terminal** | Interfaz de línea de comandos para interactuar con el sistema operativo | La que usas para correr `python manage.py ...` y `docker ...` |
| **YAML** | Formato de texto legible para archivos de configuración | [YAML](../docker-compose.yml) de este proyecto |

---

## Linux y la terminal

La mayoría de los servidores del mundo (y las imágenes base de Docker, incluida la
que usamos, `python:3.13-slim`) corren Linux, no Windows. El **Linux Kernel** es el
núcleo que administra memoria, procesos y hardware; encima de él corren las
distribuciones (Ubuntu, Debian, Alpine...). Aunque desarrolles en Windows (como en
esta máquina), es casi seguro que tu código termine corriendo sobre Linux en
producción — de ahí la importancia de sentirte cómodo en una **terminal** con
comandos básicos:

```bash
pwd          # en qué carpeta estoy
ls -la       # listar archivos (con detalles y ocultos)
cd carpeta   # moverme a una carpeta
cat archivo  # ver el contenido de un archivo
mkdir nombre # crear una carpeta
rm archivo   # borrar un archivo
```

Cuando corremos `docker compose exec web python manage.py migrate` (ver
[COMANDOS_DOCKER.md](../COMANDOS_DOCKER.md)), en realidad le estamos diciendo a Docker
"entra al contenedor Linux que está corriendo y ejecuta este comando ahí dentro" — por
eso, aunque desarrolles desde Windows, tu aplicación real vive y respira Linux.

### SSH

SSH (*Secure Shell*) es el protocolo para conectarte a una computadora remota de forma
segura (cifrada) y operarla como si estuvieras sentado frente a ella, usando la
terminal. Todavía no lo usamos en este proyecto (corre todo en tu máquina, local o en
Docker Desktop), pero es la herramienta que usarás el día que despliegues Hound
Express en un servidor real (una VPS, por ejemplo) — te conectas por SSH para
configurarlo, ver logs, correr migraciones en producción, etc.

---

## Contenedor vs imagen vs Dockerfile

Son tres cosas relacionadas pero distintas, y es fácil confundirlas al inicio:

1. **Dockerfile** → la *receta* (instrucciones de texto).
2. **Imagen** → el *platillo ya cocinado y empaquetado*, listo para servirse, pero
   todavía no "servido" (no está corriendo).
3. **Contenedor** → el platillo *servido y siendo comido ahora mismo* — la imagen en
   ejecución.

Con nuestro propio [Dockerfile](../Dockerfile) como ejemplo:

```dockerfile
FROM python:3.13-slim      # 1. parte de una imagen base ya armada (Python instalado)
WORKDIR /app                # 2. carpeta de trabajo dentro del contenedor
COPY requirements.txt .     # 3. copia solo este archivo primero (para cachear el build)
RUN pip install -r requirements.txt   # 4. instala dependencias -> esto queda "horneado" en la imagen
COPY . .                    # 5. copia el resto del código
EXPOSE 8000                 # 6. documenta qué puerto usa la app
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]   # 7. qué ejecutar al arrancar el contenedor
```

- `docker compose build` (o `up --build`) lee el `Dockerfile` y genera la **imagen**
  `proyecto_python-web` — un "congelado" con Python 3.13, Django, DRF y tu código,
  todo listo.
- `docker compose up` toma esa imagen y crea un **contenedor** (`web-1`) — un proceso
  aislado corriendo, con su propia red y sistema de archivos, pero compartiendo el
  kernel de Linux del host.

La imagen es inmutable (no cambia sola); si modificas `requirements.txt` necesitas
reconstruirla (`--build`). El contenedor sí es "vivo": lo puedes detener
(`docker compose down`), y al volver a levantarlo con la misma imagen, arranca
limpio otra vez (por eso los datos importantes, como `db.sqlite3`, viven fuera del
contenedor, montados como volumen — si no, se perderían cada vez que lo recreas).

## YAML

Formato de texto pensado para que humanos lo lean y editen fácilmente (a diferencia de
JSON, permite comentarios y es menos "cuadrado"). Usa indentación (espacios, nunca
tabs) para representar estructura, en vez de llaves `{}`. Nuestro propio
[docker-compose.yml](../docker-compose.yml) es un archivo YAML:

```yaml
services:
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
```

Aquí `services` es una clave que contiene otra estructura (`web`), que a su vez tiene
sus propias claves (`build`, `command`, `volumes`, `ports`). La indentación es la que
define qué pertenece a qué — un error de espacios es el bug más común al editar YAML.

---

## Django: estructura de un proyecto

Django separa dos niveles de organización, y este proyecto es un ejemplo directo:

- **Archivos de proyecto** ([hound_express/](../hound_express/)): configuración
  general — `settings.py` (base de datos, apps instaladas, middleware...),
  `urls.py` raíz, `wsgi.py`/`asgi.py`. Solo hay **una** carpeta de proyecto.
- **Archivos de aplicación** ([shipments/](../shipments/)): el código de una
  funcionalidad concreta — sus propios `models.py`, `views.py`, `admin.py`,
  `urls.py`, `migrations/`. Un proyecto puede tener **varias** apps (creadas con
  `startapp`, ver [docs/13](13-vistas-crud-y-consultas.md#startapp)); en Hound
  Express hoy solo tenemos `shipments`, pero si mañana agregáramos, por ejemplo,
  facturación, sería una segunda app independiente dentro del mismo proyecto.

Esta separación es la que te permite reutilizar una app en otro proyecto, o
mantenerlas desacopladas entre sí (nuestra app `shipments` no sabe nada de cómo está
configurado el proyecto en general, solo de sus propios modelos y vistas).

## El ORM de Django

ORM = *Object-Relational Mapping*. Es la capa que te permite trabajar con la base de
datos usando clases y objetos de Python, en vez de escribir SQL a mano. Cada modelo
(`class Shipment(models.Model)`) es una tabla; cada instancia (`Shipment(...)`) es una
fila; cada atributo (`sender_name`) es una columna.

Usando nuestro propio modelo en vez del ejemplo genérico de `Book` del módulo:

```python
from shipments.models import Shipment

# Crear (CREATE)
nuevo = Shipment(
    sender_name="Hound Express HQ", sender_address="CDMX",
    recipient_name="Ana López", recipient_address="Monterrey",
    weight_kg="3.20",
)
nuevo.save()

# Leer (READ) — todos, o filtrados
Shipment.objects.all()
Shipment.objects.filter(current_status="delivered")

# Actualizar (UPDATE)
envio = Shipment.objects.get(id=1)
envio.recipient_address = "Monterrey, Nuevo León"
envio.save()

# Eliminar (DELETE)
Shipment.objects.get(id=2).delete()
```

Nota que esto es **exactamente** el CRUD del módulo 52
([docs/13](13-vistas-crud-y-consultas.md#crud)), solo que visto desde el shell/ORM
directamente en vez de a través de una vista o endpoint. Por debajo, cuando alguien
hace `POST /api/shipments/`, lo que termina ejecutándose es justamente
`Shipment(...).save()` — el ORM es la pieza común entre "el shell", "el admin" y "la
API": los tres, al final, hablan con la base de datos a través del mismo ORM.

Por qué es valioso: sin el ORM, cada operación de arriba sería una consulta SQL
distinta escrita a mano (`INSERT INTO ...`, `SELECT * FROM ...`, `UPDATE ... SET`,
`DELETE FROM ...`), y además tendrías que reescribirlas si algún día cambias de motor
de base de datos (SQLite → PostgreSQL, por ejemplo). Con el ORM, ese mismo código
Python funciona igual sin importar el motor — de hecho, cambiar de SQLite a Postgres
en este proyecto sería solo editar `DATABASES` en
[settings.py](../hound_express/settings.py), sin tocar una sola línea de
`models.py` ni `views.py`.

### Migraciones (repaso rápido)

Las migraciones son cómo el ORM mantiene sincronizada la base de datos real con tus
modelos de Python. Ya lo cubrimos a fondo en
[docs/14 — Modelos y migraciones](14-modelos-y-migraciones.md#141-cambios-en-los-modelos-y-qué-son-las-migraciones);
la idea mínima para este módulo es: **nunca tocas la base de datos directamente**,
siempre pasa por `makemigrations` (generar el cambio) + `migrate` (aplicarlo).

---

## Autoevaluación (Módulo 51)

Intenta responder cada una antes de leer la respuesta.

1. **¿Qué es Linux y por qué es importante en el desarrollo web?**
   Sistema operativo de código abierto, base de la mayoría de los servidores; da un
   entorno estable con las herramientas de terminal que usas a diario. → [Linux y la terminal](#linux-y-la-terminal)

2. **¿Qué es Django y cuáles son sus ventajas?**
   Framework web en Python: ORM incluido, estructura clara (proyecto/apps), gran
   comunidad. → [Django: estructura de un proyecto](#django-estructura-de-un-proyecto)

3. **¿Cómo se estructura un proyecto Django?**
   Archivos de proyecto (configuración general, una sola carpeta) + archivos de una o
   varias apps (funcionalidad concreta, creadas con `startapp`). → [Django: estructura de un proyecto](#django-estructura-de-un-proyecto)

4. **¿Qué es el ORM y por qué es útil?**
   Capa que traduce clases/objetos de Python a filas/tablas SQL, evitando escribir SQL
   a mano y facilitando cambiar de motor de base de datos. → [El ORM de Django](#el-orm-de-django)

5. **¿Qué son las migraciones?**
   Forma incremental y controlada de aplicar cambios de `models.py` a la base de
   datos real, consistente entre entornos. → [Migraciones (repaso rápido)](#migraciones-repaso-rápido)

6. **¿Cómo ayuda Docker en el desarrollo con Django?**
   Empaqueta código + dependencias + configuración en un contenedor reproducible, para
   que el entorno sea igual en cualquier máquina. → [Contenedor vs imagen vs Dockerfile](#contenedor-vs-imagen-vs-dockerfile)

7. **¿Por qué es importante gestionar los recursos al usar Docker?**
   Los contenedores consumen memoria/CPU reales del host; detenerlos con
   `docker compose down`/`stop` cuando no se usan libera esos recursos (ver
   [COMANDOS_DOCKER.md](../COMANDOS_DOCKER.md)).

8. **¿Qué papel juega GitHub en el desarrollo con Docker y Django?**
   Repositorio para versionar y compartir el código; un repo preconfigurado (como
   `docker-django-example`) da una base lista para construir encima sin partir de
   cero.

9. **¿Cómo se realizan cambios visibles en un proyecto Django?**
   Editando modelos/vistas/plantillas (o serializers, en nuestro caso API), aplicando
   las migraciones correspondientes si el cambio toca la base de datos.

10. **¿Qué beneficios da pasar de Jupyter Notebooks a VS Code + Docker?**
    Entorno de desarrollo más "profesional": mejor integración con Git, y un entorno
    de contenedores reproducible en vez de depender de lo que esté instalado a mano en
    tu máquina.

## Ejemplo de uso en el mercado laboral

- **Aplicaciones web escalables**: Instagram es un ejemplo público y conocido de una
  aplicación construida sobre Django, elegido por permitir desarrollo rápido sin
  sacrificar estructura a medida que el equipo/proyecto crece.
- **Despliegue en contenedores**: Docker es el estándar de facto para empaquetar
  aplicaciones y moverlas entre entornos de desarrollo, pruebas y producción sin
  sorpresas de "en mi máquina sí funciona" — exactamente el problema que resolvimos
  para este proyecto en [COMANDOS_DOCKER.md](../COMANDOS_DOCKER.md).
