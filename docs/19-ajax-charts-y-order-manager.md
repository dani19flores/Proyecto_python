# 19 — AJAX, Chart.js y OrderManager a fondo (Módulo 58 de la plataforma)

Temas: la CBV base `View`, `JsonResponse`, AJAX/jQuery, Chart.js vía CDN, `timedelta`
para filtrar por rangos de fecha, y los métodos reales de `OrderManager`
(`total_data`, `by_weeks_range`, `get_sales_breakdown`) — el manager que ya
adelantamos como concepto genérico unas respuestas atrás.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **AJAX** | Actualizar parte de una página sin recargarla completa | [AJAX y jQuery](#ajax-y-jquery-cómo-se-conectan) |
| **Chart.js** | Librería JS para gráficos interactivos | [Chart.js vía CDN](#chartjs-vía-cdn) |
| **CDN** | Red de servidores que sirve librerías ya listas, sin instalarlas tú | [Chart.js vía CDN](#chartjs-vía-cdn) |
| **JsonResponse** | Atajo de Django para responder JSON sin DRF | [JsonResponse](#jsonresponse-el-response-de-drf-sin-drf) |
| **Order Manager** | Manager con la lógica de cálculo/filtrado de órdenes | [Los métodos reales de OrderManager](#los-métodos-reales-de-ordermanager) |
| **Queryset** | Consulta encadenable y perezosa | Ya cubierto en [docs/14](14-modelos-y-migraciones.md#querysets) |
| **timedelta** | Diferencia entre fechas/horas, para sumar o restar tiempo | [timedelta para rangos de fecha](#timedelta-para-rangos-de-fecha) |
| **View** | La CBV más genérica — todas las demás heredan de ella | [La CBV base: View](#la-cbv-base-view) |

---

## La CBV base: `View`

Todas las CBV que ya vimos (`TemplateView`, `ListView`, `DetailView`, `CreateView`...
en [docs/15](15-cbv-mixins-formularios.md)) en realidad heredan, en algún punto de su
cadena, de `django.views.generic.base.View` — la clase base sin ninguna
funcionalidad de modelo/template incluida. Cuando necesitas una vista que **no**
encaja en ningún patrón genérico (como "aquí va JSON calculado a la medida, no un
CRUD ni una página"), heredas directo de `View`:

```python
from django.views import View
from django.http import JsonResponse


class SalesChartAjaxView(View):
    def get(self, request, *args, **kwargs):
        # tu lógica aquí
        return JsonResponse({'labels': [], 'data': []})
```

`View` no asume nada sobre modelos ni templates — solo define el mecanismo de
"despachar según el método HTTP" (`get()`, `post()`, `put()`, etc., como métodos de
la clase). Es el mismo patrón de las demás CBV, pero sin ningún comportamiento
heredado de fábrica — tú decides el 100% de la lógica.

## AJAX y jQuery: cómo se conectan

**AJAX** no es una librería ni una clase — es una *técnica*: el navegador hace una
petición HTTP **desde JavaScript**, en segundo plano, sin recargar la página, y usa
la respuesta para actualizar solo una parte del DOM (por ejemplo, redibujar un
gráfico con datos nuevos).

**jQuery** es la librería que el módulo usa para hacer esa petición de forma simple:

```javascript
$.ajax({
    url: '/sales/chart-data/',
    method: 'GET',
    success: function(data) {
        // data ya viene parseado de JSON a objeto JS
        myChart.data.labels = data.labels;
        myChart.data.datasets[0].data = data.sales;
        myChart.update();
    }
});
```

El flujo completo: el navegador pide `/sales/chart-data/` → Django (`SalesChartAjaxView.get()`)
calcula los datos y responde JSON → jQuery recibe esa respuesta → actualiza el
gráfico de Chart.js **sin** que la página se recargue. Las tres piezas (AJAX, jQuery,
`JsonResponse`) son, en el fondo, la misma idea de siempre: petición → respuesta JSON
→ el cliente hace algo con ella — el mismo patrón que ya usa **toda** nuestra API de
Hound Express, solo que ahí el "cliente" sería un frontend consumiendo
`/api/guias/` en vez de jQuery consumiendo esta vista a medida.

## `JsonResponse`: el `Response` de DRF, sin DRF

Ya usamos `Response` de DRF varias veces (por ejemplo, en la acción
`estatus_history` de [shipments/views.py](../shipments/views.py)). `JsonResponse` es
el equivalente **de Django puro**, sin necesidad de instalar Django REST Framework —
tal como se ve en este módulo, que trabaja con `View` normal, no con DRF:

```python
from django.http import JsonResponse

def mi_vista(request):
    data = {'labels': ['Lun', 'Mar'], 'sales': [12, 19]}
    return JsonResponse(data)
```

Diferencias prácticas frente a `Response` de DRF:

| | `JsonResponse` (Django) | `Response` (DRF) |
|---|---|---|
| Necesita DRF instalado | No | Sí |
| Serializa modelos automáticamente | No — tienes que armar el diccionario tú mismo | Sí, vía un `Serializer` |
| Negociación de contenido (JSON vs otros formatos) | No | Sí |
| Cuándo conviene | Un endpoint suelto, con datos ya calculados a mano (como este de gráficos) | Un CRUD completo sobre modelos, como `GuiaViewSet` |

Por eso este módulo usa `JsonResponse` en vez de DRF: no está exponiendo un modelo
tal cual, está devolviendo **datos calculados** (sumas, promedios, agrupados por
semana) — no hay un "objeto" que serializar, solo un diccionario armado a mano.

## Chart.js vía CDN

Un **CDN** (*Content Delivery Network*) es una red de servidores que ya tiene
alojadas copias de librerías populares — en vez de descargar Chart.js e instalarlo
en tu proyecto, apuntas a una URL externa:

```html
{# en tu template base (layout.html), ver docs/16 #}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

Con eso, `Chart` ya está disponible como variable global en cualquier `<script>` que
cargue después. El ejemplo completo del módulo:

```javascript
const ctx = document.getElementById('myChart').getContext('2d');
const myChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'],
        datasets: [{
            label: 'Ventas diarias',
            data: [12, 19, 3, 5, 2, 3, 7],
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 1
        }]
    },
    options: {
        scales: { y: { beginAtZero: true } }
    }
});
```

- `ctx`: el "lienzo" 2D del elemento `<canvas id="myChart">` donde se dibuja.
- `type: 'line'`: tipo de gráfico (también existen `'bar'`, `'pie'`, etc.).
- `labels`/`data`: van de la mano por posición — `labels[0]` ("Lunes") corresponde a
  `data[0]` (12 ventas).
- `options.scales.y.beginAtZero`: fuerza que el eje Y empiece en 0, para no
  distorsionar visualmente la diferencia entre valores.

Estos mismos `labels`/`data` son exactamente lo que la vista `SalesChartAjaxView`
debe devolver en su `JsonResponse` — el backend calcula los números, el frontend solo
los dibuja.

## `timedelta` para rangos de fecha

`timedelta` (de `datetime`) representa una **duración**, no un punto en el tiempo —
sirve para sumar/restar tiempo a una fecha:

```python
from datetime import timedelta
from django.utils import timezone

hoy = timezone.now()
hace_una_semana = hoy - timedelta(days=7)
hace_cuatro_semanas = hoy - timedelta(weeks=4)
```

Es la pieza que permite filtrar "las órdenes de las últimas N semanas" — combinando
`timedelta` con un `QuerySet` (ver [docs/14](14-modelos-y-migraciones.md#querysets)):

```python
Order.objects.filter(created_at__gte=hoy - timedelta(weeks=4))
```

`created_at__gte` es el patrón de *lookup* de Django (`__gte` = *greater than or
equal*) para comparar fechas en un filtro — sin `timedelta`, tendrías que calcular esa
fecha límite a mano.

## Los métodos reales de `OrderManager`

Cuando hablamos de `OrderManager` como concepto genérico, mencionamos `by_status`
como ejemplo. Este módulo trae los métodos **reales** que arma para el dashboard de
ventas — el mismo patrón, aplicado a un caso concreto:

```python
from datetime import timedelta

from django.db import models
from django.db.models import Sum, Avg
from django.utils import timezone


class OrderManager(models.Manager):
    def by_weeks_range(self, weeks=4):
        start = timezone.now() - timedelta(weeks=weeks)
        return self.get_queryset().filter(
            created_at__gte=start, refunded=False
        )

    def total_data(self, weeks=4):
        qs = self.by_weeks_range(weeks)
        return qs.aggregate(sum=Sum('total'), avg=Avg('total'))

    def get_sales_breakdown(self, weeks=4):
        qs = self.by_weeks_range(weeks)
        return {
            'labels': [o.created_at.strftime('%d/%m') for o in qs],
            'sales': [float(o.total) for o in qs],
            'totals': self.total_data(weeks),
        }
```

Pieza por pieza:

- **`by_weeks_range`**: el filtro base — últimas N semanas, **excluyendo**
  reembolsadas (`refunded=False`, tal como menciona el resumen del módulo: "excluir
  datos irrelevantes, como órdenes no reembolsadas"). Los otros dos métodos lo
  reutilizan en vez de repetir el filtro.
- **`total_data`**: usa `.aggregate()` (no `.filter()`) — a diferencia de un filtro,
  que regresa varios objetos, `aggregate()` colapsa el queryset en **un solo**
  resultado (`Sum`, `Avg`, `Count`, `Max`, `Min` son las funciones de agregación más
  comunes de `django.db.models`).
- **`get_sales_breakdown`**: arma exactamente el diccionario `{labels, sales}` que
  Chart.js espera — la "traducción" final entre el ORM y el frontend.

La vista que consume esto, atando todos los conceptos del módulo:

```python
from django.http import JsonResponse
from django.views import View

from order_manager.models import Order


class SalesChartAjaxView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'no autorizado'}, status=401)
        data = Order.objects.get_sales_breakdown(weeks=4)
        return JsonResponse(data)
```

La validación `request.user.is_authenticated` es la que menciona el resumen del
módulo ("validar la presencia de un usuario en la solicitud") — el equivalente,
hecho a mano dentro del `get()`, de lo que `LoginRequiredMixin` (ya visto en
[docs/15](15-cbv-mixins-formularios.md#loginrequiredmixin)) resolvería
automáticamente si heredaras de él en vez de chequearlo tú mismo.

---

## Autoevaluación (Módulo 58)

1. **¿Qué es Chart.js y cómo se integra?**
   Librería JS de gráficos, incluida vía `<script src="...">` apuntando a un CDN en
   el template base. → [Chart.js vía CDN](#chartjs-vía-cdn)

2. **¿Cómo se hace que los datos del gráfico sean dinámicos?**
   Con métodos en `OrderManager` (`total_data`, `by_weeks_range`) que calculan y
   filtran usando `datetime`/`timedelta`, en vez de datos fijos en el HTML. → [Los métodos reales de OrderManager](#los-métodos-reales-de-ordermanager)

3. **¿Qué es una vista AJAX y cómo se usa aquí?**
   Una vista (heredando de `View`, no de una CBV con template) que responde JSON
   para que el frontend actualice el gráfico sin recargar la página — el método
   `get()` es el que procesa la solicitud. → [La CBV base: View](#la-cbv-base-view)

4. **¿Cómo se estructuran y devuelven los datos en JSON?**
   Un diccionario (`{labels, sales}` o similar) devuelto con `JsonResponse(data)`.
   → [JsonResponse](#jsonresponse-el-response-de-drf-sin-drf)

5. **¿Qué papel juega jQuery?**
   Hace la petición AJAX desde el navegador y, en su callback `success`, actualiza
   el gráfico con la respuesta — sin jQuery (o `fetch` nativo) no habría quien
   disparara la petición. → [AJAX y jQuery](#ajax-y-jquery-cómo-se-conectan)

6. **¿Cómo se generan datos de prueba para los gráficos?**
   Modificando manualmente las fechas de órdenes existentes o creando órdenes
   "dummy", para poblar el rango de semanas que filtra `by_weeks_range` antes de
   tener datos reales.

7. **¿Por qué importa la integración backend-frontend?**
   Para que los cambios en los datos (nuevas órdenes, reembolsos) se reflejen
   automáticamente en el gráfico sin trabajo manual — es la razón de ser de AJAX en
   vez de datos estáticos incrustados en el HTML.

8. **¿Qué métodos se implementaron en `OrderManager`?**
   `total_data` (suma/promedio), `by_weeks_range` (filtro por rango de semanas) y
   `get_sales_breakdown` (arma el diccionario final para el gráfico). → [Los métodos reales de OrderManager](#los-métodos-reales-de-ordermanager)

## Ejemplo de uso en el mercado laboral

- **Dashboards de ventas en tiempo real**: exactamente el caso de este módulo — datos
  agregados (`Sum`, `Avg`) por rango de fechas, servidos vía AJAX para que el
  gráfico se actualice sin recargar.
- **Monitoreo de campañas de marketing**: mismo patrón (`OrderManager` → aquí sería
  un `CampaignManager` o similar) para visualizar métricas que cambian con el
  tiempo.

## Cómo se vería aplicado a Hound Express

Aunque este proyecto no tiene frontend, ya tenemos toda la mitad "backend" de este
patrón lista para reutilizar: `Estatus.objects.filter(timestamp__gte=...)` con
`timedelta` daría, por ejemplo, "entregas de la última semana por día" — el mismo
`get_sales_breakdown` pero para estatus de envíos en vez de ventas. La diferencia
sería devolver esos datos con `Response` de DRF (ya lo hacemos en
`GuiaViewSet.estatus_history`) en vez de `JsonResponse` — el resto del razonamiento
(agregaciones, `timedelta`, agrupar por fecha) es idéntico.
