# 25 — Autenticación: básica, tokens y JWT (Módulo 64 de la plataforma)

Temas: autenticación básica vs por tokens, `Permisos`, el endpoint de login manual
con `Token`, y JWT (`Simple JWT`). Este módulo cierra un hueco que señalamos varias
veces en la documentación anterior: **hoy ningún `ViewSet` de Hound Express exige
autenticación** — cualquiera puede crear/editar/borrar guías sin loguearse. Este
módulo explica exactamente cómo se resolvería.

## Glosario del módulo

| Término | Definición corta | Dónde se explica aquí |
|---------|--------------------|---------------------------|
| **Autenticación Básica** | Usuario/contraseña en Base64 en el header — simple pero insegura | [Autenticación Básica](#autenticación-básica-y-por-qué-no-para-producción) |
| **Autenticación por Tokens** | Token generado que representa al usuario, en vez de credenciales | [Autenticación por tokens](#autenticación-por-tokens) |
| **Endpoint de Login** | Ruta que recibe credenciales y devuelve un token | [El LoginView del módulo](#el-loginview-del-módulo) |
| **JWT** | Estándar de token autocontenido, sin depender de la base de datos | [JWT y Simple JWT](#jwt-y-simple-jwt) |
| **Permisos** | Reglas sobre qué puede hacer un usuario autenticado | [Permisos](#permisos) |
| **Postman** | Herramienta para probar la API | Ya cubierto en [docs/22](22-rest-apis-fundamentos.md#probar-la-api-con-postman) |
| **Serializer** | Valida/transforma datos, incluido el registro de usuarios | Ya cubierto en [docs/13](13-vistas-crud-y-consultas.md) |
| **Simple JWT** | Librería que implementa JWT para DRF | [JWT y Simple JWT](#jwt-y-simple-jwt) |
| **Token de Acceso** | El token en sí, que el cliente manda en cada petición | [Autenticación por tokens](#autenticación-por-tokens) |

---

## Autenticación Básica y por qué no para producción

`BasicAuthentication` de DRF manda usuario y contraseña **en cada petición**,
codificados en Base64 dentro del header:

```
Authorization: Basic ZGFuaTE5ZmxvcmVzOm1pY29udHJhc2XDsWE=
```

**Base64 no es cifrado** — es solo una codificación, reversible por cualquiera en un
segundo (`echo "..." | base64 -d`). Si esa petición viaja sin HTTPS, la contraseña
queda expuesta en texto plano a quien intercepte el tráfico. Por eso el módulo la
marca como "útil para pruebas", no para producción — sirve para probar rápido desde
Postman/`curl` en desarrollo local, nunca para un sistema real expuesto en internet.

## Autenticación por tokens

En vez de mandar la contraseña en cada petición, el usuario la manda **una sola vez**
(al loguearse) y recibe a cambio un **token** — una cadena opaca que representa su
sesión autenticada. De ahí en adelante, cada petición manda el token, no la
contraseña:

```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4
```

Si alguien intercepta el token, puede hacerse pasar por el usuario **mientras el
token siga siendo válido** — pero nunca obtiene la contraseña real, y el token se
puede revocar sin que el usuario tenga que cambiar su contraseña.

### El `LoginView` del módulo

```python
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate


class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        return Response({'error': 'Credenciales inválidas'}, status=400)
```

- **`authenticate(username=, password=)`**: función de Django que verifica las
  credenciales contra la base de datos (usando el `User` de fábrica, o el que hayas
  configurado con `AUTH_USER_MODEL`, ver
  [docs/16](16-usuarios-personalizados-y-templates.md#usuario-personalizado-abstractbaseuser--usermanager)) —
  regresa el objeto `User` si son correctas, o `None` si no.
- **`Token.objects.get_or_create(user=user)`**: trae el token existente de ese
  usuario, o crea uno nuevo la primera vez — así el mismo usuario siempre tiene el
  mismo token hasta que se revoque explícitamente.
- El cliente guarda ese `token.key` y lo manda en el header `Authorization` de ahí en
  adelante — **usa `APIView`, no `ViewSet`**, porque no es una operación CRUD sobre
  un modelo (ver la distinción de [docs/23](23-apiview-vs-viewset.md)), es una acción
  puntual: "dame un token".

Del lado del `ViewSet` que quieres proteger, solo hace falta:

```python
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

class GuiaViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Guia.objects.all()
    serializer_class = GuiaSerializer
```

## Permisos

`authentication_classes` responde "¿quién eres?" (identifica al usuario a partir del
token/credenciales). `permission_classes` responde una pregunta distinta: "¿puedes
hacer *esto*?" — son capas separadas. Las más comunes de DRF:

| Permiso | Qué permite |
|---------|---------------|
| `AllowAny` | Cualquiera, sin autenticarse (el default actual de Hound Express, aunque no lo declaremos explícito) |
| `IsAuthenticated` | Solo usuarios con token/sesión válida |
| `IsAdminUser` | Solo `is_staff=True` |
| `IsAuthenticatedOrReadOnly` | Cualquiera puede leer (`GET`), solo autenticados pueden escribir (`POST`/`PATCH`/`DELETE`) |

`IsAuthenticatedOrReadOnly` es, probablemente, el ajuste más razonable para
`GuiaViewSet` si quisiéramos que cualquier sistema externo pueda **consultar** el
estatus de un envío (sin loguearse) pero solo un operador autenticado pueda
**crear/modificar** guías o estatus.

## JWT y Simple JWT

Con `Token` (lo de arriba), el servidor tiene que **guardar** cada token en una tabla
y consultarla en cada petición para saber a quién pertenece. **JWT** (*JSON Web
Token*) resuelve la autenticación sin esa consulta: el token mismo contiene la
información (usuario, fecha de expiración, etc.), firmada criptográficamente — el
servidor solo verifica la firma, no busca nada en la base de datos.

`Simple JWT` es la librería que agrega esto a DRF:

```bash
pip install djangorestframework-simplejwt
```

```python
# urls.py
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns += [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
```

`POST /api/token/` con `{"username": "...", "password": "..."}` regresa **dos**
tokens: uno de acceso (corta duración, el que mandas en cada petición) y uno de
refresco (larga duración, sirve para pedir un access token nuevo sin volver a mandar
la contraseña vía `/api/token/refresh/`).

**La desventaja real** (la que marca el módulo): como el servidor no guarda el token
en ninguna tabla, no hay un `Token.objects.filter(...).delete()` para "cerrarle la
sesión" a alguien a la fuerza — el token JWT sigue siendo válido hasta que expira por
sí solo. Mitigaciones típicas: tiempos de expiración cortos para el access token, y
listas negras (`blacklist`, que Simple JWT sí soporta como app opcional) para
tokens de refresco revocados explícitamente.

**Cuándo usar cada uno**: `Token` simple es más fácil de razonar y de revocar, bueno
para APIs internas o de tamaño moderado (como Hound Express hoy). JWT brilla cuando
tienes **múltiples servicios** verificando el mismo token sin compartir base de datos
(microservicios, ver [docs/22](22-rest-apis-fundamentos.md)) — cada servicio valida
la firma localmente, sin necesitar una consulta central.

---

## Autoevaluación (Módulo 64)

1. **¿Qué es la autenticación básica en DRF?**
   Usuario/contraseña codificados en Base64 en el header — simple de configurar,
   pero insegura sin HTTPS. → [Autenticación Básica](#autenticación-básica-y-por-qué-no-para-producción)

2. **¿Por qué no es adecuada para producción?**
   Base64 no es cifrado — es reversible al instante; las credenciales viajan
   expuestas en cada petición.

3. **¿Qué es la autenticación por tokens y por qué es más segura?**
   Un token representa al usuario tras loguearse una vez; no hace falta reenviar la
   contraseña en cada petición, y el token se puede revocar sin cambiarla. → [Autenticación por tokens](#autenticación-por-tokens)

4. **¿Cómo se implementa un registro de usuarios?**
   Con un serializer que valida datos (contraseñas coincidentes, email único) y una
   vista que lo use para crear el `User` — mismo patrón que ya vimos con
   `UsuarioSerializer` en este proyecto, aplicado a autenticación real.

5. **¿Qué es JWT y cuáles son sus ventajas?**
   Token autocontenido y firmado; el servidor no necesita guardar nada ni consultar
   la base de datos para validarlo — eficiente y sin dependencia de estado. → [JWT y Simple JWT](#jwt-y-simple-jwt)

6. **¿Cómo se configura JWT en Django?**
   Con `djangorestframework-simplejwt`, agregando `TokenObtainPairView`/
   `TokenRefreshView` a las URLs y `permission_classes`/`authentication_classes` en
   las vistas a proteger.

7. **¿Cuáles son las desventajas de JWT?**
   Difícil de revocar antes de que expire (no vive en una tabla que puedas borrar) —
   se mitiga con expiración corta y listas negras de refresh tokens.

8. **¿Qué herramientas prueban la autenticación?**
   Postman (o `curl`), mandando el token en el header `Authorization` tras
   obtenerlo del endpoint de login. → [docs/22](22-rest-apis-fundamentos.md#probar-la-api-con-postman)

9. **¿Cómo mejora la gestión de usuarios la autenticación por tokens?**
   Automatiza obtener credenciales válidas una sola vez (login) en vez de
   validarlas en cada petición, simplificando tanto la seguridad como la
   experiencia de quien consume la API.

## Ejemplo de uso en el mercado laboral

- **E-commerce**: tokens/JWT protegen checkout y datos de pago — solo un usuario
  autenticado puede completar una compra o ver su historial de pedidos.
- **Streaming**: JWT gestiona acceso a contenido exclusivo sin golpear la base de
  datos en cada solicitud de video, crítico a la escala de esas plataformas.

## Cómo se vería aplicado a Hound Express

Hoy, `GuiaViewSet`, `EstatusViewSet` y `UsuarioViewSet` no tienen
`permission_classes` — cualquiera puede operar la API sin loguearse (lo señalamos ya
en [docs/13](13-vistas-crud-y-consultas.md#login_required-y-autenticación-en-una-api),
[docs/15](15-cbv-mixins-formularios.md#loginrequiredmixin) y
[docs/24](24-paginacion-y-seguridad-drf.md#renders-y-seguridad-de-api)). El cambio
mínimo, usando lo de este módulo, sería:

1. Instalar `djangorestframework-simplejwt` y activar sus dos endpoints de token.
2. Agregar a cada `ViewSet`:
   ```python
   authentication_classes = [JWTAuthentication]
   permission_classes = [IsAuthenticatedOrReadOnly]
   ```
3. El Front primero llama `POST /api/token/` con las credenciales de un `Usuario`
   (una vez convertido en el `AUTH_USER_MODEL` real, como se discutió en
   [docs/16](16-usuarios-personalizados-y-templates.md)), y manda el `access` token
   recibido en cada llamada posterior a `crear-guia`, `actualizar-guia`, etc.

No lo implementamos todavía porque no formaba parte de ninguna entrega pedida — queda
documentado como el siguiente paso natural de seguridad para este proyecto.
