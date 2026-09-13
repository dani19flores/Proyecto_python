# 35 — Administración de SQL Server: usuarios, backups y carga de datos (Módulo 74 de la plataforma)

Temas: crear/gestionar bases de datos y usuarios, roles y permisos, políticas de
contraseñas, respaldo y restauración, y los 3 métodos para cargar datos masivos
(`BULK INSERT`, asistente de importación, `ETL`). Este módulo es trabajo de **DBA**
(administrador de bases de datos) — la capa de operación y seguridad que vive por
encima de escribir consultas.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **BULK INSERT** | Carga masiva de datos desde un archivo externo (CSV, etc.) | [Los 3 métodos para cargar datos](#los-3-métodos-para-cargar-datos) |
| **ETL** | Extraer, Transformar y Cargar datos entre sistemas | [Los 3 métodos para cargar datos](#los-3-métodos-para-cargar-datos) |
| **Management Studio** | Herramienta gráfica de Microsoft para SQL Server | Ya cubierto en [docs/28](28-fundamentos-bases-de-datos.md#ide-vs-herramienta-de-base-de-datos) |
| **Modelo Entidad-Relación** | Estructura lógica de entidades, atributos y relaciones | Se profundiza en [docs/36](36-modelado-de-datos-y-normalizacion.md) |
| **Optimización del rendimiento** | Ajustar consultas/operaciones para que corran más rápido | [Optimización del rendimiento](#optimización-del-rendimiento) |
| **Políticas de contraseñas** | Reglas sobre cómo deben ser las contraseñas de acceso | [Usuarios, roles y permisos](#usuarios-roles-y-permisos) |
| **Respaldo y restauración** | Copias de seguridad y su recuperación ante pérdida/corrupción | [Respaldo y restauración](#respaldo-y-restauración) |
| **Roles de base de datos** | Conjuntos de permisos asignables a usuarios | [Usuarios, roles y permisos](#usuarios-roles-y-permisos) |

---

## Crear y eliminar bases de datos

```sql
CREATE DATABASE MiBaseDeDatos;
DROP DATABASE MiBaseDeDatos;
```

Tan simple como crear/eliminar una tabla (ver [docs/29](29-sql-basico-crud.md#delete-vs-truncate-vs-drop-la-diferencia-que-importa)),
pero un nivel más arriba: `CREATE DATABASE` crea el contenedor completo donde
después vivirán tablas, vistas, procedimientos, etc. Puede hacerse por SQL (como
arriba) o gráficamente desde Management Studio — clic derecho en **Databases** →
**New Database...**.

## Usuarios, roles y permisos

```sql
-- Crear un login (autenticación a nivel de servidor) y un usuario (acceso a una base específica)
CREATE LOGIN MiUsuario WITH PASSWORD = 'ContraseñaSegura';
CREATE USER MiUsuario FOR LOGIN MiUsuario;

-- Asignar permisos mediante roles
ALTER ROLE db_datareader ADD MEMBER MiUsuario;
ALTER ROLE db_datawriter ADD MEMBER MiUsuario;
```

Dos niveles distintos, fáciles de confundir al inicio:

- **`LOGIN`**: la credencial a nivel de **servidor** — "quién eres" cuando te
  conectas a la instancia de SQL Server completa.
- **`USER`**: el mapeo de ese login a permisos dentro de **una base de datos**
  específica — el mismo login puede tener distintos niveles de acceso en distintas
  bases.

**Roles de base de datos** son paquetes de permisos ya armados —
`db_datareader` (puede leer todas las tablas), `db_datawriter` (puede
insertar/actualizar/borrar), `db_owner` (control total) — en vez de otorgar
permisos uno por uno (`GRANT SELECT ON tabla TO usuario`, el comando DCL que
mencionamos como categoría en [docs/30](30-sql-select-llaves-null.md#las-4-categorías-de-comandos-sql)
sin profundizar), asignas el rol y el usuario hereda todo ese paquete. La regla de
oro (mencionada en el resumen del módulo): **permisos mínimos necesarios** — nunca
des `db_owner` a alguien que solo necesita leer datos.

**Políticas de contraseñas**: SQL Server puede exigir reglas (longitud mínima,
complejidad, expiración) al crear un `LOGIN`, heredando las políticas de Windows si
así se configura — el mismo espíritu que ya vimos con
`AUTH_PASSWORD_VALIDATORS` en `settings.py` de este proyecto ([hound_express/settings.py](../hound_express/settings.py)),
donde Django valida longitud mínima, similitud con datos del usuario, contraseñas
comunes, etc. antes de aceptar una contraseña nueva — misma idea, dos capas
distintas del stack (motor de base de datos vs framework de aplicación).

## Respaldo y restauración

```sql
-- Backup completo de la base de datos
BACKUP DATABASE MiBaseDeDatos TO DISK = 'C:\backups\MiBaseDeDatos.bak';

-- Restaurar desde ese backup
RESTORE DATABASE MiBaseDeDatos FROM DISK = 'C:\backups\MiBaseDeDatos.bak';
```

Ya usamos exactamente este patrón (`.bak` + restaurar en SSMS) para traer
**AdventureWorks** a nuestro propio SQL Server en los ejercicios de
[docs/28](28-fundamentos-bases-de-datos.md#bases-de-datos-de-ejemplo-el-rol-de-adventure-works)
y las consultas posteriores — un `.bak` no es más que el resultado de un
`BACKUP DATABASE` que alguien más corrió antes de compartirlo contigo.

**Por qué importa tanto**: es la única red de seguridad real contra pérdida o
corrupción de datos — un `DELETE`/`DROP` sin `WHERE` por accidente (ver
[docs/29](29-sql-basico-crud.md#where-la-cláusula-que-evita-desastres)) solo se
puede deshacer si existe un backup reciente. Un "plan de respaldo" real no es solo
"hacer un backup una vez" — es automatizarlos con una frecuencia definida (diario,
por hora, según qué tan crítico sea perder los últimos cambios) y **probar
periódicamente que restaurar de verdad funciona**, no asumirlo.

## Los 3 métodos para cargar datos

| Método | Cuándo conviene | Complejidad |
|--------|---------------------|----------------|
| Asistente de importación (SSMS) | Cargas simples, pocas veces, un archivo a la vez | Baja — todo con clics |
| `BULK INSERT` | Cargas grandes y frecuentes, mismo formato conocido | Media — un comando SQL |
| ETL (Extract, Transform, Load) | Datos de **múltiples fuentes**, que necesitan transformarse antes de cargarse | Alta — requiere una herramienta/proceso dedicado |

```sql
BULK INSERT Productos
FROM 'C:\datos\productos.csv'
WITH (
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    FIRSTROW = 2   -- salta el encabezado del CSV
);
```

`BULK INSERT` es mucho más rápido que un `INSERT` por fila (miles de sentencias
`INSERT` individuales) porque le indica al motor "voy a meter muchos datos de
golpe, optimiza para eso" — el mismo principio detrás de `bulk_create()` en el ORM
de Django (ver [docs/14](14-modelos-y-migraciones.md#creación-a-granel-bulk)): una
sola operación en vez de N.

**ETL** entra en juego cuando la carga no es solo "copiar un CSV a una tabla" —
implica **combinar** datos de fuentes distintas (otra base de datos, una API, varios
archivos con formatos diferentes) y **transformarlos** para que encajen en el
destino (limpiar, unificar formatos de fecha, calcular campos derivados) antes de
cargarlos. Es la misma idea que ya vimos con **Data Warehouse** en
[docs/28](28-fundamentos-bases-de-datos.md#3-data-warehouse--para-analizar-no-para-operar):
un proceso ETL es, típicamente, lo que **alimenta** un data warehouse desde las
bases operativas.

## Optimización del rendimiento

Ajustar consultas/estructura para que corran más rápido — algunas de las piezas que
ya conocemos, ahora vistas desde el ángulo de "por qué le importa a un DBA":

- **Índices** sobre columnas usadas frecuentemente en `WHERE`/`JOIN` (no cubierto
  a fondo todavía en esta documentación, pero es la optimización más común y de
  mayor impacto).
- **Evitar `SELECT *`** cuando no necesitas todas las columnas (ya mencionado en
  [docs/30](30-sql-select-llaves-null.md#select-where-y-order-by)).
- **Revisar el plan de ejecución** de una consulta lenta en SSMS, para ver en qué
  paso se está yendo el tiempo — herramienta de diagnóstico gráfica que la propia
  Management Studio ofrece.
- Del lado de Django, ya vimos el equivalente exacto de este problema con
  `select_related()`/`prefetch_related()` en [docs/14](14-modelos-y-migraciones.md#querysets)
  — evitar el problema N+1 (una consulta extra por cada fila) es optimización de
  rendimiento aplicada al ORM.

---

## Autoevaluación (Módulo 74)

1. **¿Cuál es el papel de un DBA?**
   Gestionar y administrar bases de datos: usuarios, seguridad, rendimiento y
   recursos, usando SQL como herramienta principal.

2. **¿Cómo se crean y eliminan bases de datos?**
   Con `CREATE DATABASE nombre` y `DROP DATABASE nombre`, por SQL o desde
   Management Studio.

3. **¿Por qué importan los backups regulares?**
   Protegen contra pérdida/corrupción de datos, permitiendo restaurar y garantizar
   continuidad del negocio. → [Respaldo y restauración](#respaldo-y-restauración)

4. **¿Métodos para cargar datos desde CSV?**
   Asistente de importación (simple), `BULK INSERT` (rápido, grandes volúmenes), y
   programas ETL (múltiples fuentes, con transformación). → [Los 3 métodos para cargar datos](#los-3-métodos-para-cargar-datos)

5. **¿Qué son los programas ETL y cuándo se usan?**
   Extraer-Transformar-Cargar datos de múltiples fuentes hacia un destino — para
   integraciones que requieren adecuar los datos antes de guardarlos.

6. **¿Cómo se gestionan usuarios, roles y permisos?**
   Creando `LOGIN`+`USER`, y asignando roles (`db_datareader`, `db_datawriter`,
   etc.) en vez de otorgar permisos uno por uno. → [Usuarios, roles y permisos](#usuarios-roles-y-permisos)

7. **¿Qué son los roles de base de datos?**
   Paquetes de permisos predefinidos, asignables a usuarios para simplificar y
   asegurar la gestión de acceso.

8. **¿Cómo se asignan permisos a nivel de servidor y base de datos?**
   `LOGIN` a nivel de servidor (autenticación), `USER` a nivel de base de datos
   específica (autorización) — dos capas distintas.

9. **¿Por qué importan las políticas de contraseñas?**
   Protegen cuentas contra acceso no autorizado exigiendo contraseñas robustas —
   el mismo rol que cumple `AUTH_PASSWORD_VALIDATORS` en Django.

## Ejemplo de uso en el mercado laboral

- **Optimización de rendimiento**: un DBA ajusta diseño e índices para que las
  consultas de una aplicación con miles de usuarios respondan rápido.
- **Integración de datos**: analistas usan ETL para combinar datos de ventas, CRM y
  soporte en un solo destino, habilitando reportes unificados.
