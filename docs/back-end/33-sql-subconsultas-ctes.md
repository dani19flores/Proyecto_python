# 33 — Subconsultas, CTEs y funciones integradas de SQL (Módulo 72 de la plataforma)

Temas: subconsultas (escalares, con `EXISTS`, correlacionadas), tablas derivadas,
CTEs (`WITH`, incluidos los recursivos), tablas temporales, y las funciones
integradas de SQL Server (matemáticas, de texto, de fecha/hora). Es el módulo que
junta todo lo anterior —`SELECT`, `JOIN`, `GROUP BY`— en consultas de varios
niveles, para resolver preguntas que una sola consulta plana no puede responder.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **CTEs** | Subconsultas con nombre, definidas al inicio, reutilizables en la consulta | [CTEs: subconsultas con nombre](#ctes-subconsultas-con-nombre) |
| **Funciones de Texto** | Manipulan cadenas: mayúsculas, minúsculas, extraer partes | [Funciones de texto](#funciones-de-texto) |
| **Funciones de Tiempo/Fecha** | Obtener/extraer/formatear fechas y horas | [Funciones de fecha y hora](#funciones-de-fecha-y-hora) |
| **Funciones Matemáticas** | Redondeo, valor absoluto, aleatorios, min/max/avg/suma | [Funciones matemáticas](#funciones-matemáticas) |
| **Subconsultas Correlacionadas** | Subconsulta que usa valores de la consulta externa, ejecutada por cada fila | [Subconsulta correlacionada: dependencia por fila](#subconsulta-correlacionada-dependencia-por-fila) |
| **Subconsultas** | Consulta anidada dentro de una consulta principal | [Subconsulta escalar en SELECT](#subconsulta-escalar-en-select-valores-puntuales) |
| **Tablas Derivadas** | Subconsulta usada como si fuera una tabla, dentro del `FROM` | [Tabla derivada: subconsulta en el FROM](#tabla-derivada-subconsulta-en-el-from) |
| **Tablas Temporales** | Tablas que se autodestruyen cuando ya no se utilizan | [Tablas temporales](#tablas-temporales) |

---

## Subconsulta escalar en `SELECT`: valores puntuales

La forma más simple de subconsulta: un `SELECT` anidado que regresa **un solo
valor**, usado como si fuera una columna más — sin alterar la estructura del
`FROM` principal.

```sql
-- Obtener empleados y el promedio general de ventas de la empresa en la misma fila
SELECT
    p.FirstName,
    p.LastName,
    sp.SalesYTD,
    (SELECT AVG(SalesYTD) FROM Sales.SalesPerson) AS AverageCompanySales
FROM Sales.SalesPerson AS sp
INNER JOIN Person.Person AS p
    ON sp.BusinessEntityID = p.BusinessEntityID;
```

La subconsulta `(SELECT AVG(SalesYTD) FROM Sales.SalesPerson)` se ejecuta **una
sola vez** (el promedio de ventas de toda la empresa no cambia fila por fila), y ese
mismo número se repite en cada fila del resultado, junto a las ventas individuales
de cada vendedor — útil para comparar "lo mío" contra "el promedio general" sin
tener que calcular el promedio aparte y pegarlo a mano.

## Subconsulta correlacionada con `EXISTS`: filtros de existencia

`EXISTS` pregunta "¿hay al menos una fila que cumpla esto?" — regresa verdadero o
falso, sin importar **cuántas** filas coincidan. Es la forma correcta de filtrar por
"tiene al menos un registro relacionado" sin el riesgo de un `JOIN` que duplique
filas si hay más de una coincidencia:

```sql
-- Obtener productos que tienen al menos una reseña (Review) registrada
SELECT
    ProductID,
    Name
FROM Production.Product AS p
WHERE EXISTS (
    SELECT 1
    FROM Production.ProductReview AS pr
    WHERE pr.ProductID = p.ProductID
);
```

El `SELECT 1` dentro del `EXISTS` es una convención — no importa **qué** columna
selecciones ahí (podrías poner `SELECT *` o `SELECT ProductID`), porque `EXISTS`
solo verifica si la subconsulta regresó **alguna** fila, nunca usa los valores en
sí. Si en vez de `EXISTS` hubiéramos hecho `INNER JOIN Production.ProductReview`,
un producto con 5 reseñas aparecería **5 veces** en el resultado — con `EXISTS`,
aparece una sola vez, sin importar cuántas reseñas tenga.

## Tabla derivada: subconsulta en el `FROM`

Una tabla derivada es una subconsulta que va dentro del `FROM` (o un `JOIN`), con un
**alias obligatorio** — el resultado se trata como si fuera una tabla más:

```sql
-- Primero calcula la suma de ventas por cliente (tabla derivada) y
-- luego filtra los que gastaron más de $10,000
SELECT
    dt.CustomerID,
    dt.TotalSpent
FROM (
    -- Esta es la Tabla Derivada (se ejecuta 1 sola vez)
    SELECT
        CustomerID,
        SUM(TotalDue) AS TotalSpent
    FROM Sales.SalesOrderHeader
    GROUP BY CustomerID
) AS dt
WHERE dt.TotalSpent > 10000;
```

`dt` es el alias obligatorio de la tabla derivada — sin él, SQL Server marca error,
porque necesita un nombre con el cual referirse a "el resultado de esa subconsulta"
en el resto de la consulta (`dt.CustomerID`, `dt.TotalSpent`). Nota que aquí el
filtro (`TotalSpent > 10000`) va en un `WHERE` normal, no en `HAVING` — porque para
cuando se evalúa, `TotalSpent` ya es una columna calculada de una tabla (la
derivada), no el resultado en vivo de una función de agregación.

## Subconsulta correlacionada: dependencia por fila

Ocurre típicamente en `WHERE`, `HAVING` o el `SELECT` — usa un campo de la consulta
**externa**, así que debe volver a ejecutarse por cada fila que evalúa la consulta
principal:

```sql
-- Buscar las órdenes cuyo total sea mayor al promedio de ventas DE ESE MISMO CLIENTE
SELECT
    soh1.SalesOrderID,
    soh1.CustomerID,
    soh1.TotalDue
FROM Sales.SalesOrderHeader AS soh1
WHERE soh1.TotalDue > (
    -- Subquery Correlacionado (depende de soh1.CustomerID)
    SELECT AVG(soh2.TotalDue)
    FROM Sales.SalesOrderHeader AS soh2
    WHERE soh2.CustomerID = soh1.CustomerID
);
```

Nota el detalle clave: la misma tabla (`Sales.SalesOrderHeader`) aparece **dos
veces**, con dos alias distintos (`soh1` para la consulta externa, `soh2` para la
subconsulta) — necesario porque, de otro modo, SQL no sabría a cuál de las dos
referencias te refieres en `soh2.CustomerID = soh1.CustomerID`. Por cada orden
(`soh1`), la subconsulta (`soh2`) recalcula el promedio **de ese cliente en
particular** — a diferencia de la subconsulta escalar de la primera sección, que
calculaba un solo promedio para toda la tabla.

## CTEs: subconsultas con nombre

Una **CTE** (*Common Table Expression*, con `WITH`) resuelve lo mismo que una tabla
derivada, pero de forma más legible: se define **una vez**, con nombre propio, y
luego se usa en el resto de la consulta como si ya existiera:

```sql
-- Calcular las ventas totales por cliente y luego traer sus datos personales
WITH CustomerSales AS (
    SELECT
        CustomerID,
        SUM(TotalDue) AS TotalSpent
    FROM Sales.SalesOrderHeader
    GROUP BY CustomerID
)
SELECT
    cs.CustomerID,
    p.FirstName,
    p.LastName,
    cs.TotalSpent
FROM CustomerSales AS cs
INNER JOIN Sales.Customer AS c ON cs.CustomerID = c.CustomerID
INNER JOIN Person.Person AS p ON c.PersonID = p.BusinessEntityID
WHERE cs.TotalSpent > 50000;
```

Compárala con la tabla derivada de la sección anterior: aquí, `CustomerSales` está
definida **antes** del `SELECT` principal, y se usa como una tabla más en el
`FROM` — más fácil de leer que anidar la subconsulta ahí mismo, sobre todo cuando
(como aquí) además necesitas dos `JOIN` adicionales para completar la consulta. Si
necesitaras `CustomerSales` **dos veces** en la misma consulta, con una CTE solo
repites el nombre; con una tabla derivada, tendrías que copiar la subconsulta
completa otra vez.

### CTE recursivo: estructuras jerárquicas

Un CTE recursivo se referencia **a sí mismo** — indispensable para navegar
relaciones padre-hijo (jefe → subordinados, categoría → subcategorías) que una
subconsulta normal no puede resolver, porque no sabes de antemano cuántos "niveles"
de profundidad tiene la jerarquía:

```sql
-- Recorrer la jerarquía organizacional de empleados (Jefes y Subordinados)
WITH EmployeeHierarchy AS (
    -- Ancla: el CEO o nivel superior (ManagerID es NULL)
    SELECT
        BusinessEntityID,
        OrganizationNode,
        JobTitle,
        1 AS HierarchyLevel
    FROM HumanResources.Employee
    WHERE OrganizationNode.GetLevel() = 0

    UNION ALL

    -- Miembros recursivos: subordinados
    SELECT
        e.BusinessEntityID,
        e.OrganizationNode,
        e.JobTitle,
        eh.HierarchyLevel + 1
    FROM HumanResources.Employee AS e
    INNER JOIN EmployeeHierarchy AS eh
        ON e.OrganizationNode.GetAncestor(1) = eh.OrganizationNode
)
SELECT
    HierarchyLevel,
    BusinessEntityID,
    JobTitle
FROM EmployeeHierarchy
ORDER BY HierarchyLevel, BusinessEntityID;
```

Un CTE recursivo siempre tiene dos partes unidas por `UNION ALL` (ver
[docs/31](31-sql-joins-union.md#union-vs-union-all)):

1. **La ancla**: el punto de partida, sin recursión — aquí, el empleado en el nivel
   más alto del organigrama (`GetLevel() = 0`, sin jefe).
2. **El miembro recursivo**: hace `JOIN` **contra el propio CTE** (`EmployeeHierarchy`),
   buscando "el siguiente nivel hacia abajo" — se repite automáticamente hasta que
   ya no encuentra más subordinados que agregar, incrementando `HierarchyLevel` en
   cada vuelta.

Esto sería prácticamente imposible con una subconsulta o tabla derivada normal,
porque ninguna de las dos puede "repetirse a sí misma" un número variable de veces
— exactamente el problema que resuelve la recursividad.

## Tablas temporales

Una tabla temporal se crea, se llena, se usa, y se destruye **manualmente o al
cerrar la sesión** — la diferencia entre local y global está en el número de `#`:

```sql
-- Crear la tabla temporal
CREATE TABLE #ProductSales (
    ProductID INT,
    TotalSales INT
);

-- Insertar datos en la tabla temporal
INSERT INTO #ProductSales (ProductID, TotalSales)
SELECT
    ProductID,
    SUM(OrderQty) AS TotalSales
FROM
    Sales.SalesOrderDetail
GROUP BY
    ProductID;

-- Usar la tabla temporal para seleccionar productos con ventas totales superiores a 1000
SELECT
    p.Name,
    ps.TotalSales
FROM
    Production.Product p
JOIN
    #ProductSales ps
ON
    p.ProductID = ps.ProductID
WHERE
    ps.TotalSales > 1000;

-- Eliminar la tabla temporal
DROP TABLE #ProductSales;
```

- **`#ProductSales`** (un `#`): tabla temporal **local** — solo la sesión que la
  creó puede verla, y se destruye sola en cuanto esa sesión se desconecta (el
  `DROP TABLE` explícito de arriba la borra antes, mientras la sesión sigue viva).
- **`##ProductSales`** (dos `#`): tabla temporal **global** — cualquier sesión
  conectada puede verla y usarla; se destruye hasta que **todas** las sesiones que
  la referencian se desconectan.

Es el mismo patrón que ya vimos conceptualmente en
[docs/29](29-sql-basico-crud.md#delete-vs-truncate-vs-drop-la-diferencia-que-importa)
con `DROP TABLE` — aquí simplemente ocurre sobre una tabla pensada desde el inicio
para ser desechable, en vez de una tabla permanente del esquema.

## Funciones matemáticas

| Función | Qué hace |
|---------|-----------|
| `ROUND(numero, decimales)` | Redondea al número de decimales indicado |
| `ABS(numero)` | Valor absoluto (quita el signo negativo) |
| `RAND()` | Número pseudo-aleatorio entre 0 y 1 |
| `CEILING(numero)` | Redondea hacia **arriba**, al siguiente entero |
| `FLOOR(numero)` | Redondea hacia **abajo**, al entero inferior |
| `MAX(campo)` / `MIN(campo)` | Valor máximo/mínimo de un conjunto |
| `AVG(campo)` | Promedio |
| `SUM(campo)` | Suma total |

`CEILING`/`FLOOR` son fáciles de confundir por nombre: `CEILING(4.2)` da `5`
(sube), `FLOOR(4.8)` da `4` (baja) — a diferencia de `ROUND`, que redondea al más
cercano según las reglas normales de redondeo, no siempre hacia el mismo lado.

## Funciones de texto

| Función | Qué hace |
|---------|-----------|
| `LEN(texto)` | Cuenta los caracteres de una cadena |
| `UPPER(texto)` / `LOWER(texto)` | Convierte a mayúsculas/minúsculas |
| `TRIM(texto)` | Quita espacios de **ambos** lados |
| `LTRIM(texto)` / `RTRIM(texto)` | Quita espacios solo del lado izquierdo/derecho |
| `LEFT(texto, n)` / `RIGHT(texto, n)` | Extrae `n` caracteres desde la izquierda/derecha |
| `SUBSTRING(texto, inicio, longitud)` | Extrae caracteres desde una posición, una cantidad dada |

```sql
SELECT
    trackingNumber,
    LEFT(trackingNumber, 2) AS prefijo,        -- 'HE'
    SUBSTRING(trackingNumber, 3, 10) AS folio    -- el resto del código
FROM Guide;
```

Ya vimos el equivalente Python de varias de estas en
[docs/26](26-web-scraping.md#limpiar-y-convertir-datos-extraídos) (limpiar texto
extraído con `.replace()`) — `nombre.upper()`, `nombre.strip()`,
`nombre[:2]` (slicing) son las versiones Python de `UPPER`, `TRIM` y `LEFT`
respectivamente.

## Funciones de fecha y hora

| Función | Qué hace |
|---------|-----------|
| `GETDATE()` | Fecha y hora actuales del servidor (ver [docs/29](29-sql-basico-crud.md#getdate-y-su-equivalente-en-django)) |
| `YEAR(fecha)` / `MONTH(fecha)` / `DAY(fecha)` | Extrae el año/mes/día de una fecha |
| `DATEPART(HOUR, fecha)` / `DATEPART(MINUTE, fecha)` / `DATEPART(SECOND, fecha)` | Extrae hora/minuto/segundo |
| `DATENAME(MONTH, fecha)` | El mes **en nombre** (`'January'`) en vez de número |
| `FORMAT(fecha, 'dd/MM/yyyy')` | Formatea la fecha como texto, con el patrón que definas |

```sql
SELECT
    trackingNumber,
    YEAR(createdAt) AS anio,
    DATENAME(MONTH, createdAt) AS mes_nombre,
    FORMAT(createdAt, 'dd/MM/yyyy') AS fecha_formateada
FROM Guide;
```

El equivalente Python/Django de `YEAR`/`MONTH`/`DAY` son los atributos
`.year`/`.month`/`.day` de un objeto `datetime` (o, dentro de un `QuerySet`, las
funciones `django.db.models.functions.ExtractYear`/`ExtractMonth`); `FORMAT` es
`strftime('%d/%m/%Y')` en Python puro.

---

## Autoevaluación (Módulo 72)

1. **¿Qué son las subconsultas en SQL?**
   Consultas anidadas dentro de una consulta principal, usadas en `SELECT`,
   `INSERT`, `DELETE` y `UPDATE` para delimitar los datos obtenidos. → [Subconsulta escalar en SELECT](#subconsulta-escalar-en-select-valores-puntuales)

2. **¿Cómo funcionan las subconsultas correlacionadas?**
   Usan valores de la consulta externa dentro de su `WHERE`, ejecutándose una vez
   por cada fila de la consulta principal. → [Subconsulta correlacionada](#subconsulta-correlacionada-dependencia-por-fila)

3. **¿Qué son las tablas derivadas y cómo se utilizan?**
   Subconsultas usadas como tabla dentro del `FROM`, con alias obligatorio, para
   organizar y simplificar consultas complejas. → [Tabla derivada](#tabla-derivada-subconsulta-en-el-from)

4. **¿Qué son los CTEs y qué ventajas tienen?**
   Subconsultas con nombre, definidas al inicio con `WITH`, reutilizables varias
   veces — incluyen la variante recursiva, para jerarquías padre-hijo. → [CTEs](#ctes-subconsultas-con-nombre)

5. **¿Qué son las tablas temporales?**
   Tablas que se autodestruyen al terminar de usarse — locales (`#`, por sesión) o
   globales (`##`, hasta que todas las sesiones se desconecten). → [Tablas temporales](#tablas-temporales)

6. **¿Qué funciones matemáticas ofrece SQL Server?**
   `ROUND`, `ABS`, `RAND`, `CEILING`, `FLOOR`, y `MIN`/`MAX`/`AVG`/`SUM` para
   cálculos numéricos directo en la consulta. → [Funciones matemáticas](#funciones-matemáticas)

7. **¿Cómo se manipulan cadenas de texto?**
   Con `UPPER`/`LOWER`, `TRIM`/`LTRIM`/`RTRIM`, `LEFT`/`RIGHT` y `SUBSTRING` para
   extraer y transformar partes de una cadena. → [Funciones de texto](#funciones-de-texto)

8. **¿Qué funciones de fecha/hora existen?**
   `GETDATE()`, `YEAR`/`MONTH`/`DAY`, extraer hora/minuto/segundo, el nombre del
   mes, y `FORMAT` para darle el formato de texto que necesites. → [Funciones de fecha y hora](#funciones-de-fecha-y-hora)

9. **¿Por qué importan las técnicas avanzadas de SQL?**
   Permiten análisis más complejos y eficientes directo en la base de datos, sin
   depender de traer todo el dato crudo a la aplicación para procesarlo ahí.

10. **¿Cómo mejoran el análisis de datos?**
    Subconsultas, CTEs y funciones integradas permiten manipular grandes volúmenes
    de datos de forma más directa y organizada que encadenar consultas separadas a
    mano.

## Ejemplo de uso en el mercado laboral

- **Reportes financieros**: CTEs para encadenar varios pasos de cálculo de forma
  legible, en vez de anidar subconsultas ilegibles unas dentro de otras.
- **Organigramas y catálogos jerárquicos**: CTEs recursivos para navegar
  estructuras padre-hijo de profundidad variable (empleados y jefes, categorías y
  subcategorías) que una subconsulta normal no puede resolver.
- **Procesos de carga de datos (ETL)**: tablas temporales para pasos intermedios de
  transformación antes de insertar el resultado final en las tablas permanentes.
