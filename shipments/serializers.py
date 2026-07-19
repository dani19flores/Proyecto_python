from rest_framework import serializers

from .models import Shipment, ShipmentStatusEvent


class ShipmentStatusEventSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ShipmentStatusEvent
        fields = [
            'id', 'shipment', 'status', 'status_display',
            'location', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ShipmentSerializer(serializers.ModelSerializer):
    current_status_display = serializers.CharField(
        source='get_current_status_display', read_only=True
    )

    class Meta:
        model = Shipment
        fields = [
            'id', 'tracking_number', 'sender_name', 'sender_address',
            'recipient_name', 'recipient_address', 'weight_kg',
            'current_status', 'current_status_display',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tracking_number', 'current_status', 'created_at', 'updated_at']


class ShipmentDetailSerializer(ShipmentSerializer):
    status_events = ShipmentStatusEventSerializer(many=True, read_only=True)

    class Meta(ShipmentSerializer.Meta):
        fields = ShipmentSerializer.Meta.fields + ['status_events']
