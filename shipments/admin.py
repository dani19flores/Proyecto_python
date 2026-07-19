from django.contrib import admin

from .models import Shipment, ShipmentStatusEvent


class ShipmentStatusEventInline(admin.TabularInline):
    model = ShipmentStatusEvent
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = [
        'tracking_number', 'recipient_name', 'current_status', 'created_at',
    ]
    list_filter = ['current_status']
    search_fields = ['tracking_number', 'recipient_name', 'sender_name']
    readonly_fields = ['tracking_number', 'current_status', 'created_at', 'updated_at']
    inlines = [ShipmentStatusEventInline]


@admin.register(ShipmentStatusEvent)
class ShipmentStatusEventAdmin(admin.ModelAdmin):
    list_display = ['shipment', 'status', 'location', 'created_at']
    list_filter = ['status']
    readonly_fields = ['created_at']
