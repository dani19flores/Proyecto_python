# 26 — Web scraping con Selenium y Beautiful Soup (Módulo 65 de la plataforma)

Temas: qué es el web scraping, Selenium + ChromeDriver para controlar un navegador
real, Beautiful Soup para extraer datos del HTML resultante, y buenas prácticas de
manejo de `WebDriver`. Es el primer módulo del curso que sale de Django — aquí el
"backend" no es una API propia, sino un script que consume datos de **otro** sitio.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **Beautiful Soup** | Librería para parsear HTML/XML y navegar su estructura | [Beautiful Soup: extraer datos del HTML](#beautiful-soup-extraer-datos-del-html) |
| **ChromeDriver** | Ejecutable que le permite a Selenium controlar Chrome | [Selenium + ChromeDriver](#selenium--chromedriver-controlar-un-navegador-real) |
| **DOM** | Representación estructurada (en árbol) de un documento HTML | [Beautiful Soup: extraer datos del HTML](#beautiful-soup-extraer-datos-del-html) |
| **Homebrew** | Gestor de paquetes de macOS, usado para instalar ChromeDriver ahí | [Instalación](#instalación) |
| **Instancia de WebDriver** | El objeto que representa "un navegador abierto y controlado por tu script" | [Manejo de la instancia de WebDriver](#manejo-de-la-instancia-de-webdriver) |
| **Scraping** | Extraer datos de sitios web de forma automatizada | [Qué es el web scraping](#qué-es-el-web-scraping) |
| **Selenium** | Herramienta para automatizar navegadores | [Selenium + ChromeDriver](#selenium--chromedriver-controlar-un-navegador-real) |
| **Selector** | Expresión para ubicar un elemento específico en el HTML | [Selectores: cómo apunta Beautiful Soup](#selectores-cómo-apunta-beautiful-soup) |

---

## Qué es el web scraping

Extraer información de un sitio web **de forma automática**, en vez de copiarla a
mano: un script "visita" páginas y guarda los datos que le interesan (precios,
títulos, reseñas...) para procesarlos después. La pieza que ya conocemos de este
curso —una API REST propia, como la de Hound Express— es la otra cara de la misma
moneda: en vez de exponer datos para que otros los consuman (lo que hace
`GuiaViewSet`), el scraping **consume** datos de un sitio que no te dio una API
para eso.

## Selenium + ChromeDriver: controlar un navegador real

Muchos sitios modernos cargan contenido con JavaScript **después** de que la página
carga — si solo pides el HTML crudo (como haría una petición `requests.get()`
normal), ese contenido todavía no existe en la respuesta. **Selenium** resuelve esto
abriendo un navegador de verdad, dejando que el JavaScript corra, y dándote el HTML
**ya renderizado**.

**ChromeDriver** es el puente entre tu código Python y Chrome: un ejecutable
separado que Selenium usa para mandarle comandos al navegador ("abre esta URL",
"haz clic aquí", "dame el HTML actual").

```python
from selenium import webdriver

driver = webdriver.Chrome()
driver.get('https://www.example.com')
html = driver.page_source
```

- **`webdriver.Chrome()`**: crea la instancia de WebDriver — esto literalmente abre
  una ventana de Chrome controlada por tu script.
- **`driver.get(url)`**: navega a esa URL (equivalente a que tú escribieras la
  dirección y dieras Enter).
- **`driver.page_source`**: el HTML de la página **en este momento** — ya con
  cualquier contenido cargado por JavaScript.

## Instalación

```bash
pip install selenium
pip install beautifulsoup4
```

ChromeDriver, en cambio, es un ejecutable aparte, no un paquete de Python — cómo lo
instalas depende del sistema operativo:

- **macOS**: con **Homebrew** (`brew install chromedriver`), el gestor de paquetes
  estándar de macOS — resuelve también darle permiso de ejecución al binario, que
  macOS bloquea por default para ejecutables descargados de internet.
- **Windows/Linux**: se descarga el ejecutable que coincida con tu versión de Chrome
  y se coloca en el `PATH`, o se le pasa la ruta directamente a `webdriver.Chrome()`.

Versiones recientes de Selenium (4.6+) incluyen **Selenium Manager**, que descarga y
gestiona el ChromeDriver correcto automáticamente — si tu versión lo soporta, te
ahorras este paso manual por completo.

## Manejo de la instancia de WebDriver

El punto que remarca el resumen del módulo: cada `webdriver.Chrome()` abre un
proceso de navegador real, que consume memoria y CPU — si tu script termina (o
truena) sin cerrar esa instancia, el proceso de Chrome se queda abierto "huérfano".

```python
driver = webdriver.Chrome()
try:
    driver.get('https://www.example.com')
    html = driver.page_source
finally:
    driver.quit()   # se ejecuta pase lo que pase, incluso si algo falla arriba
```

`driver.quit()` cierra el navegador y libera los recursos — usar `try/finally` (o un
`with` si la versión de Selenium lo soporta) asegura que se cierre incluso si el
scraping falla a la mitad, evitando acumular procesos de Chrome abiertos entre
corridas sucesivas del script.

## Beautiful Soup: extraer datos del HTML

Ya con el HTML completo (`driver.page_source`), Beautiful Soup lo convierte en una
estructura navegable — básicamente representa el **DOM** (el árbol de elementos
anidados: `<html>` contiene `<body>`, que contiene `<div>`, que contiene `<h2>`...)
como objetos de Python que puedes recorrer y buscar.

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, 'html.parser')

productos = soup.find_all('h2', class_='product-title')
for producto in productos:
    print(producto.text)
```

- **`BeautifulSoup(html, 'html.parser')`**: parsea el HTML — `'html.parser'` es el
  parser incorporado de Python; también existen `'lxml'` (más rápido, requiere
  instalar la librería `lxml` aparte).
- **`soup.find_all('h2', class_='product-title')`**: busca **todos** los elementos
  `<h2>` que tengan la clase CSS `product-title` — regresa una lista.
- **`.text`**: el texto plano dentro del elemento, sin las etiquetas HTML.

## Selectores: cómo apunta Beautiful Soup

Un selector es, en el fondo, "cómo le describes a Beautiful Soup qué elemento
quieres". Los más comunes:

```python
soup.find('h1')                                  # el primer <h1>
soup.find_all('a')                                # todos los <a>
soup.find('div', class_='precio')                 # un <div class="precio">
soup.find('span', id='total')                     # un <span id="total">
soup.select('.product-title')                     # selector CSS: clase .product-title
soup.select('#total')                              # selector CSS: id #total
soup.select('div.card > h2')                       # CSS: h2 hijo directo de div.card
```

`.select()` acepta selectores CSS completos (los mismos que usarías en una hoja de
estilos) — más flexible que `find`/`find_all` para estructuras anidadas complejas.

### Cómo se encuentran los selectores correctos en la práctica

El paso que menciona el módulo como "inspección de elementos HTML": en el navegador,
clic derecho sobre el dato que quieres (un precio, un título) → **Inspeccionar** →
el DevTools te muestra exactamente qué etiqueta, clase o id tiene ese elemento en el
DOM real — de ahí sacas el selector que le vas a pasar a Beautiful Soup. Sin este
paso, estarías adivinando la estructura del HTML a ciegas.

## Limpiar y convertir datos extraídos

Los datos que salen de Beautiful Soup son siempre **texto** (`str`), aunque
"parezcan" números — un precio como `"$1,299.00"` no sirve para cálculos hasta
limpiarlo:

```python
precio_texto = producto.find('span', class_='precio').text   # "$1,299.00"
precio_limpio = precio_texto.replace('$', '').replace(',', '')
precio = float(precio_limpio)   # 1299.0
```

Es el mismo principio de "validar/transformar datos de entrada" que ya vimos con
Django Forms (`clean_<campo>`, ver [docs/20](20-django-forms.md#validación-personalizada-clean_campo))
y con los serializers de DRF — aquí no hay validación automática de ningún
framework, así que la limpieza (quitar símbolos, convertir tipo) la escribes tú a
mano antes de usar el dato.

---

## Autoevaluación (Módulo 65)

1. **¿Qué es el web scraping?**
   Extraer datos de sitios web de forma automatizada, con un script que navega
   páginas y guarda la información relevante. → [Qué es el web scraping](#qué-es-el-web-scraping)

2. **¿Qué herramientas se usan en este módulo?**
   Selenium (controla un navegador real) y Beautiful Soup (parsea el HTML
   resultante para extraer datos). → [Selenium + ChromeDriver](#selenium--chromedriver-controlar-un-navegador-real)

3. **¿Cómo se instalan Beautiful Soup y Selenium?**
   `pip install beautifulsoup4` y `pip install selenium`; ChromeDriver se instala
   aparte (por ejemplo con Homebrew en macOS) o lo gestiona Selenium Manager
   automáticamente en versiones recientes. → [Instalación](#instalación)

4. **¿Para qué sirve ChromeDriver?**
   Es el puente entre Selenium y Chrome — permite automatizar clics, navegación y
   obtener el HTML ya renderizado (incluido contenido cargado por JavaScript).

5. **¿Cómo se obtiene el HTML de una página con Selenium?**
   `driver.get(url)` navega a la página, y `driver.page_source` regresa el HTML
   actual para procesarlo después con Beautiful Soup.

6. **¿Qué se puede extraer de un sitio de e-commerce?**
   Títulos, URLs, precios, descripciones y otros detalles de producto — datos útiles
   para análisis de mercado o comparación de precios.

7. **¿Por qué importa manejar bien las instancias de WebDriver?**
   Cada instancia abre un proceso de navegador real que consume recursos; no
   cerrarlo (`driver.quit()`) dentro de un `try/finally` deja procesos huérfanos y
   puede causar conflictos entre corridas. → [Manejo de la instancia de WebDriver](#manejo-de-la-instancia-de-webdriver)

8. **¿Aplicaciones prácticas del scraping en e-commerce?**
   Monitorear precios de la competencia, analizar tendencias de productos,
   recopilar reseñas — Trivago comparando precios de hoteles es el ejemplo citado
   por el módulo.

9. **¿Qué habilidades destaca el módulo?**
   Extracción/procesamiento de datos web, uso de Selenium + Beautiful Soup, y
   automatización de navegación — habilidades demandadas fuera del desarrollo web
   "de construir" APIs, en el lado de "consumir" datos externos.

10. **¿Cómo se limpia y convierte un precio extraído a número?**
    Quitando símbolos no numéricos (`$`, comas) del texto extraído y convirtiendo
    con `float()`/`int()` antes de usarlo en cálculos. → [Limpiar y convertir datos extraídos](#limpiar-y-convertir-datos-extraídos)

## Ejemplo de uso en el mercado laboral

- **Comparación de precios**: Trivago y sitios similares dependen de scraping (o
  APIs equivalentes) para agregar precios de múltiples fuentes en un solo lugar.
- **Análisis de mercado en e-commerce**: monitorear precios y catálogos de la
  competencia para ajustar estrategia de precios propia.
