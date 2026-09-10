# 27 — Redux Toolkit, Axios y estado global en React (Módulo 66 de la plataforma)

Temas: `slice` de Redux Toolkit, `createAsyncThunk`/`extraReducers` para operaciones
asíncronas, `useSelector`/`useDispatch`, Axios, Local Storage para persistir el
carrito, y spinners para estados de carga. Es el primer módulo puramente de
**frontend** — pero el que más directamente se conecta con la API que hemos
construido: es literalmente lo que usaría un cliente para consumir
`/api/crear-guia`, `/api/obtener-guia/{id}`, etc.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **Axios** | Cliente HTTP para JavaScript, para llamar a la API desde el navegador | [Axios: el cliente HTTP](#axios-el-cliente-http) |
| **createAsyncThunk** | Crea una acción de Redux que envuelve una operación asíncrona (una petición) | [createAsyncThunk y extraReducers](#createasyncthunk-y-extrareducers) |
| **extraReducers** | Maneja las acciones que genera un `createAsyncThunk` dentro de un slice | [createAsyncThunk y extraReducers](#createasyncthunk-y-extrareducers) |
| **Local Storage** | Almacenamiento persistente del navegador (sobrevive recargas de página) | [Local Storage: persistir el carrito](#local-storage-persistir-el-carrito) |
| **OrderSlice** | El slice que gestiona el estado de las órdenes/checkout | [Un slice real: consumiendo Hound Express](#un-slice-real-consumiendo-hound-express) |
| **Redux Toolkit** | Conjunto de herramientas que simplifica usar Redux | [Slice: la unidad básica de Redux Toolkit](#slice-la-unidad-básica-de-redux-toolkit) |
| **slice** | Una porción del estado global, con su `initialState` y reducers | [Slice: la unidad básica de Redux Toolkit](#slice-la-unidad-básica-de-redux-toolkit) |
| **spinners** | Indicador visual de "cargando" | [Spinners: mostrar el estado pending](#spinners-mostrar-el-estado-pending) |
| **useDispatch** | Hook para enviar acciones al store desde un componente | [useSelector y useDispatch](#useselector-y-usedispatch-conectar-componentes-al-store) |
| **useSelector** | Hook para leer datos del store desde un componente | [useSelector y useDispatch](#useselector-y-usedispatch-conectar-componentes-al-store) |

---

## Slice: la unidad básica de Redux Toolkit

Redux administra **un solo objeto de estado global** para toda la aplicación —
pero organizado en pedazos independientes, cada uno llamado **slice** ("rebanada").
Un slice agrupa: el estado inicial de esa porción, y las funciones (`reducers`) que
saben modificarlo.

```javascript
const productsSlice = createSlice({
  name: 'products',
  initialState: { items: [], status: 'idle', error: null },
  reducers: {},
  extraReducers: (builder) => { /* ... */ },
});
```

Es conceptualmente parecido a cómo dividimos Hound Express en apps (`shipments`) con
sus propios modelos — cada slice es "el área de responsabilidad de una parte del
estado", igual que cada app de Django es responsable de sus propios modelos.
**Redux Toolkit** es, en este sentido, el envoltorio que hace que definir un slice
sea mucho más corto que el Redux "clásico" (sin la palabra "Toolkit"), donde había
que escribir action types, action creators y el reducer por separado a mano.

## `createAsyncThunk` y `extraReducers`

Casi cualquier dato en una app real viene de una API — y eso es **asíncrono** (la
respuesta no llega al instante). `createAsyncThunk` empaqueta ese "pedir datos y
esperar" en una acción de Redux que automáticamente pasa por 3 estados:
`pending` (esperando) → `fulfilled` (éxito) o `rejected` (falló).

```javascript
export const fetchProducts = createAsyncThunk('products/fetchProducts', async () => {
  const response = await axios.get('/api/products');
  return response.data;
});
```

El slice completo, reaccionando a esos 3 estados con `extraReducers`:

```javascript
const productsSlice = createSlice({
  name: 'products',
  initialState: { items: [], status: 'idle', error: null },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchProducts.pending, (state) => {
        state.status = 'pending';
      })
      .addCase(fetchProducts.fulfilled, (state, action) => {
        state.status = 'fulfilled';
        state.items = action.payload;
      })
      .addCase(fetchProducts.rejected, (state, action) => {
        state.status = 'rejected';
        state.error = action.error.message;
      });
  }
});
```

- **`fetchProducts.pending`**: se dispara en cuanto se llama `dispatch(fetchProducts())`,
  antes de que la petición termine — aquí es donde activarías un **spinner**.
- **`fetchProducts.fulfilled`**: la petición salió bien; `action.payload` es
  justo lo que regresó la función async (`response.data`).
- **`fetchProducts.rejected`**: la petición falló (por ejemplo, un `404` o `500` de
  la API) — `action.error.message` trae el motivo.

`extraReducers` se llama así (a diferencia de `reducers`, el otro campo del slice)
porque maneja acciones que **no se definieron dentro de este mismo slice** — las
generó `createAsyncThunk` por fuera.

## `useSelector` y `useDispatch`: conectar componentes al store

Dentro de un componente de React, estos dos hooks son la conexión con Redux:

```javascript
import { useSelector, useDispatch } from 'react-redux';
import { fetchProducts } from './productsSlice';

function ListaProductos() {
  const dispatch = useDispatch();
  const { items, status } = useSelector((state) => state.products);

  useEffect(() => {
    dispatch(fetchProducts());
  }, [dispatch]);

  if (status === 'pending') return <Spinner />;
  return <ul>{items.map((p) => <li key={p.id}>{p.nombre}</li>)}</ul>;
}
```

- **`useDispatch()`**: te da la función `dispatch` — la única forma de "avisarle" a
  Redux que algo debe pasar (disparar una acción, síncrona o asíncrona como
  `fetchProducts()`).
- **`useSelector(callback)`**: lee una parte del estado global — el callback recibe
  todo el estado y regresa solo lo que este componente necesita, para no
  re-renderizar de más cuando cambia una parte del estado que no le importa.

## `spinners`: mostrar el estado `pending`

Un spinner es, literalmente, el `if (status === 'pending')` de arriba — la interfaz
reacciona al estado que ya está guardado en el slice, sin lógica extra: el mismo
`status` que actualiza `extraReducers` es el que decide qué se dibuja.

## Axios: el cliente HTTP

Axios hace lo mismo que el `fetch` nativo del navegador, con menos código
repetitivo:

```javascript
// fetch nativo
const response = await fetch('/api/crear-guia', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
});
const json = await response.json();

// axios
const { data: json } = await axios.post('/api/crear-guia', data);
```

Axios ya convierte la respuesta a JSON automáticamente, manda `Content-Type` solo,
y —diferencia importante— **rechaza la promesa automáticamente en códigos de error**
(4xx/5xx), mientras que `fetch` los trata como "éxito" y tienes que chequear
`response.ok` tú mismo.

## Local Storage: persistir el carrito

El estado de Redux vive **solo en memoria** — si recargas la página, se pierde. Para
que un carrito de compras sobreviva una recarga, se guarda también en
`localStorage` (ver la nota sobre `localStorage` en artefactos, mismo concepto: es
almacenamiento del navegador, por origen, que persiste entre recargas):

```javascript
const cartSlice = createSlice({
  name: 'cart',
  initialState: {
    items: JSON.parse(localStorage.getItem('cart')) || [],
  },
  reducers: {
    addItem: (state, action) => {
      state.items.push(action.payload);
      localStorage.setItem('cart', JSON.stringify(state.items));
    },
  },
});
```

El patrón es siempre el mismo: leer de `localStorage` al armar el `initialState`, y
escribir a `localStorage` cada vez que un reducer cambia ese pedazo del estado.

## Un slice real: consumiendo Hound Express

Uniendo todo lo anterior con nuestra propia API — así se vería un `guiasSlice` que
consume `/api/crear-guia` y `/api/obtener-guia/{id}` (los endpoints reales de este
proyecto, ver [README.md](../README.md#endpoints-de-la-api)):

```javascript
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export const crearGuia = createAsyncThunk('guias/crear', async (datosGuia) => {
  const { data } = await axios.post(`${API_BASE}/crear-guia`, datosGuia);
  return data;
});

export const obtenerGuia = createAsyncThunk('guias/obtener', async (id) => {
  const { data } = await axios.get(`${API_BASE}/obtener-guia/${id}`);
  return data;
});

const guiasSlice = createSlice({
  name: 'guias',
  initialState: { actual: null, status: 'idle', error: null },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(crearGuia.pending, (state) => { state.status = 'pending'; })
      .addCase(crearGuia.fulfilled, (state, action) => {
        state.status = 'fulfilled';
        state.actual = action.payload;
      })
      .addCase(crearGuia.rejected, (state, action) => {
        state.status = 'rejected';
        state.error = action.error.message;
      })
      .addCase(obtenerGuia.fulfilled, (state, action) => {
        state.actual = action.payload;
      });
  },
});

export default guiasSlice.reducer;
```

Este es, literalmente, el "sistema frontal" que menciona la consigna de la entrega
"Creación de los Endpoints" ([shipments/urls.py](../shipments/urls.py)) — el `axios.post`
de `crearGuia` es quien haría la llamada real a `POST /api/crear-guia` que probamos
con `curl` y Postman a lo largo de este proyecto. El `camelCase` de los campos de
`Guia` (`trackingNumber`, `currentStatus`) ya viene "listo" para usarse tal cual en
JavaScript, sin transformar nombres — una de las razones por las que ese proyecto
usa `camelCase` en vez de `snake_case`, como se señaló en el
[README.md](../README.md#modelo-de-datos).

---

## Autoevaluación (Módulo 66)

1. **¿Por qué importa un entorno de desarrollo bien configurado?**
   Para que Node.js/npm (frontend) y Python/Django (backend) funcionen correctos y
   se puedan integrar sin fricción, sobre todo cuando viven en repos separados.

2. **¿Cómo se gestiona el estado global en la app trabajada?**
   Con Redux Toolkit, organizando el estado en slices independientes por área
   (productos, carrito, órdenes). → [Slice: la unidad básica de Redux Toolkit](#slice-la-unidad-básica-de-redux-toolkit)

3. **¿Qué es `createAsyncThunk` y cómo se usa?**
   Función que envuelve una operación asíncrona (como una petición con axios) en
   una acción de Redux con 3 estados automáticos (`pending`/`fulfilled`/`rejected`),
   manejados en `extraReducers`. → [createAsyncThunk y extraReducers](#createasyncthunk-y-extrareducers)

4. **¿Cómo se asegura la persistencia del carrito?**
   Guardando su estado en `localStorage` cada vez que cambia, y leyéndolo de ahí al
   inicializar el slice — sobrevive recargas de página. → [Local Storage](#local-storage-persistir-el-carrito)

5. **¿Por qué importa documentar el código en un proyecto Full Stack?**
   Facilita depurar problemas que cruzan frontend y backend, y mantiene alineado a
   todo el equipo sobre cómo se integran ambas partes — el mismo motivo por el que
   este proyecto lleva toda la carpeta `docs/`.

6. **¿Cómo se integran las operaciones asíncronas en Redux Toolkit?**
   Con `createAsyncThunk` para crear la acción, y `extraReducers` dentro del slice
   para reaccionar a sus 3 estados posibles.

7. **¿Qué hooks conectan componentes al estado global?**
   `useSelector` (leer estado) y `useDispatch` (disparar acciones). → [useSelector y useDispatch](#useselector-y-usedispatch-conectar-componentes-al-store)

8. **¿Cómo se implementa un sistema de checkout?**
   Con un `OrderSlice` propio (estado de la orden en curso), formularios de
   login/registro para autenticación, y conexión correcta a la base de datos del
   backend — la misma idea de `Order`/`BillingProfile` vista en
   [docs/17](17-ordenes-facturacion-y-senales.md).

9. **¿Qué prepara este módulo para proyectos futuros?**
   Integrar frontend y backend de punta a punta, con manejo robusto de estados de
   carga/error — la base de cualquier aplicación Full Stack real.

## Ejemplo de uso en el mercado laboral

- **E-commerce**: React + Redux Toolkit en el frontend, Django + DRF en el backend —
  exactamente la arquitectura que asume este proyecto (Hound Express) para "la
  aplicación Front" que menciona el [README.md](../README.md).
- **Gestión de inventario**: Axios + Redux Toolkit para actualizaciones en tiempo
  real sobre grandes volúmenes de datos, con spinners y manejo de error consistente
  en toda la app.
