# 36 — Modelado de datos: conceptual, lógico, físico y normalización (Módulo 75 de la plataforma)

Temas: las 3 etapas del modelado de datos (conceptual → lógico → físico),
cardinalidad, diagramas de entidad-relación (ERD) con notación "Crow's Foot",
llaves primaria/foránea, normalización, y restricciones de datos. Este módulo es el
"antes" de todo lo que hemos visto de SQL — el diseño que **precede** a escribir un
solo `CREATE TABLE`.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **Cardinalidad** | Cuántas instancias de una entidad se asocian con otra (1:1, 1:N, N:M) | [Cardinalidad: cuántos con cuántos](#cardinalidad-cuántos-con-cuántos) |
| **Diagrama de Entidad-Relación (ERD)** | Representación visual de entidades, atributos y relaciones | Ya cubierto en [docs/28](28-fundamentos-bases-de-datos.md#el-diagrama-de-entidad-relación-de-hound-express) |
| **Llave Foránea** | Campo que referencia la llave primaria de otra tabla | Ya cubierto en [docs/30](30-sql-select-llaves-null.md#llave-primaria-vs-llave-foránea) |
| **Llave Primaria** | Identifica de forma única cada fila de una tabla | Ya cubierto en [docs/30](30-sql-select-llaves-null.md#llave-primaria-vs-llave-foránea) |
| **Modelo Conceptual** | Representación abstracta, de alto nivel, sin detalles técnicos | [Las 3 etapas del modelado](#las-3-etapas-del-modelado-conceptual--lógico--físico) |
| **Modelo Físico** | Implementación real en un sistema de base de datos específico | [Las 3 etapas del modelado](#las-3-etapas-del-modelado-conceptual--lógico--físico) |
| **Modelo Lógico** | Estructuras técnicas y normalización, sin atarse a un motor específico | [Las 3 etapas del modelado](#las-3-etapas-del-modelado-conceptual--lógico--físico) |
| **Normalización** | Organiza datos para minimizar redundancias y dependencias | [Normalización: las 3 primeras formas](#normalización-las-3-primeras-formas) |
| **Notación de "Crow's Foot"** | Símbolos gráficos para cardinalidad/obligatoriedad en un ERD | [Notación Crow's Foot](#notación-crows-foot) |
| **Restricciones de Datos** | Reglas que aseguran integridad (únicos, no nulos, validaciones) | [Restricciones de datos](#restricciones-de-datos) |

---

## Las 3 etapas del modelado: conceptual → lógico → físico

Como dice el resumen del módulo: un arquitecto no construye sin plano. Modelar datos
**antes** de crear una sola tabla evita descubrir errores de diseño después de que
ya hay datos reales cargados — mucho más caro de corregir en ese punto.

| Etapa | Qué define | Nivel de detalle |
|-------|--------------|----------------------|
| **Conceptual** | Entidades principales y cómo se relacionan, en lenguaje de negocio | Alto nivel, sin tipos de dato ni nombres técnicos de columna |
| **Lógico** | Atributos de cada entidad, llaves, normalización | Técnico, pero independiente de qué motor de base de datos se use |
| **Físico** | El `CREATE TABLE` real, con tipos de dato exactos y restricciones del motor elegido | Específico de SQL Server/PostgreSQL/SQLite/etc. |

**Ejemplo con nuestro propio dominio** (guías de Hound Express):

- **Conceptual**: "Una Guía tiene un Historial de Estatus. Un Usuario actualiza
  esos estatus." — sin mencionar tipos de dato ni nombres de columna todavía.
- **Lógico**: `Guia` tiene `id` (llave primaria), `trackingNumber`, `origin`,
  `destination`, `currentStatus`; `Estatus` tiene `id`, `guideId` (llave foránea
  hacia `Guia`), `status`, `timestamp`, `updatedBy` — ya con estructura, pero sin
  decidir todavía si es SQLite o SQL Server.
- **Físico**: el `CREATE TABLE "Guide" (...)` real que ya vimos en
  [scripts.sql](../scripts.sql), generado por Django a partir de
  [shipments/models.py](../shipments/models.py) — con tipos concretos de SQLite
  (`varchar(15)`, `datetime`, etc.).

Los modelos de Django (`models.py`) viven, en la práctica, en un punto intermedio
entre el modelo lógico y el físico: ya tienen estructura técnica completa (tipos,
llaves, relaciones), pero siguen siendo independientes del motor exacto — el mismo
`shipments/models.py` genera un `CREATE TABLE` distinto según si `DATABASES['default']['ENGINE']`
apunta a SQLite o a PostgreSQL (ver [docs/28](28-fundamentos-bases-de-datos.md#sqlite-lo-que-usamos-vs-postgresqlsql-server)).

## Cardinalidad: cuántos con cuántos

Ya usamos cardinalidad sin nombrarla formalmente en varias entregas de este curso —
aquí el vocabulario correcto:

| Cardinalidad | Significa | Ejemplo ya visto |
|---------------|-------------|----------------------|
| **1:1** (uno a uno) | Una instancia de A con como máximo una de B | `PerfilUsuario` ↔ `User` (ver [docs/18](18-migraciones-avanzadas-y-onetoone.md#onetoonefield-cuando-foreignkey-no-es-suficiente)) |
| **1:N** (uno a muchos) | Una instancia de A con varias de B | `BillingProfile` → `Order` (ver [docs/17](17-ordenes-facturacion-y-senales.md)) |
| **N:M** (muchos a muchos) | Varias de A con varias de B | `Cart` ↔ `Product` (ver [docs/17](17-ordenes-facturacion-y-senales.md)) |

En Django, cada cardinalidad tiene su campo correspondiente:
`OneToOneField` (1:1), `ForeignKey` (1:N, del lado "muchos"), `ManyToManyField`
(N:M) — la elección del campo **es**, literalmente, la decisión de cardinalidad del
modelo lógico, escrita en código Python.

## Notación "Crow's Foot"

Es la forma gráfica más común de dibujar cardinalidad en un ERD — el nombre viene
de que el símbolo de "muchos" se parece a una pata de cuervo (tres líneas que se
abren):

```
Guia ||--o{ Estatus : "tiene"
```

- **`||`** (dos líneas paralelas): "exactamente uno" — obligatorio, cardinalidad 1.
- **`o{`** (círculo + pata de cuervo): "cero o muchos" — opcional, cardinalidad N.

Ya usamos exactamente esta notación (Mermaid `erDiagram`, que sigue esta misma
convención) en [docs/28](28-fundamentos-bases-de-datos.md#el-diagrama-de-entidad-relación-de-hound-express)
para el diagrama de `Guide`/`StatusHistory` de este proyecto — la notación indica
tanto la **cardinalidad** (uno vs muchos) como la **obligatoriedad** (círculo =
opcional, líneas dobles = obligatorio) en el mismo símbolo.

## Normalización: las 3 primeras formas

Normalizar es reorganizar una tabla para eliminar redundancia — cada dato debería
vivir **en un solo lugar**, no repetido en varias filas:

- **1FN (Primera Forma Normal)**: cada columna tiene un solo valor atómico (no
  listas ni valores compuestos dentro de una celda) — por ejemplo, no meter
  `"CDMX, GDL, MTY"` como texto en una sola columna cuando en realidad son 3 datos
  distintos.
- **2FN (Segunda Forma Normal)**: cumple 1FN, y además cada columna depende de la
  **llave primaria completa** — no de solo una parte de ella (relevante en tablas
  con llave primaria compuesta, de dos o más columnas).
- **3FN (Tercera Forma Normal)**: cumple 2FN, y además ninguna columna depende de
  **otra columna que no sea la llave primaria** — por ejemplo, si guardas
  `CategoriaID` y también `NombreCategoria` en la misma tabla `Productos`,
  `NombreCategoria` depende de `CategoriaID`, no de `ProductoID` — debería vivir en
  su propia tabla `Categorias`.

**Nuestro propio proyecto ya sigue estas reglas**, aunque no las hayamos nombrado
así: `Guia.currentStatus` es un solo valor atómico (1FN); no tenemos llaves
compuestas que violen 2FN; y separamos `Estatus` de `Guia` en vez de repetir los
datos de la guía en cada evento de estatus (evitando la violación de 3FN que sería
guardar `trackingNumber`/`origin`/`destination` copiados en cada fila de
`StatusHistory`).

## Restricciones de datos

Reglas que la propia base de datos hace cumplir, sin depender de que la aplicación
las valide correctamente cada vez:

```sql
CREATE TABLE Productos (
    ProductoID INT PRIMARY KEY,
    Nombre VARCHAR(100) NOT NULL,
    Precio DECIMAL(10, 2) CHECK (Precio > 0),
    CategoriaID INT,
    FOREIGN KEY (CategoriaID) REFERENCES Categorias(CategoriaID)
);
```

- **`PRIMARY KEY`**: unicidad + no nulo, para identificar cada fila.
- **`NOT NULL`**: el campo no puede quedar vacío.
- **`CHECK (condición)`**: valida una regla de negocio directo en la base de datos
  (aquí, que el precio sea positivo) — sin esta restricción, un `INSERT` con
  `Precio = -50` se guardaría sin problema.
- **`FOREIGN KEY ... REFERENCES ...`**: integridad referencial — impide crear un
  producto con un `CategoriaID` que no exista en `Categorias`.

Es exactamente el mismo propósito de `null=True`/`blank=False`/validadores de
campo que ya vimos en Django ([docs/14](14-modelos-y-migraciones.md#opciones-de-campo-más-importantes)) —
la diferencia es **dónde** se hace cumplir la regla: `CHECK`/`FOREIGN KEY` la
imponen en la base de datos misma (protege incluso si alguien escribe directo por
SQL, sin pasar por Django); las validaciones de Django solo protegen si el dato
entra por el ORM. Un diseño robusto normalmente usa **ambas** capas — validación en
la aplicación para dar buenos mensajes de error al usuario, y restricciones en la
base de datos como última línea de defensa.

---

## Autoevaluación (Módulo 75)

1. **¿Por qué importa el modelado de datos?**
   Como un plano antes de construir — asegura que la base de datos cumpla los
   requerimientos del negocio antes de implementarla, evitando corregir errores
   costosos después. → [Las 3 etapas del modelado](#las-3-etapas-del-modelado-conceptual--lógico--físico)

2. **¿Cuáles son las etapas del modelado de datos?**
   Conceptual (entidades y relaciones, simple), lógico (estructura técnica y
   normalización), físico (implementación en un motor específico). → [Las 3 etapas del modelado](#las-3-etapas-del-modelado-conceptual--lógico--físico)

3. **¿Qué es un modelo de datos relacional?**
   Organiza datos en tablas conectadas por llaves primarias y foráneas, permitiendo
   relaciones claras y eficientes entre conjuntos de datos.

4. **¿Cómo se simplifica el diseño de bases de datos relacionales?**
   Definiendo propósito, entidades y atributos, llaves primarias, relaciones entre
   tablas, y aplicando normalización — revisando el diseño antes de implementarlo.

5. **¿Qué es un ERD y para qué sirve?**
   Herramienta visual que representa entidades, atributos y relaciones — facilita
   diseñar y comunicar la estructura de una base de datos.

6. **¿Qué es la cardinalidad?**
   La naturaleza numérica de una relación entre entidades: uno a uno, uno a
   muchos, o muchos a muchos. → [Cardinalidad](#cardinalidad-cuántos-con-cuántos)

7. **¿Qué es la normalización y por qué importa?**
   Organiza una base de datos para minimizar redundancias y dependencias
   incorrectas, mejorando integridad y eficiencia — las 3 primeras formas normales
   cubren los casos más comunes. → [Normalización](#normalización-las-3-primeras-formas)

8. **¿Cómo se crea el modelo físico?**
   Implementando el modelo lógico con DDL real (`CREATE TABLE`, llaves,
   restricciones) sobre un motor de base de datos específico.

9. **¿Qué son las llaves primarias y foráneas?**
   Primaria: identifica de forma única cada fila. Foránea: conecta con la llave
   primaria de otra tabla, manteniendo integridad referencial.

10. **¿Cómo se usan los JOINs para unir tablas?**
    Combinan filas de dos o más tablas según una columna relacionada — ya cubierto
    a fondo en [docs/31](31-sql-joins-union.md).

## Ejemplo de uso en el mercado laboral

- **Gestión de inventarios**: modelo relacional bien normalizado para categorizar
  productos y relacionarlos correctamente con proveedores.
- **CRM (gestión de clientes)**: diseño de base de datos estructurado para
  seguimiento eficiente de interacciones y datos personales de clientes.
