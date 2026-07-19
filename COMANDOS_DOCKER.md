# Comandos de Docker que vas a usar en este proyecto (y en el curso)

Referencia rápida de los comandos de Docker más comunes al trabajar con un proyecto
Django en contenedor, como Hound Express. Pensado para ir consultándolo mientras
avanzas en el curso (EBAC — Profesión: Desarrollador Full Stack Python).

## Conceptos rápidos

- **Imagen**: la "plantilla" armada a partir del `Dockerfile` (código + dependencias
  instaladas). No cambia sola; se reconstruye cuando cambias `requirements.txt` o el
  propio `Dockerfile`.
- **Contenedor**: una imagen *en ejecución*. Es lo que realmente corre tu servidor.
- **`docker`**: comandos para manejar imágenes/contenedores individuales.
- **`docker compose`**: comandos para manejar *varios* contenedores definidos en
  `docker-compose.yml` como si fueran un solo proyecto (en Hound Express, por ahora
  solo hay uno: `web`).

## Levantar y bajar el proyecto

```bash
docker compose up --build
```
Construye la imagen (si hay cambios) y levanta el/los contenedor(es), mostrando los
logs en la terminal (queda "pegado" ahí — `Ctrl+C` lo detiene).

```bash
docker compose up -d
```
Igual que arriba, pero en segundo plano (`-d` = *detached*). Recuperas tu terminal.

```bash
docker compose down
```
Detiene y **elimina** los contenedores y la red creados por `up`. No borra tu código
ni la base de datos si está en un volumen aparte (en este proyecto, `db.sqlite3` vive
en tu carpeta local montada como volumen, así que no se pierde).

```bash
docker compose stop
```
Solo detiene los contenedores, sin eliminarlos (más rápido de volver a levantar con
`docker compose start`, pero casi siempre vas a usar `up`/`down`).

## Ver qué está pasando

```bash
docker compose ps
```
Lista los contenedores del proyecto actual y su estado (`running`, `exited`, etc.).

```bash
docker compose logs -f
```
Muestra los logs del contenedor en vivo (`-f` = *follow*, como un `tail -f`). Útil si
levantaste con `-d` y quieres ver qué está haciendo el servidor.

## Ejecutar comandos de Django dentro del contenedor

Cuando el contenedor ya está corriendo (`up -d`), para correr comandos de `manage.py`
**dentro** del contenedor (no en tu venv local):

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell
```

`exec` = "ejecuta este comando dentro de un contenedor que ya está corriendo".
`web` es el nombre del servicio definido en `docker-compose.yml`.

Si el contenedor **no** está corriendo y solo quieres correr un comando suelto y que
se cierre después:

```bash
docker compose run --rm web python manage.py migrate
```

`--rm` elimina el contenedor temporal en cuanto termina el comando (para no ir
acumulando contenedores "muertos").

## Reconstruir la imagen

```bash
docker compose build
```
Reconstruye la imagen sin levantar contenedores (útil después de cambiar
`requirements.txt` o el `Dockerfile`). Casi siempre es más simple usar
`docker compose up --build`, que hace ambas cosas.

## Limpieza / diagnóstico

```bash
docker ps
```
Lista **todos** los contenedores corriendo en tu máquina (de cualquier proyecto), no
solo los de `docker-compose.yml`.

```bash
docker ps -a
```
Igual, pero incluye los detenidos también.

```bash
docker images
```
Lista las imágenes que tienes descargadas/construidas localmente.

```bash
docker system prune
```
⚠️ Borra contenedores detenidos, redes e imágenes sin usar para liberar espacio.
Es seguro en el sentido de que no toca contenedores activos ni volúmenes con nombre,
pero sí es una limpieza general de Docker en tu máquina, no solo de este proyecto —
úsalo con calma, no como parte del flujo normal de trabajo.

```bash
docker context ls
docker context use <nombre>
```
Muestra a qué "motor" de Docker le está hablando tu CLI, y permite cambiarlo. En esta
máquina tuvimos que hacer `docker context use default` porque el contexto
`desktop-linux` apuntaba a un pipe que no existía — si en algún momento `docker`
vuelve a decir que no encuentra el daemon aunque Docker Desktop esté abierto, este es
el primer lugar a revisar.

## Flujo típico día a día con este proyecto

1. `docker compose up --build` (primera vez o si cambiaste dependencias)
2. Dejarlo corriendo y editar código — el volumen monta tu carpeta, así que los
   cambios se reflejan sin reconstruir la imagen (Django recarga solo).
3. Si necesitas correr una migración nueva: abrir otra terminal y
   `docker compose exec web python manage.py makemigrations` /
   `migrate`.
4. `Ctrl+C` o `docker compose down` para terminar.
