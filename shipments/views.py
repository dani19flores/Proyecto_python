from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Shipment, ShipmentStatusEvent
from .serializers import (
    ShipmentDetailSerializer,
    ShipmentSerializer,
    ShipmentStatusEventSerializer,
)


class ShipmentViewSet(viewsets.ModelViewSet):
    queryset = Shipment.objects.prefetch_related('status_events').all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ShipmentDetailSerializer
        return ShipmentSerializer

    @action(detail=True, methods=['get'])
    def status_history(self, request, pk=None):
        shipment = self.get_object()
        events = shipment.status_events.all()
        serializer = ShipmentStatusEventSerializer(events, many=True)
        return Response(serializer.data)


class ShipmentStatusEventViewSet(viewsets.ModelViewSet):
    queryset = ShipmentStatusEvent.objects.select_related('shipment').all()
    serializer_class = ShipmentStatusEventSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        shipment_id = self.request.query_params.get('shipment')
        if shipment_id:
            queryset = queryset.filter(shipment_id=shipment_id)
        return queryset
