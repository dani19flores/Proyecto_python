# 34 — Vistas, procedimientos almacenados y T-SQL (Módulo 73 de la plataforma)

Temas: `Vistas` (`CREATE VIEW`) y vistas materializadas, `T-SQL` (variables y
control de flujo), funciones definidas por el usuario (`UDF`, escalares y de valor
de tabla), procedimientos almacenados (`CREATE PROCEDURE`), y `@@ROWCOUNT`. Este
módulo mueve lógica **hacia adentro** de la base de datos — algo que en este
proyecto casi siempre hacemos del lado de Django, así que es un buen contraste para
entender la diferencia entre las dos filosofías.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **Common Table Expressions (CTE)** | Subconsulta con nombre, vive solo durante la consulta | Ya cubierto en [docs/33](33-sql-subconsultas-ctes.md#ctes-subconsultas-con-nombre) |
| **Funciones de valor de tabla** | UDF que regresa un conjunto de filas, no un solo valor | [UDF: funciones definidas por el usuario](#udf-funciones-definidas-por-el-usuario) |
| **Procedimientos almacenados** | Bloques de código SQL guardados en el servidor, con parámetros | [Procedimientos almacenados](#procedimientos-almacenados) |
| **Transact-SQL (T-SQL)** | Extensión de SQL de Microsoft, con variables y control de flujo | [T-SQL: variables y control de flujo](#t-sql-variables-y-control-de-flujo) |
| **UDF** | Funciones personalizadas para encapsular lógica repetitiva | [UDF: funciones definidas por el usuario](#udf-funciones-definidas-por-el-usuario) |
| **Vistas** | Consulta guardada que actúa como tabla virtual, sin guardar datos | [Vistas: consultas con nombre, permanentes](#vistas-consultas-con-nombre-permanentes) |
| **Vistas materializadas** | Vista que sí guarda los datos físicamente, para más velocidad | [Vistas materializadas: cuando la velocidad importa más que estar al día](#vistas-materializadas-cuando-la-velocidad-importa-más-que-estar-al-día) |
| **@@ROWCOUNT** | Variable global con el número de filas afectadas por el último comando | [@@ROWCOUNT: cuántas filas tocó el último comando](#rowcount-cuántas-filas-tocó-el-último-comando) |

---

## Vistas: consultas con nombre, permanentes

Una vista es, en esencia, una **CTE que se queda guardada** en la base de datos en
vez de vivir solo durante una consulta — se crea una vez, y de ahí en adelante se
consulta como si fuera una tabla más:

```sql
CREATE VIEW TotalVentasPorCliente AS
SELECT ClienteID, SUM(Monto) AS TotalVentas
FROM Ventas
GROUP BY ClienteID;
```

```sql
-- Uso normal, como si fuera una tabla:
SELECT * FROM TotalVentasPorCliente WHERE TotalVentas > 50000;
```

La vista **no almacena datos** — cada vez que la consultas, SQL Server vuelve a
ejecutar el `SELECT` original por debajo. Sirve para encapsular una consulta
compleja (con `JOIN`s, agregaciones, condiciones) detrás de un nombre simple, y
para restringir acceso (dar permiso solo sobre la vista, no sobre las tablas
reales, ocultando columnas sensibles).

**Restricción importante del módulo**: una vista no puede llevar `ORDER BY` a menos
que también uses `TOP` — porque una vista es conceptualmente un **conjunto** de
filas sin orden garantizado, no un reporte final; el orden se decide en la consulta
que **usa** la vista, no en la vista misma.

### Vistas vs CTE vs tablas temporales

Ya cubrimos CTE ([docs/33](33-sql-subconsultas-ctes.md#ctes-subconsultas-con-nombre))
y tablas temporales ([docs/33](33-sql-subconsultas-ctes.md#tablas-temporales)) — los
tres "envuelven" una consulta, pero con alcances muy distintos:

| | Vista | CTE | Tabla temporal |
|---|---|---|---|
| Dónde vive | Guardada permanentemente en la base de datos | Solo dentro de la consulta que la define | Guardada durante la sesión (o hasta el `DROP`) |
| Guarda datos físicos | No (se recalcula cada vez) | No | Sí |
| Reutilizable entre consultas distintas | Sí, cualquiera con permiso puede usarla | No, muere con la consulta | Sí, mientras dure la sesión |
| Se comporta como | Una tabla | Una tabla, solo "por ahora" | Una tabla real, temporal |

## Vistas materializadas: cuando la velocidad importa más que estar al día

Una vista normal se **recalcula** cada vez que la consultas — si la consulta detrás
es pesada (varios `JOIN`, agregaciones sobre millones de filas), eso cuesta tiempo
cada vez. Una **vista materializada** resuelve esto guardando el resultado
**físicamente**, como si fuera una tabla — consultarla es instantáneo, a cambio de
que los datos pueden quedar desactualizados hasta la siguiente actualización
(automática, periódica, o manual).

Es la misma decisión de fondo que ya vimos entre base operativa y **Data Warehouse**
en [docs/28](28-fundamentos-bases-de-datos.md#data-warehouse-vs-data-lake-vs-base-de-datos-operativa):
rapidez de lectura vs qué tan "al momento" están los datos — una vista materializada
es, de hecho, una de las piezas típicas que alimentan un data warehouse.

## T-SQL: variables y control de flujo

T-SQL agrega a SQL lo que le falta a un `SELECT` plano para comportarse como un
lenguaje de programación real — variables, condicionales, ciclos:

```sql
DECLARE @PrecioPromedio DECIMAL(10, 2);

SELECT @PrecioPromedio = AVG(Precio) FROM Productos;

IF @PrecioPromedio > 100
    PRINT 'El precio promedio es alto';
ELSE
    PRINT 'El precio promedio es accesible';
```

- **`DECLARE @nombre TIPO`**: declara una variable — el prefijo `@` es obligatorio
  para cualquier variable en T-SQL.
- **`SET @var = valor`** o **`SELECT @var = columna FROM tabla`**: le asigna un
  valor — `SET` para un valor fijo, `SELECT` cuando el valor viene de una consulta.
- **`IF`/`ELSE`**: control de flujo, igual que en cualquier lenguaje de
  programación — la diferencia frente a Python es que aquí no hay indentación
  obligatoria, cada rama es una sola instrucción (o un bloque `BEGIN...END` si son
  varias).

Este es el punto donde SQL dejar de ser "solo un lenguaje de consultas" y se acerca
a un lenguaje de programación completo — la pieza que hace posibles los
procedimientos almacenados y las UDF de abajo.

## UDF: funciones definidas por el usuario

Encapsulan lógica reutilizable, igual que una función de Python — existen dos
tipos:

**Escalar** (regresa un solo valor):

```sql
CREATE FUNCTION CalcularDescuento (@Precio DECIMAL(10,2), @Porcentaje DECIMAL(5,2))
RETURNS DECIMAL(10,2)
AS
BEGIN
    RETURN @Precio - (@Precio * @Porcentaje / 100);
END;

-- Uso, como cualquier función integrada:
SELECT Nombre, dbo.CalcularDescuento(Precio, 10) AS PrecioConDescuento
FROM Productos;
```

**De valor de tabla** (regresa un conjunto de filas — se usa como si fuera una
tabla, igual que una vista, pero **acepta parámetros**, algo que una vista no
puede):

```sql
CREATE FUNCTION ProductosPorCategoria (@CategoriaID INT)
RETURNS TABLE
AS
RETURN (
    SELECT ProductoID, Nombre, Precio
    FROM Productos
    WHERE CategoriaID = @CategoriaID
);

-- Uso:
SELECT * FROM ProductosPorCategoria(5);
```

Esa es la diferencia práctica clave entre una vista y una función de valor de tabla:
la vista siempre regresa "todo" (tú filtras después con `WHERE`); la función de
valor de tabla recibe un parámetro y decide **desde adentro** qué filas regresar.

## Procedimientos almacenados

A diferencia de una función (que regresa un valor y se usa **dentro** de una
consulta), un procedimiento almacenado se **ejecuta** como una acción independiente
— puede no regresar nada, o regresar varios result sets, y puede modificar datos
(`INSERT`/`UPDATE`/`DELETE`), algo que una función no debería hacer:

```sql
CREATE PROCEDURE ObtenerProductosPorRangoPrecio
    @PrecioMin DECIMAL(10, 2),
    @PrecioMax DECIMAL(10, 2)
AS
BEGIN
    SELECT ProductoID, Nombre, Precio
    FROM Productos
    WHERE Precio BETWEEN @PrecioMin AND @PrecioMax;
END;
```

```sql
-- Ejecutar el procedimiento:
EXEC ObtenerProductosPorRangoPrecio @PrecioMin = 20, @PrecioMax = 100;
```

- **`CREATE PROCEDURE nombre @param1 TIPO, @param2 TIPO AS BEGIN ... END`**: define
  el procedimiento con sus parámetros de **entrada**.
- **`EXEC nombre @param1 = valor, ...`**: lo ejecuta, pasando los valores.
- También existen **parámetros de salida** (`@Resultado INT OUTPUT`), para que el
  procedimiento le devuelva un valor calculado a quien lo llamó, más allá de un
  simple result set.

**Dónde encaja esto frente a lo que ya hacemos en Hound Express**: nuestra lógica
equivalente a `ObtenerProductosPorRangoPrecio` vive del lado de Django, no de la
base de datos — sería un método de vista o del manager, como
`Guia.objects.filter(currentStatus=estatus)` (ver
[docs/19](19-ajax-charts-y-order-manager.md#los-métodos-reales-de-ordermanager)
para el patrón de manager con lógica encapsulada). Un procedimiento almacenado
resuelve el mismo problema (encapsular lógica reutilizable) pero **del lado del
servidor de base de datos** en vez de la aplicación — la ventaja es que corre más
cerca de los datos (útil para lógica pesada que no quieres traer y procesar en la
aplicación); la desventaja es que queda fuera del control de versiones de tu código
Python, en un lugar donde Django/el ORM no la ve ni la gestiona.

## `@@ROWCOUNT`: cuántas filas tocó el último comando

```sql
UPDATE Productos SET Precio = Precio * 1.10 WHERE CategoriaID = 3;

IF @@ROWCOUNT = 0
    PRINT 'Ningún producto fue actualizado';
ELSE
    PRINT CONCAT(@@ROWCOUNT, ' productos actualizados');
```

`@@ROWCOUNT` es una variable **global** (no la declaras tú, ya existe) que se
actualiza automáticamente después de cada instrucción — útil dentro de un
procedimiento almacenado para verificar si un `UPDATE`/`DELETE`/`INSERT` realmente
afectó algo antes de continuar con el resto de la lógica. El equivalente en el ORM
de Django es el valor que regresan `.update()` y `.delete()` — ambos métodos
regresan el número de filas afectadas:

```python
filas_actualizadas = Guia.objects.filter(currentStatus='created').update(currentStatus='picked_up')
if filas_actualizadas == 0:
    print('Ninguna guía fue actualizada')
```

---

## Autoevaluación (Módulo 73)

1. **¿Qué son las vistas y para qué se utilizan?**
   Consultas guardadas que actúan como tablas virtuales, sin almacenar datos
   físicamente — encapsulan lógica compleja y restringen acceso a columnas/filas. → [Vistas](#vistas-consultas-con-nombre-permanentes)

2. **¿Diferencia entre vistas, tablas temporales y CTE?**
   Vista: permanente, sin datos físicos. Tabla temporal: temporal, con datos
   físicos. CTE: vive solo durante una consulta, sin datos físicos. → [Vistas vs CTE vs tablas temporales](#vistas-vs-cte-vs-tablas-temporales)

3. **¿Qué es T-SQL y en qué se diferencia del SQL estándar?**
   Extensión de Microsoft con variables, control de flujo, funciones y
   procedimientos — más allá de lo que cubre el estándar ANSI SQL. → [T-SQL](#t-sql-variables-y-control-de-flujo)

4. **¿Cómo se manejan variables en T-SQL?**
   `DECLARE @variable TIPO` para declarar, `SET`/`SELECT` para asignar un valor.

5. **¿Qué son las UDF?**
   Funciones personalizadas, escalares (un valor) o de valor de tabla (un conjunto
   de filas, con parámetros) — para encapsular lógica repetitiva. → [UDF](#udf-funciones-definidas-por-el-usuario)

6. **¿Cómo se crean y usan procedimientos almacenados?**
   Con `CREATE PROCEDURE nombre @parametros AS BEGIN ... END`, y se ejecutan con
   `EXEC nombre @parametro = valor`. → [Procedimientos almacenados](#procedimientos-almacenados)

7. **¿Qué restricciones tienen las vistas?**
   No pueden llevar `ORDER BY` sin `TOP`, y no siempre se pueden modificar
   directamente si incluyen agregaciones, `JOIN`s complejos o subconsultas.

8. **¿Qué son las vistas materializadas?**
   Vistas que sí guardan físicamente el resultado, para consultas más rápidas a
   cambio de requerir actualizaciones periódicas. → [Vistas materializadas](#vistas-materializadas-cuando-la-velocidad-importa-más-que-estar-al-día)

9. **¿Cómo se usan los parámetros en procedimientos almacenados?**
   Los de entrada reciben valores al ejecutar (`EXEC ... @param = valor`); los de
   salida (`OUTPUT`) devuelven un resultado calculado a quien llamó al procedimiento.

10. **¿Qué es `@@ROWCOUNT` y cómo se usa?**
    Variable global con el número de filas afectadas por la última instrucción —
    útil para verificar si un `UPDATE`/`DELETE`/`INSERT` tocó algo antes de seguir
    con la lógica. → [@@ROWCOUNT](#rowcount-cuántas-filas-tocó-el-último-comando)

## Ejemplo de uso en el mercado laboral

- **Sistemas de inventario**: vistas para simplificar consultas complejas sobre
  múltiples tablas, facilitando el acceso a información crítica del stock.
- **Informes financieros automatizados**: procedimientos almacenados que generan
  reportes de forma consistente y eficiente, sin depender de que cada aplicación
  reimplemente la misma lógica de cálculo por separado.
