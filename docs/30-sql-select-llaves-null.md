# 30 — SELECT, llaves, NULL y las categorías de comandos SQL (Módulo 68 de la plataforma)

Temas: `SELECT`/`WHERE`/`ORDER BY`, llave primaria vs llave foránea, `NULL`, Esquema,
y cómo se clasifican **todos** los comandos SQL que ya vimos en
[docs/29](29-sql-basico-crud.md) dentro de las categorías DDL/DML/TCL (y DCL). Este
módulo es, en cierto sentido, anterior en concepto a `docs/29` — aquí se sientan las
bases que ese documento ya daba por conocidas.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **Adventure Works** | Base de datos de ejemplo de Microsoft | Ya cubierto en [docs/28](28-fundamentos-bases-de-datos.md#bases-de-datos-de-ejemplo-el-rol-de-adventure-works) |
| **DDL** | Comandos que definen/modifican la estructura (tablas, etc.) | [Las 4 categorías de comandos SQL](#las-4-categorías-de-comandos-sql) |
| **DML** | Comandos que manipulan los datos dentro de las tablas | [Las 4 categorías de comandos SQL](#las-4-categorías-de-comandos-sql) |
| **Esquema** | Agrupa tablas/vistas para organizar la base y sus permisos | [Esquema: organizar tablas en grupos](#esquema-organizar-tablas-en-grupos) |
| **Llave foránea** | Campo que referencia la llave primaria de otra tabla | [Llave primaria vs llave foránea](#llave-primaria-vs-llave-foránea) |
| **Llave primaria** | Identifica de forma única cada fila de una tabla | [Llave primaria vs llave foránea](#llave-primaria-vs-llave-foránea) |
| **NULL** | Representa "sin valor" — no es lo mismo que vacío o cero | [NULL: la ausencia de un valor](#null-la-ausencia-de-un-valor) |
| **Result Set** | El conjunto de filas que devuelve un `SELECT` | [SELECT, WHERE y ORDER BY](#select-where-y-order-by) |
| **SQL Server Management Studio** | Herramienta gráfica para administrar SQL Server | Ya cubierto en [docs/28](28-fundamentos-bases-de-datos.md#ide-vs-herramienta-de-base-de-datos) |
| **TCL** | Comandos que controlan transacciones (`COMMIT`, `ROLLBACK`) | [Las 4 categorías de comandos SQL](#las-4-categorías-de-comandos-sql) |

---

## `SELECT`, `WHERE` y `ORDER BY`

El comando más usado de todo SQL — trae datos de una tabla, sin modificarlos:

```sql
SELECT * FROM Productos WHERE Categoria = 'Electrónica';
SELECT * FROM Productos ORDER BY Precio ASC;
```

- **`SELECT *`**: trae todas las columnas. En la práctica, casi siempre conviene
  nombrar las columnas que de verdad necesitas (`SELECT Nombre, Precio FROM
  Productos`) — traer columnas de más cuesta ancho de banda y memoria sin razón,
  sobre todo en tablas grandes.
- **`WHERE`**: ya lo vimos en [docs/29](29-sql-basico-crud.md#where-la-cláusula-que-evita-desastres)
  para `UPDATE`/`DELETE` — en un `SELECT` funciona igual, filtrando qué filas
  aparecen en el resultado.
- **`ORDER BY columna ASC|DESC`**: ordena el resultado — `ASC` (ascendente) es el
  default si no pones nada. Equivalente exacto al `.order_by('precio')` /
  `.order_by('-precio')` del ORM de Django que ya vimos en
  [docs/14](14-modelos-y-migraciones.md#querysets).

**Result Set** es, literalmente, el nombre técnico de "lo que te regresa un
`SELECT`" — una tabla temporal en memoria con las filas y columnas que pediste. Cada
vez que en Django hacemos `Guia.objects.filter(currentStatus='delivered')`, el
`QuerySet` que regresa es la versión "ORM" de un result set — de hecho, así se llama
literalmente la clase que Django usa por debajo (`QuerySet`), evaluada de forma
perezosa como ya vimos en [docs/14](14-modelos-y-migraciones.md#querysets).

## Llave primaria vs llave foránea

Ya usamos ambas extensamente en este proyecto sin pararnos a definirlas con
precisión de libro de texto:

- **Llave primaria** (*primary key*): identifica de forma única cada fila — no puede
  repetirse ni estar vacía. En `Guia`, es el campo `id` (`models.IntegerField(primary_key=True)`,
  ver [docs/14](14-modelos-y-migraciones.md#opciones-de-campo-más-importantes)).
- **Llave foránea** (*foreign key*): un campo que **apunta** a la llave primaria de
  otra tabla, creando la relación entre ambas. Django lo modela con `ForeignKey` —
  como vimos con `Order.billing_profile` en
  [docs/17](17-ordenes-facturacion-y-senales.md#foreignkey-en-un-caso-real-order--billingprofile).

**El detalle que sigue siendo importante repetir de este proyecto**: `Estatus.guideId`
**no** es una llave foránea real a nivel de base de datos — es un `IntegerField`
suelto que *funciona como si lo fuera* a nivel de lógica de negocio, pero sin que
SQL Server (o SQLite, en nuestro caso) sepa ni imponga esa relación. Si fuera una
llave foránea real, la base de datos rechazaría automáticamente crear un `Estatus`
con un `guideId` que no exista en `Guide` — hoy, sin ella, esa validación no existe a
nivel de base de datos (habría que hacerla a mano en el serializer, si se quisiera).

## `NULL`: la ausencia de un valor

`NULL` no es lo mismo que `0`, `""` (cadena vacía), o `'N'` — es "no sé", "no
aplica", o "no se guardó nada aquí". Por eso las comparaciones normales
(`=`, `<>`) **no funcionan** con `NULL`:

```sql
SELECT * FROM Ordenes WHERE Observaciones = NULL;     -- ¡nunca regresa nada, aunque haya filas con NULL!
SELECT * FROM Ordenes WHERE Observaciones IS NULL;    -- correcto
SELECT * FROM Ordenes WHERE Observaciones IS NOT NULL; -- correcto
```

`NULL = NULL` no es verdadero en SQL — es "desconocido", así que hace falta el
operador especial `IS NULL`/`IS NOT NULL`. Esto es exactamente lo que ya explicamos
en Django con `null=True` en [docs/14](14-modelos-y-migraciones.md#opciones-de-campo-más-importantes):
esa opción controla si la columna en la base de datos **acepta** `NULL` — y por eso
recomendamos ahí mismo no usar `null=True` en campos de texto (se prefiere `""`
antes que `NULL`, precisamente para evitar tener que lidiar con `IS NULL` en cada
consulta).

## Esquema: organizar tablas en grupos

Un **esquema** (*schema*, en el sentido de SQL Server) es una forma de agrupar
tablas/vistas dentro de una misma base de datos — por ejemplo, separar `ventas.Ordenes`
de `inventario.Productos` dentro de la misma base, facilitando permisos por grupo
(el equipo de ventas solo ve el esquema `ventas`). Es un nivel de organización
**dentro** de una sola base de datos — distinto de separar en bases de datos
completamente aparte. Django no expone este concepto directamente (todas las tablas
de nuestras apps viven en el mismo "esquema" default de SQLite), pero el paralelo
más cercano que ya conocemos es cómo organizamos **apps** (`shipments`) para agrupar
modelos relacionados — incluso el nombre de tabla que generamos manualmente
(`db_table = 'Guide'`, ver [docs/13](13-vistas-crud-y-consultas.md)) podría, en
SQL Server, ir prefijado por un esquema (`dbo.Guide`, `ventas.Guide`, etc.).

## Las 4 categorías de comandos SQL

Todo comando SQL que ya usamos en [docs/29](29-sql-basico-crud.md) cae en una de
estas 4 categorías:

| Categoría | Qué hace | Comandos | Ya los vimos en |
|-----------|-----------|------------|--------------------|
| **DDL** (*Data Definition Language*) | Define/modifica la **estructura** | `CREATE`, `ALTER`, `DROP` | [docs/29](29-sql-basico-crud.md#create-table-lo-que-ya-generó-nuestra-migración) |
| **DML** (*Data Manipulation Language*) | Manipula los **datos** dentro de las tablas | `SELECT`, `INSERT`, `UPDATE`, `DELETE` | [docs/29](29-sql-basico-crud.md#insert-crear-una-fila) |
| **DCL** (*Data Control Language*) | Controla **permisos/acceso** | `GRANT`, `REVOKE` | No cubierto todavía en este proyecto |
| **TCL** (*Transaction Control Language*) | Controla **transacciones** (agrupar varios comandos como una sola unidad, todo o nada) | `COMMIT`, `ROLLBACK`, `BEGIN TRANSACTION` | No cubierto todavía en este proyecto |

`TCL` es nuevo hasta este módulo, y vale la pena entenderlo bien: una **transacción**
agrupa varios comandos SQL para que se apliquen **todos o ninguno** — si a mitad de
crear un `Estatus` y actualizar el `Guia` correspondiente algo falla, una
transacción evita que quede la mitad del trabajo hecho a medias. Django ya maneja
esto por ti en gran parte (cada `.save()` va en su propia transacción implícita), y
lo expone explícitamente vía `transaction.atomic()` para agrupar varias operaciones
del ORM en una sola transacción — algo que no hemos necesitado en este proyecto
porque cada una de nuestras operaciones (crear una guía, registrar un estatus) es
independiente por diseño, pero sería la herramienta correcta si, por ejemplo,
quisiéramos que "crear una guía + su primer estatus" fuera atómico (todo o nada).

---

## Autoevaluación (Módulo 68)

1. **¿Qué es una base de datos relacional?**
   Organiza datos en tablas interconectadas por llaves primarias/foráneas — la base
   de todo lo que hemos construido en Hound Express.

2. **¿Qué son las llaves primarias y foráneas?**
   Primaria: identifica de forma única cada fila. Foránea: conecta una tabla con la
   llave primaria de otra. → [Llave primaria vs llave foránea](#llave-primaria-vs-llave-foránea)

3. **¿Qué es un esquema en una base de datos?**
   Agrupación de tablas/vistas dentro de una base, para organización y permisos. → [Esquema](#esquema-organizar-tablas-en-grupos)

4. **¿Cuáles son los tipos de datos más comunes en SQL?**
   Numéricos, de cadena (texto), de fecha, binarios y especiales — cada motor
   (SQLite, SQL Server, PostgreSQL) los nombra un poco distinto, aunque resuelven lo
   mismo.

5. **¿Qué son DDL, DML, DCL y TCL?**
   Las 4 categorías de comandos SQL: definir estructura, manipular datos, controlar
   acceso, y controlar transacciones respectivamente. → [Las 4 categorías de comandos SQL](#las-4-categorías-de-comandos-sql)

6. **¿Cómo se usa `SELECT`?**
   Para extraer datos de una o más tablas, devolviendo un Result Set — el
   equivalente SQL de un `QuerySet` de Django. → [SELECT, WHERE y ORDER BY](#select-where-y-order-by)

7. **¿Para qué sirve `WHERE`?**
   Filtrar qué filas afecta o devuelve un comando — ya visto también en
   `UPDATE`/`DELETE` en [docs/29](29-sql-basico-crud.md#where-la-cláusula-que-evita-desastres).

8. **¿Cómo se manejan los `NULL`?**
   Con `IS NULL`/`IS NOT NULL` — nunca con `= NULL`, porque `NULL` no es igual a
   nada, ni siquiera a sí mismo. → [NULL: la ausencia de un valor](#null-la-ausencia-de-un-valor)

9. **¿Qué hace `ORDER BY`?**
   Ordena el resultado de una consulta, ascendente (`ASC`, default) o descendente
   (`DESC`), por una o varias columnas.

10. **¿Por qué importan las diferencias de tipos de dato entre motores?**
    Al migrar datos entre plataformas (SQLite → PostgreSQL, por ejemplo), un tipo
    que existe en un motor puede no existir igual en otro — hay que mapearlos
    correctamente para no perder precisión ni romper datos.

## Nota práctica: vincular un script `.sql` con una base de datos específica

Un problema común al abrir un archivo `.sql` en SSMS: el script no sabe contra
**qué base de datos** ejecutarse — depende de cuál esté seleccionada en ese momento
en la ventana de consulta, y es fácil correr un script contra la base equivocada sin
darte cuenta. Formas de resolverlo, de más a menos recomendable:

1. **Un `USE` al principio del script** (la más simple y portable):
   ```sql
   USE AdventureWorks2022;
   GO

   SELECT * FROM Person.Person;
   ```
   `USE` cambia la base de datos activa **para el resto del script** — así,
   compartas el archivo con quien lo compartas, siempre se ejecuta contra la base
   correcta sin depender de qué base tenía seleccionada la ventana de SSMS antes de
   abrirlo. `GO` separa "lotes" (*batches*) — en SSMS, es buena práctica ponerlo
   después de un `USE` antes de seguir con el resto del script.
2. **Base de datos predeterminada de la sesión/login**: en SSMS, se configura por
   login (`Propiedades del login → General → Base de datos predeterminada`) — útil
   si *siempre* trabajas contra la misma base, pero no viaja con el archivo `.sql`
   si lo compartes con alguien más.
3. **Organizar por carpetas/proyecto**: agrupar los `.sql` de un mismo proyecto en
   una carpeta (o una "Solución" de SQL Server Data Tools) — ayuda a la organización,
   pero no selecciona la base de datos automáticamente por sí solo.
4. **Scripts de conexión personalizados**: útil en flujos más avanzados (CI/CD,
   herramientas de migración) donde un script previo configura la conexión antes de
   correr el resto — para trabajo manual en SSMS es más de lo que hace falta.

**Ya lo aplicamos**: el script `consultas_adventureworks.sql` (el ejercicio de
`SELECT`/`WHERE`/`ORDER BY`/`BETWEEN` contra AdventureWorks, guardado fuera de este
repo, en la carpeta de ese curso) ahora empieza con `USE AdventureWorks2022;` por
esta misma razón — así, sin importar qué tenías seleccionado antes en SSMS, el
script siempre corre contra la base correcta.

## Ejemplo de uso en el mercado laboral

- **Gestión de inventarios**: llaves primarias/foráneas bien diseñadas garantizan
  que un producto nunca quede "huérfano" de su categoría o proveedor.
- **Análisis de clientes**: `SELECT ... WHERE ... ORDER BY` es, literalmente, la
  base de cualquier reporte de marketing que filtra y ordena datos de clientes para
  campañas segmentadas.
