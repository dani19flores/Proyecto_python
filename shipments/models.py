import uuid

from django.db import models


class ShipmentStatus(models.TextChoices):
    CREATED = 'created', 'Creado'
    PICKED_UP = 'picked_up', 'Recolectado'
    IN_TRANSIT = 'in_transit', 'En tránsito'
    OUT_FOR_DELIVERY = 'out_for_delivery', 'En reparto'
    DELIVERED = 'delivered', 'Entregado'
    FAILED_ATTEMPT = 'failed_attempt', 'Intento fallido'
    RETURNED = 'returned', 'Devuelto'
    CANCELLED = 'cancelled', 'Cancelado'


class Shipment(models.Model):
    tracking_number = models.CharField(max_length=32, unique=True, editable=False)
    sender_name = models.CharField(max_length=150)
    sender_address = models.CharField(max_length=255)
    recipient_name = models.CharField(max_length=150)
    recipient_address = models.CharField(max_length=255)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2)
    current_status = models.CharField(
        max_length=20, choices=ShipmentStatus.choices, default=ShipmentStatus.CREATED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.tracking_number

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = f'HE{uuid.uuid4().hex[:10].upper()}'
        super().save(*args, **kwargs)


class ShipmentStatusEvent(models.Model):
    shipment = models.ForeignKey(
        Shipment, on_delete=models.CASCADE, related_name='status_events'
    )
    status = models.CharField(max_length=20, choices=ShipmentStatus.choices)
    location = models.CharField(max_length=255, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.shipment.tracking_number} - {self.get_status_display()}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.shipment.current_status = self.status
        self.shipment.save(update_fields=['current_status', 'updated_at'])
