# 32 — GROUP BY, HAVING y funciones de ventana en SQL (Módulo 71 de la plataforma)

Temas: `GROUP BY` con funciones de agregación, `HAVING` (el `WHERE` de los datos ya
agrupados), y las funciones de ventana (`OVER`, `PARTITION BY`, `ROW_NUMBER`,
`RANK`, `DENSE_RANK`). Es el módulo que da el salto de "consultar filas individuales"
(lo que hacíamos en [docs/29](29-sql-basico-crud.md) y
[docs/30](30-sql-select-llaves-null.md)) a **resumir y analizar** conjuntos
completos de datos.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **Cláusula GROUP BY** | Resume filas en grupos, para aplicar funciones de agregación | [GROUP BY: resumir datos](#group-by-resumir-datos) |
| **Cláusula HAVING** | Filtra grupos ya agregados (lo que `WHERE` no puede hacer) | [HAVING: el WHERE de los grupos](#having-el-where-de-los-grupos) |
| **Cláusula OVER** | Convierte una función de agregación en función de ventana | [Funciones de ventana: OVER](#funciones-de-ventana-over) |
| **Función Dense Rank** | Rango con secuencia continua, sin saltos tras un empate | [RANK vs DENSE_RANK vs ROW_NUMBER](#rank-vs-dense_rank-vs-row_number) |
| **Función Rank** | Rango que salta números después de un empate | [RANK vs DENSE_RANK vs ROW_NUMBER](#rank-vs-dense_rank-vs-row_number) |
| **Función Row Number** | Numeración secuencial única, sin importar empates | [RANK vs DENSE_RANK vs ROW_NUMBER](#rank-vs-dense_rank-vs-row_number) |
| **Función de ventana** | Cálculo sobre un grupo de filas relacionadas, sin colapsarlas en una sola | [Funciones de ventana: OVER](#funciones-de-ventana-over) |
| **Partición de datos** | División de un conjunto de datos en partes para calcular por separado | [PARTITION BY: particionar antes de calcular](#partition-by-particionar-antes-de-calcular) |
| **Subcláusula PARTITION BY** | Define cómo se particionan los datos antes de una función de ventana | [PARTITION BY: particionar antes de calcular](#partition-by-particionar-antes-de-calcular) |
| **SQL Management Studio** | Herramienta gráfica para SQL Server | Ya cubierto en [docs/28](28-fundamentos-bases-de-datos.md#ide-vs-herramienta-de-base-de-datos) |

---

## `GROUP BY`: resumir datos

`GROUP BY` colapsa muchas filas en una por cada valor distinto de la columna que
agrupas, para aplicar funciones de agregación (`SUM`, `COUNT`, `MIN`, `MAX`, `AVG`)
sobre cada grupo:

```sql
SELECT
    vendedor_id,
    SUM(ventas) AS total_ventas
FROM ventas
GROUP BY vendedor_id;
```

Por cada `vendedor_id` distinto, esta consulta regresa **una sola fila** con la suma
de todas sus ventas — sin `GROUP BY`, `SUM(ventas)` sumaría **todas** las filas de la
tabla en un solo número, sin distinguir por vendedor.

**Aplicado a Hound Express**: si quisiéramos saber cuántos eventos de estatus tiene
cada guía, sería:

```sql
SELECT guideId, COUNT(*) AS total_eventos
FROM StatusHistory
GROUP BY guideId;
```

El equivalente en el ORM de Django es `.values('guideId').annotate(total=Count('id'))`
— `.values()` define por qué campo agrupar, y `.annotate()` aplica la función de
agregación, siguiendo la misma lógica que ya vimos con `.aggregate()` en
[docs/19](19-ajax-charts-y-order-manager.md#los-métodos-reales-de-ordermanager) (la
diferencia: `.aggregate()` colapsa **todo** el queryset en un solo resultado;
`.annotate()` agrupa y regresa **una fila por grupo**, como el `GROUP BY` de arriba).

## `HAVING`: el `WHERE` de los grupos

`WHERE` filtra **antes** de agrupar (fila por fila); `HAVING` filtra **después**,
sobre el resultado ya agregado — por eso `HAVING` puede usar el resultado de una
función de agregación, y `WHERE` no:

```sql
SELECT vendedor_id, SUM(ventas) AS total_ventas
FROM ventas
GROUP BY vendedor_id
HAVING SUM(ventas) > 100000;
```

Esto sería un error si lo escribieras con `WHERE`:

```sql
SELECT vendedor_id, SUM(ventas) AS total_ventas
FROM ventas
WHERE SUM(ventas) > 100000    -- ERROR: WHERE no puede evaluar funciones de agregación
GROUP BY vendedor_id;
```

`WHERE` se evalúa fila por fila, antes de que exista ningún grupo — en ese momento
`SUM(ventas)` todavía no tiene sentido, porque no sabe a qué grupo pertenece esa
fila. Regla práctica: si el filtro es sobre una columna cruda → `WHERE`; si el
filtro es sobre el resultado de `SUM`/`COUNT`/`AVG`/etc. → `HAVING`.

## Funciones de ventana: `OVER`

Una función de agregación normal **colapsa** filas en una sola (`GROUP BY` reduce
100 filas a 5, una por grupo). Una **función de ventana** calcula algo agregado
**sin perder el detalle** de cada fila individual — cada fila conserva su propia
información, más una columna extra con el cálculo:

```sql
SELECT
    OrderID,
    CustomerID,
    Amount,
    SUM(Amount) OVER (PARTITION BY CustomerID) AS TotalPorCliente
FROM Orders;
```

Aquí **no** desaparece ninguna fila de `Orders` — cada orden individual sigue
apareciendo, pero con una columna adicional que muestra el total acumulado de **su**
cliente. Es justo el ejemplo que menciona el resumen del módulo: "calcular el monto
total de órdenes por cliente mientras se mantiene el detalle de cada transacción" —
algo que `GROUP BY` no puede hacer (con `GROUP BY` perderías el detalle de
`OrderID`/`Amount` de cada orden individual, quedándote solo con el total).

## `PARTITION BY`: particionar antes de calcular

`PARTITION BY`, dentro de un `OVER(...)`, es lo que le dice a la función de ventana
**cómo dividir** los datos antes de calcular — es al `OVER` lo que `GROUP BY` es a
una agregación normal, pero sin colapsar filas:

```sql
SELECT
    vendedor_id,
    SUM(ventas) AS total_ventas,
    RANK() OVER (ORDER BY SUM(ventas) DESC) AS rank_ventas
FROM ventas
GROUP BY vendedor_id;
```

- **`SELECT`**: trae `vendedor_id`, `total_ventas` y `rank_ventas`.
- **`SUM(ventas) AS total_ventas`**: suma total de ventas por vendedor (esto sí
  agrega gracias al `GROUP BY` de más abajo).
- **`RANK() OVER (ORDER BY SUM(ventas) DESC)`**: le asigna un lugar (1º, 2º, 3º...)
  a cada vendedor según su total de ventas, de mayor a menor — sin este `OVER`,
  tendrías que calcular el ranking tú mismo comparando filas manualmente.
- **`GROUP BY vendedor_id`**: agrupa las filas originales para poder calcular
  `SUM(ventas)` por cada vendedor.

Sin `PARTITION BY` (como en este ejemplo), la ventana es **toda la tabla** — el
ranking compara a todos los vendedores entre sí. Si agregáramos
`PARTITION BY region`, cada región tendría su propio ranking independiente (el
vendedor #1 de cada región, no un solo #1 global) — exactamente la idea de
"partición de datos" del glosario: dividir el conjunto en partes más pequeñas para
calcular dentro de cada una por separado.

## `RANK` vs `DENSE_RANK` vs `ROW_NUMBER`

Las 3 numeran filas dentro de una ventana (`OVER`, con o sin `PARTITION BY`), pero
manejan los empates de forma distinta:

| Función | Ventas: 100, 100, 80, 50 → | Comportamiento con empates |
|---------|-------------------------------|--------------------------------|
| `ROW_NUMBER()` | 1, 2, 3, 4 | Nunca hay empates — siempre números únicos y consecutivos, sin importar valores iguales |
| `RANK()` | 1, 1, 3, 4 | Empate = mismo número; **salta** el/los siguientes (el 2 desaparece) |
| `DENSE_RANK()` | 1, 1, 2, 3 | Empate = mismo número; **no salta** — la secuencia sigue continua |

```sql
SELECT
    vendedor_id,
    ventas,
    ROW_NUMBER() OVER (ORDER BY ventas DESC) AS fila,
    RANK()       OVER (ORDER BY ventas DESC) AS rango,
    DENSE_RANK() OVER (ORDER BY ventas DESC) AS rango_denso
FROM ventas;
```

**Cuándo usar cada una**: `ROW_NUMBER()` cuando necesitas un identificador único sin
importar empates (por ejemplo, para paginar resultados — algo parecido, en espíritu,
al `CursorPagination` que vimos en [docs/24](24-paginacion-y-seguridad-drf.md#cursorpagination),
aunque son mecanismos distintos). `RANK()` cuando un empate real debe "costar"
posiciones (dos vendedores en 1er lugar significa que el siguiente es 3º, no 2º).
`DENSE_RANK()` cuando quieres saber cuántos **niveles** distintos de valor existen,
sin huecos en la numeración (útil para, por ejemplo, "top 3 niveles de venta",
donde varios vendedores pueden compartir el nivel 1).

---

## Autoevaluación (Módulo 71)

1. **¿Qué es el agrupamiento de datos en SQL?**
   Usar `GROUP BY` para resumir filas en grupos, aplicando funciones de agregación
   (`SUM`, `COUNT`, `MIN`, `MAX`, `AVG`) sobre cada grupo. → [GROUP BY](#group-by-resumir-datos)

2. **¿Cómo se utilizan las funciones de agregación?**
   Calculan un único valor a partir de un conjunto de filas — normalmente
   combinadas con `GROUP BY` para obtener ese valor por cada grupo distinto.

3. **¿Diferencia entre `WHERE` y `HAVING`?**
   `WHERE` filtra filas individuales antes de agrupar; `HAVING` filtra grupos ya
   agregados, permitiendo condiciones sobre el resultado de una función de
   agregación. → [HAVING](#having-el-where-de-los-grupos)

4. **¿Qué es `PARTITION BY` y cómo se usa?**
   Divide los datos en particiones dentro de una función de ventana, calculando de
   forma independiente en cada una sin perder el detalle de cada fila. → [PARTITION BY](#partition-by-particionar-antes-de-calcular)

5. **¿Cómo funciona `ROW_NUMBER`?**
   Asigna un número secuencial único a cada fila de la ventana, sin saltos ni
   repeticiones, sin importar si hay valores empatados. → [RANK vs DENSE_RANK vs ROW_NUMBER](#rank-vs-dense_rank-vs-row_number)

6. **¿Diferencias entre `RANK` y `DENSE_RANK`?**
   Ambas repiten número en empates; `RANK` salta números después (deja huecos),
   `DENSE_RANK` mantiene la secuencia continua sin saltos. → [RANK vs DENSE_RANK vs ROW_NUMBER](#rank-vs-dense_rank-vs-row_number)

7. **¿Por qué importa practicar agrupamiento y particionamiento?**
   Son la base de cualquier análisis de datos real — consolidar lo aprendido para
   aplicarlo en reportes y decisiones de negocio genuinas, no solo ejercicios.

8. **¿Cómo se identifican tendencias con SQL?**
   Agrupando datos para evitar repeticiones y ordenando los resultados — por
   ejemplo, `GROUP BY` + `COUNT` + `ORDER BY` para encontrar el puesto con más
   empleados en una organización.

9. **¿Qué beneficios dan las funciones de ventana?**
   Cálculos agregados (totales, rankings) **sin perder el detalle** de cada fila —
   algo que `GROUP BY` solo no puede hacer, porque colapsa las filas. → [Funciones de ventana: OVER](#funciones-de-ventana-over)

10. **¿Cómo se numeran órdenes de un cliente por fecha?**
    Con `ROW_NUMBER() OVER (PARTITION BY CustomerID ORDER BY OrderDate)` — numera
    cada orden dentro de su propio cliente, en el orden en que se hicieron.

## Ejemplo de uso en el mercado laboral

- **Análisis de ventas por región**: `GROUP BY` + funciones de agregación para
  resumir ventas, identificando tendencias y regiones con bajo desempeño.
- **Ranking de productos más vendidos**: `RANK()`/`DENSE_RANK()` para ordenar
  productos por ventas, enfocando estrategias de marketing en los más populares.
