from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Estatus, Guia, Usuario
from .serializers import EstatusSerializer, GuiaSerializer, UsuarioSerializer


class GuiaViewSet(viewsets.ModelViewSet):
    queryset = Guia.objects.all()
    serializer_class = GuiaSerializer

    @action(detail=True, methods=['get'])
    def estatus_history(self, request, pk=None):
        guia = self.get_object()
        eventos = Estatus.objects.filter(guideId=guia.id)
        serializer = EstatusSerializer(eventos, many=True)
        return Response(serializer.data)


class EstatusViewSet(viewsets.ModelViewSet):
    queryset = Estatus.objects.all()
    serializer_class = EstatusSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        guide_id = self.request.query_params.get('guideId')
        if guide_id:
            queryset = queryset.filter(guideId=guide_id)
        return queryset


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
