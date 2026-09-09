from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import EstatusViewSet, GuiaViewSet, UsuarioViewSet

router = DefaultRouter()
router.register('guias', GuiaViewSet, basename='guia')
router.register('estatus', EstatusViewSet, basename='estatus')
router.register('usuarios', UsuarioViewSet, basename='usuario')

urlpatterns = [
    path('crear-guia', GuiaViewSet.as_view({'post': 'create'}), name='crear-guia'),
    path('actualizar-guia/<int:pk>', GuiaViewSet.as_view({'put': 'update', 'patch': 'partial_update'}), name='actualizar-guia'),
    path('obtener-guia/<int:pk>', GuiaViewSet.as_view({'get': 'retrieve'}), name='obtener-guia'),
    path('eliminar-guia/<int:pk>', GuiaViewSet.as_view({'delete': 'destroy'}), name='eliminar-guia'),
] + router.urls
