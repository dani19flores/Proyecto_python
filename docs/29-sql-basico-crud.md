# 29 — SQL básico: CREATE, INSERT, UPDATE, DELETE (Módulo 69 de la plataforma)

Temas: los comandos SQL fundamentales para crear tablas y manipular datos —
`CREATE TABLE`, `ALTER`, `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, `DROP`, la
cláusula `WHERE`, y `GetDate()` de SQL Server. Este módulo es el SQL "crudo" que el
ORM de Django ya ha estado generando por nosotros desde el principio de este
proyecto — aquí lo vemos explícito.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **ALTER** | Modifica la estructura de una tabla ya existente | [ALTER: modificar una tabla existente](#alter-modificar-una-tabla-existente) |
| **CREATE TABLE** | Define una tabla nueva | [CREATE TABLE: lo que ya generó nuestra migración](#create-table-lo-que-ya-generó-nuestra-migración) |
| **DELETE** | Borra filas específicas de una tabla | [DELETE vs TRUNCATE vs DROP](#delete-vs-truncate-vs-drop-la-diferencia-que-importa) |
| **DROP** | Elimina la tabla completa (estructura + datos) | [DELETE vs TRUNCATE vs DROP](#delete-vs-truncate-vs-drop-la-diferencia-que-importa) |
| **GetDate** | Función de SQL Server que da la fecha/hora actual del servidor | [GetDate() y su equivalente en Django](#getdate-y-su-equivalente-en-django) |
| **INSERT** | Agrega una fila nueva a una tabla | [INSERT: crear una fila](#insert-crear-una-fila) |
| **Management Studio** | Herramienta gráfica de Microsoft para SQL Server | Ya cubierto en [docs/28](28-fundamentos-bases-de-datos.md#ide-vs-herramienta-de-base-de-datos) |
| **TRUNCATE** | Borra todas las filas de una tabla, conservando su estructura | [DELETE vs TRUNCATE vs DROP](#delete-vs-truncate-vs-drop-la-diferencia-que-importa) |
| **UPDATE** | Modifica filas existentes | [UPDATE: modificar filas existentes](#update-modificar-filas-existentes) |
| **WHERE** | Filtra qué filas afecta una consulta/comando | [WHERE: la cláusula que evita desastres](#where-la-cláusula-que-evita-desastres) |

---

## `CREATE TABLE`: lo que ya generó nuestra migración

Ya vimos esto, sin llamarlo "SQL básico", cuando corrimos `sqlmigrate` en
[docs/14](14-modelos-y-migraciones.md#141-cambios-en-los-modelos-y-qué-son-las-migraciones)
y en [scripts.sql](../scripts.sql). El `CREATE TABLE` real que generó Django para
`Guia` (SQLite, pero la sintaxis ANSI es prácticamente la misma en SQL Server):

```sql
CREATE TABLE "Guide" (
    "id" integer NOT NULL PRIMARY KEY,
    "trackingNumber" varchar(15) NOT NULL,
    "origin" varchar(100) NOT NULL,
    "destination" varchar(100) NOT NULL,
    "createdAt" date NOT NULL,
    "updatedAt" datetime NOT NULL,
    "currentStatus" varchar(20) NOT NULL
);
```

El ejemplo del módulo, en SQL Server, con la misma idea:

```sql
CREATE TABLE Clientes (
    ID INT PRIMARY KEY,
    Nombre VARCHAR(100),
    Email VARCHAR(100),
    FechaRegistro DATE
);
```

Cada línea dentro del paréntesis es una columna: `nombre_columna TIPO_DE_DATO
[restricciones]`. `PRIMARY KEY` marca la llave primaria — exactamente lo que
`models.IntegerField(primary_key=True)` le indica a Django que genere para `Guia.id`
(ver [docs/14](14-modelos-y-migraciones.md#opciones-de-campo-más-importantes)).

## `INSERT`: crear una fila

```sql
INSERT INTO Clientes (ID, Nombre, Email, FechaRegistro)
VALUES (1, 'Juan Pérez', 'juan.perez@example.com', GETDATE());
```

Es el SQL que se ejecuta por debajo cuando hacemos, desde el ORM:

```python
Guia.objects.create(
    id=1, trackingNumber='HE0000001', origin='CDMX',
    destination='GDL', currentStatus='created',
)
```

o cuando llamamos `POST /api/crear-guia` en nuestra propia API — el `ViewSet`
termina llamando `serializer.save()`, que termina en un `INSERT INTO Guide (...)
VALUES (...)` idéntico en espíritu al de arriba.

## `UPDATE`: modificar filas existentes

```sql
UPDATE Clientes
SET Email = 'juan.perez@nuevoemail.com'
WHERE ID = 1;
```

Equivalente a `Guia.objects.filter(id=1).update(currentStatus='picked_up')` en el
ORM, o a lo que dispara nuestro propio endpoint
`PATCH /api/actualizar-guia/1` (ver [shipments/views.py](../shipments/views.py)) —
por dentro, DRF llama a `instance.save()`, que Django traduce a un `UPDATE ... WHERE
id = 1`.

## `WHERE`: la cláusula que evita desastres

`WHERE` no es opcional en la práctica — es lo que le dice a `UPDATE`/`DELETE`
**cuáles** filas tocar. Sin él, el comando afecta **todas** las filas de la tabla:

```sql
UPDATE Clientes SET Email = 'nuevo@email.com';  -- ¡les cambia el email a TODOS los clientes!
```

Es exactamente el mismo peligro (y la misma solución) que ya vimos en el ORM: la
diferencia entre `Guia.objects.filter(id=1).update(...)` (equivalente a `WHERE
id=1`) y `Guia.objects.all().update(...)` (sin filtro, afecta todo). El resumen del
módulo lo remarca justo por esto: **siempre** revisa que tu `WHERE` esté puesto antes
de correr un `UPDATE` o `DELETE`, sobre todo en producción.

## `DELETE` vs `TRUNCATE` vs `DROP`: la diferencia que importa

Los tres "borran" algo, pero a niveles completamente distintos:

| Comando | Qué borra | Qué conserva | Con `WHERE` |
|---------|-------------|-----------------|----------------|
| `DELETE FROM tabla WHERE ...` | Filas específicas (o todas, sin `WHERE`) | La estructura de la tabla | Sí, opcional |
| `TRUNCATE TABLE tabla` | **Todas** las filas, de un golpe | La estructura de la tabla | No — siempre es todo o nada |
| `DROP TABLE tabla` | La tabla **completa**: filas y estructura | Nada — la tabla deja de existir | No aplica |

```sql
DELETE FROM Clientes WHERE ID = 1;   -- borra solo ese cliente
TRUNCATE TABLE Clientes;              -- vacía la tabla completa, pero sigue existiendo
DROP TABLE Clientes;                  -- la tabla ya ni existe; hay que CREATE TABLE de nuevo
```

**Equivalentes en el ORM/nuestro proyecto**: `Guia.objects.get(id=1).delete()` (o
nuestro endpoint `DELETE /api/eliminar-guia/1`) es un `DELETE ... WHERE id = 1`.
Django no expone un atajo directo a `TRUNCATE` (normalmente usarías
`Modelo.objects.all().delete()`, que es un `DELETE` sin `WHERE`, no un `TRUNCATE`
real — la diferencia práctica es que `TRUNCATE` suele ser más rápido porque no
registra cada fila borrada individualmente). Un `DROP TABLE` equivaldría a
**revertir la migración** que creó esa tabla — algo que ya hicimos en este proyecto
cuando reemplazamos `Shipment`/`ShipmentStatusEvent` por
`Guia`/`Estatus`/`Usuario` (ver [docs/18](18-migraciones-avanzadas-y-onetoone.md#errores-comunes-al-trabajar-con-migraciones)).

## `ALTER`: modificar una tabla existente

```sql
ALTER TABLE Clientes ADD Telefono VARCHAR(15);
ALTER TABLE Clientes ALTER COLUMN Email VARCHAR(150);
ALTER TABLE Clientes DROP COLUMN Telefono;
```

Agregar, modificar o quitar columnas de una tabla que **ya tiene datos** — sin tener
que borrarla y recrearla. Esto es, literalmente, lo que genera cada migración de
Django que no sea la inicial: cuando agregamos un campo a un modelo existente y
corremos `makemigrations`, Django genera una operación `AddField` que se traduce en
un `ALTER TABLE ... ADD COLUMN ...` — puedes verlo tú mismo con
`sqlmigrate` sobre cualquier migración que no sea `0001_initial` (ver
[docs/14](14-modelos-y-migraciones.md#141-cambios-en-los-modelos-y-qué-son-las-migraciones)).

## `GetDate()` y su equivalente en Django

`GETDATE()` en SQL Server regresa la fecha/hora actual **del servidor de base de
datos** — se usa directo en un `INSERT`/`UPDATE` para no tener que calcular la fecha
desde la aplicación:

```sql
INSERT INTO Clientes (ID, Nombre, Email, FechaRegistro)
VALUES (1, 'Juan Pérez', 'juan.perez@example.com', GETDATE());
```

En Django, el equivalente es `timezone.now()` (calculado en Python, no en el motor
de base de datos) — que es exactamente lo que usamos como `default` en
`Guia.createdAt` y dentro de nuestro propio campo `AutoDateTimeField` (ver
[shipments/models.py](../shipments/models.py) y
[docs/14](14-modelos-y-migraciones.md#señales-signals)). La diferencia de fondo:
`GETDATE()` se resuelve en el servidor de la base de datos en el momento exacto del
`INSERT`; `timezone.now()` se resuelve en tu aplicación Python, justo antes de
mandarle el valor ya calculado a la base de datos — con Django casi siempre usamos
la segunda opción, porque mantiene la lógica de fechas centralizada en el código,
no repartida entre la app y el motor de base de datos.

---

## Autoevaluación (Módulo 69)

1. **¿Qué es SQL Server y por qué importa?**
   DBMS relacional de Microsoft, para crear/manipular/gestionar bases de datos y
   ejecutar consultas complejas sobre grandes volúmenes de datos.

2. **¿Cómo se crea una tabla?**
   Con `CREATE TABLE nombre (columna TIPO, ...)`, definiendo columnas y tipos de
   dato — el mismo resultado que genera Django a partir de un modelo. → [CREATE TABLE](#create-table-lo-que-ya-generó-nuestra-migración)

3. **¿Qué considerar al insertar datos?**
   Que los valores correspondan al tipo de cada columna, y usar funciones como
   `GetDate()` para fechas automáticas en vez de escribirlas a mano. → [INSERT](#insert-crear-una-fila)

4. **¿Cómo se actualizan registros?**
   Con `UPDATE tabla SET columna = valor WHERE condición` — el `WHERE` es lo que
   evita modificar toda la tabla por accidente. → [UPDATE](#update-modificar-filas-existentes)

5. **¿Diferencias entre `DROP`, `DELETE` y `TRUNCATE`?**
   `DELETE` borra filas específicas (con `WHERE`); `TRUNCATE` vacía la tabla
   completa de un golpe pero la conserva; `DROP` elimina la tabla entera, estructura
   incluida. → [DELETE vs TRUNCATE vs DROP](#delete-vs-truncate-vs-drop-la-diferencia-que-importa)

6. **¿Cómo se modifica la estructura de una tabla existente?**
   Con `ALTER TABLE` (agregar/modificar/quitar columnas) — lo que genera cada
   migración de Django que no sea la inicial. → [ALTER](#alter-modificar-una-tabla-existente)

7. **¿Qué prácticas se recomiendan al trabajar con tablas?**
   Convenciones de nomenclatura consistentes, probar en desarrollo antes de
   producción, y entender bien cada comando antes de ejecutarlo contra datos reales.

8. **¿Por qué practicar la gestión de tablas?**
   Para ganar soltura real con los comandos y herramientas, y evitar errores
   costosos (como un `UPDATE`/`DELETE` sin `WHERE`) cuando ya se trabaja con datos
   de producción.

9. **¿Qué herramientas facilitan insertar datos?**
   SQL Server Management Studio, con interfaz gráfica para insertar/editar filas sin
   escribir cada `INSERT` a mano.

10. **¿Cómo manejar errores comunes al crear tablas?**
    Revisar sintaxis de `CREATE TABLE`, confirmar tipos de dato correctos, seguir
    convenciones de nombres, y probar en un entorno de desarrollo antes de aplicar
    cambios reales.

## Ejemplo de uso en el mercado laboral

- **Logística**: `UPDATE` sobre inventario para reflejar existencias actuales —
  exactamente el tipo de operación que hace `actualizar-guia` en este proyecto, pero
  sobre un estatus de envío en vez de un nivel de stock.
- **Telecomunicaciones**: `UPDATE` sobre registros de clientes para mantener datos
  de contacto vigentes, siempre con `WHERE` acotando a un cliente específico.
