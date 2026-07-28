from rest_framework.routers import DefaultRouter

from .views import EstatusViewSet, GuiaViewSet, UsuarioViewSet

router = DefaultRouter()
router.register('guias', GuiaViewSet, basename='guia')
router.register('estatus', EstatusViewSet, basename='estatus')
router.register('usuarios', UsuarioViewSet, basename='usuario')

urlpatterns = router.urls
