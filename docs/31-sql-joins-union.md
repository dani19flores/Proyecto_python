# 31 — JOINs, UNION y funciones condicionales en SQL (Módulo 70 de la plataforma)

Temas: los 5 tipos de `JOIN` (`INNER`, `LEFT`, `RIGHT`, `FULL OUTER`, `CROSS`),
`UNION` vs `UNION ALL`, y las funciones `CASE`/`COALESCE`/`ISNULL`. Este módulo es
la pieza que le faltaba a la teoría de llaves foráneas que ya vimos en
[docs/30](30-sql-select-llaves-null.md#llave-primaria-vs-llave-foránea): una llave
foránea define la *relación*; un `JOIN` es *cómo la usas* para traer datos de ambas
tablas en una sola consulta.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **AdventureWorks** | Base de ejemplo de Microsoft, usada para practicar JOINs | Ya cubierto en [docs/28](28-fundamentos-bases-de-datos.md#bases-de-datos-de-ejemplo-el-rol-de-adventure-works) |
| **CROSS JOIN** | Producto cartesiano: cada fila de A con cada fila de B | [CROSS JOIN: el que casi nunca usas](#cross-join-el-que-casi-nunca-usas) |
| **FULL OUTER JOIN** | Todo de ambas tablas, con `NULL` donde no hay coincidencia | [FULL OUTER JOIN: todo de ambos lados](#full-outer-join-todo-de-ambos-lados) |
| **INNER JOIN** | Solo las filas que coinciden en ambas tablas | [INNER JOIN: el más común](#inner-join-el-más-común) |
| **LEFT JOIN** | Todo de la tabla izquierda + coincidencias de la derecha | [LEFT JOIN y RIGHT JOIN: cuando faltan datos](#left-join-y-right-join-cuando-faltan-datos) |
| **RIGHT JOIN** | Todo de la tabla derecha + coincidencias de la izquierda | [LEFT JOIN y RIGHT JOIN: cuando faltan datos](#left-join-y-right-join-cuando-faltan-datos) |
| **UNION** | Combina resultados de 2+ consultas, quitando duplicados | [UNION vs UNION ALL](#union-vs-union-all) |
| **UNION ALL** | Igual que `UNION`, pero sin quitar duplicados (más rápido) | [UNION vs UNION ALL](#union-vs-union-all) |

---

## `INNER JOIN`: el más común

Trae filas de dos tablas, pero **solo** cuando hay coincidencia en el campo que las
relaciona — si una guía no tiene ningún evento de estatus, o un evento apunta a una
guía que no existe, esa fila simplemente no aparece en el resultado:

```sql
SELECT
    o.OrderID,
    o.OrderDate,
    p.ProductName,
    COALESCE(o.Quantity, 0) AS Quantity
FROM Orders o
INNER JOIN Products p ON o.ProductID = p.ProductID;
```

- **`FROM Orders o`**: la tabla principal, con alias `o` (para no repetir
  `Orders.OrderID` en todo el `SELECT`).
- **`INNER JOIN Products p ON o.ProductID = p.ProductID`**: por cada fila de
  `Orders`, busca la fila de `Products` cuyo `ProductID` coincida — si no hay
  ninguna, esa orden **no sale** en el resultado.

**Aplicado a Hound Express**: si `Estatus.guideId` fuera una llave foránea real
(como discutimos en [docs/30](30-sql-select-llaves-null.md#llave-primaria-vs-llave-foránea)),
un `INNER JOIN` para traer cada evento junto con los datos de su guía se vería así:

```sql
SELECT g.trackingNumber, e.status, e.timestamp
FROM Guide g
INNER JOIN StatusHistory e ON g.id = e.guideId;
```

En el ORM de Django, esto es exactamente lo que hace `select_related()` — ya lo
mencionamos en [docs/14](14-modelos-y-migraciones.md#querysets): en vez de dos
consultas separadas, `select_related('guia')` le pide a Django que arme un
`INNER JOIN` (o `LEFT JOIN`, ver abajo) para traer todo en una sola consulta SQL.
Como nuestro `guideId` no es una FK real, no podemos usar `select_related()` aquí —
por eso en [shipments/views.py](../shipments/views.py) filtramos manualmente
(`Estatus.objects.filter(guideId=guia.id)`) en vez de dejar que el ORM arme el JOIN
por nosotros.

## `LEFT JOIN` y `RIGHT JOIN`: cuando faltan datos

```sql
SELECT g.trackingNumber, e.status
FROM Guide g
LEFT JOIN StatusHistory e ON g.id = e.guideId;
```

`LEFT JOIN` trae **todas** las filas de la tabla izquierda (`Guide`), tengan o no un
evento de estatus asociado — si una guía todavía no tiene ningún `Estatus`,
aparece igual, con `NULL` en las columnas de `StatusHistory`. Es la diferencia clave
frente a `INNER JOIN`: con `INNER JOIN`, esa guía sin eventos **desaparecería** del
resultado por completo.

`RIGHT JOIN` es exactamente lo mismo, pero al revés: todo de la tabla de la
**derecha**, con `NULL` donde no hay coincidencia del lado izquierdo. En la práctica,
casi nadie usa `RIGHT JOIN` — cualquier `RIGHT JOIN` se puede reescribir como un
`LEFT JOIN` intercambiando el orden de las tablas, y la mayoría de los equipos
prefieren esa consistencia ("siempre `LEFT`, nunca `RIGHT`") para que el código sea
más fácil de leer.

**Equivalente en el ORM**: cuando usamos `prefetch_related('status_events')` en una
versión anterior de este proyecto (con `ForeignKey` real, ver
[docs/17](17-ordenes-facturacion-y-senales.md)), el resultado incluye guías **sin**
eventos igual (con una lista vacía en vez de `NULL`) — el mismo espíritu de
`LEFT JOIN`, adaptado a cómo Django representa "cero relacionados" en Python.

## `FULL OUTER JOIN`: todo de ambos lados

```sql
SELECT g.trackingNumber, e.status
FROM Guide g
FULL OUTER JOIN StatusHistory e ON g.id = e.guideId;
```

Combina lo de `LEFT` y `RIGHT`: trae **todas** las filas de ambas tablas, con `NULL`
en cualquier lado donde no haya coincidencia — útil para auditorías, como menciona
el resumen del módulo: encontrar registros de una tabla que no tienen
correspondencia en la otra (guías sin ningún evento, **y** eventos huérfanos
apuntando a guías que ya no existen, en una sola consulta).

**Nota práctica**: SQLite (el motor que usa este proyecto) **no soporta**
`FULL OUTER JOIN` de forma nativa — se simula combinando un `LEFT JOIN` y un
`RIGHT JOIN` con `UNION` (ver abajo). SQL Server sí lo soporta directo, como en el
ejemplo de arriba.

## `CROSS JOIN`: el que casi nunca usas

```sql
SELECT p.ProductName, d.CalendarDate
FROM Products p
CROSS JOIN Calendar d;
```

Combina **cada fila** de una tabla con **cada fila** de la otra — si `Products` tiene
10 filas y `Calendar` tiene 30, el resultado tiene 300 filas (10 × 30). Se usa para
generar combinaciones completas a propósito (como dice el resumen del módulo:
"calcular combinaciones de productos por cada día de un mes") — casi nunca es lo que
quieres por accidente, y un `JOIN` al que se le olvidó el `ON` termina siendo,
sin querer, un `CROSS JOIN`.

## `UNION` vs `UNION ALL`

Mientras los `JOIN` combinan tablas **lado a lado** (más columnas), `UNION` combina
resultados **uno debajo del otro** (más filas) — las consultas deben tener el mismo
número de columnas y tipos compatibles:

```sql
SELECT trackingNumber AS identificador FROM Guide WHERE currentStatus = 'delivered'
UNION
SELECT name AS identificador FROM User WHERE email LIKE '%@empresa.com';
```

- **`UNION`**: junta ambos resultados y **quita duplicados** — internamente hace un
  trabajo extra (ordenar/comparar) para detectar filas repetidas.
- **`UNION ALL`**: junta ambos resultados **sin** quitar duplicados — más rápido,
  porque se salta ese paso. Úsalo siempre que sepas de antemano que no puede haber
  duplicados entre ambas consultas (o que no te importa si los hay).

## `CASE`: lógica condicional dentro de una consulta

```sql
SELECT
    trackingNumber,
    CASE
        WHEN currentStatus = 'delivered' THEN 'Entregado'
        WHEN currentStatus = 'cancelled' THEN 'Cancelado'
        ELSE 'En proceso'
    END AS estatus_amigable
FROM Guide;
```

Es el `if/elif/else` de SQL — evalúa condiciones en orden y regresa el primer
`THEN` que aplique (`ELSE` es el default si ninguna condición coincide). El
equivalente en el ORM de Django son las expresiones condicionales `Case`/`When`
(`django.db.models.Case`, `django.db.models.When`) — mismo concepto, sintaxis de
Python en vez de SQL.

## `COALESCE` vs `ISNULL`

Ambas resuelven lo mismo — "dame un valor de repuesto si esto es `NULL`" — pero con
una diferencia importante:

```sql
SELECT COALESCE(o.Quantity, 0) AS Quantity   -- ANSI SQL, funciona en cualquier motor
SELECT ISNULL(o.Quantity, 0) AS Quantity      -- específico de SQL Server
```

| | `COALESCE` | `ISNULL` |
|---|---|---|
| Estándar | ANSI SQL (ver [docs/28](28-fundamentos-bases-de-datos.md#ansi-sql-por-qué-el-sql-es-portable)) — funciona en SQL Server, PostgreSQL, SQLite... | Específico de SQL Server |
| Cuántos argumentos | 2 o más (regresa el primero que no sea `NULL`) | Exactamente 2 |
| Tipo de dato del resultado | Se determina por reglas de precedencia entre todos los argumentos | Toma el tipo del **primer** argumento |

**Recomendación práctica**: usa `COALESCE` por default — es portable entre motores
(la misma razón por la que preferimos ANSI SQL en general), y `ISNULL` solo si ya
sabes que el proyecto vive exclusivamente en SQL Server y necesitas ese
comportamiento específico de tipos.

---

## Autoevaluación (Módulo 70)

1. **¿Qué es un `INNER JOIN` y cuándo se usa?**
   Combina dos tablas trayendo solo las filas con coincidencia en ambas — para
   obtener información relacionada, descartando lo que no tiene correspondencia. → [INNER JOIN](#inner-join-el-más-común)

2. **¿Diferencia entre `LEFT JOIN` y `RIGHT JOIN`?**
   `LEFT JOIN` prioriza todo de la tabla izquierda; `RIGHT JOIN`, todo de la
   derecha — son intercambiables invirtiendo el orden de las tablas. → [LEFT JOIN y RIGHT JOIN](#left-join-y-right-join-cuando-faltan-datos)

3. **¿Cuándo es útil un `FULL OUTER JOIN`?**
   Para traer todo de ambas tablas a la vez, útil en auditorías que buscan
   registros sin correspondencia en cualquiera de los dos lados. → [FULL OUTER JOIN](#full-outer-join-todo-de-ambos-lados)

4. **¿Qué es un `CROSS JOIN` y cuándo se aplica?**
   Producto cartesiano de dos tablas — combinaciones completas a propósito (como
   productos × días del mes), casi nunca accidental si le pones atención al `ON`. → [CROSS JOIN](#cross-join-el-que-casi-nunca-usas)

5. **¿Diferencia entre `UNION` y `UNION ALL`?**
   `UNION` quita duplicados (más trabajo); `UNION ALL` no los quita (más rápido). → [UNION vs UNION ALL](#union-vs-union-all)

6. **¿Para qué sirve `CASE`?**
   Lógica condicional dentro de una consulta — el equivalente SQL de un
   `if/elif/else`, para personalizar el resultado según condiciones. → [CASE](#case-lógica-condicional-dentro-de-una-consulta)

7. **¿Qué hace `COALESCE` y cuándo es útil?**
   Regresa el primer valor no nulo de una lista — evita `NULL` en los resultados,
   dando un valor por default. → [COALESCE vs ISNULL](#coalesce-vs-isnull)

8. **¿Diferencia entre `ISNULL` y `COALESCE`?**
   `ISNULL` es de SQL Server, solo 2 argumentos, tipo del primero. `COALESCE` es
   ANSI SQL, portable, acepta múltiples argumentos. → [COALESCE vs ISNULL](#coalesce-vs-isnull)

9. **¿Por qué importa dominar los JOINs?**
   Porque la información relevante casi nunca vive en una sola tabla — combinar
   tablas correctamente es la base de cualquier reporte o vista de datos real.

10. **¿Cómo ilustra AdventureWorks el uso de JOINs?**
    Con tablas reales relacionadas (órdenes, productos, empleados) para practicar
    cada tipo de unión en un escenario parecido a un sistema de producción.

## Ejemplo de uso en el mercado laboral

- **Informes de ventas**: `INNER JOIN` entre órdenes y productos para reportes de
  rendimiento — el ejemplo exacto del módulo.
- **Auditoría de datos**: `LEFT JOIN`/`FULL OUTER JOIN` para encontrar transacciones
  sin su correspondiente registro de auditoría — señal de un posible error o fraude.
