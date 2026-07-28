from rest_framework import serializers

from .models import Estatus, Guia, Usuario


class GuiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guia
        fields = [
            'id', 'trackingNumber', 'origin', 'destination',
            'createdAt', 'updatedAt', 'currentStatus',
        ]
        read_only_fields = ['createdAt', 'updatedAt']

    def create(self, validated_data):
        # createdAt's default (timezone.now) is a datetime; refresh from DB so
        # it comes back as the date DateField actually stores, not the raw
        # in-memory datetime DRF refuses to serialize.
        instance = super().create(validated_data)
        instance.refresh_from_db()
        return instance


class EstatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estatus
        fields = ['id', 'guideId', 'status', 'timestamp', 'updatedBy']
        read_only_fields = ['timestamp']


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'name', 'email', 'password', 'createdAt', 'updatedAt']
        read_only_fields = ['createdAt', 'updatedAt']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Same createdAt datetime-vs-date issue as GuiaSerializer.
        instance = super().create(validated_data)
        instance.refresh_from_db()
        return instance
