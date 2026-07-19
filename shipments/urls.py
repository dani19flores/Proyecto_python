from rest_framework.routers import DefaultRouter

from .views import ShipmentStatusEventViewSet, ShipmentViewSet

router = DefaultRouter()
router.register('shipments', ShipmentViewSet, basename='shipment')
router.register('status-events', ShipmentStatusEventViewSet, basename='status-event')

urlpatterns = router.urls
