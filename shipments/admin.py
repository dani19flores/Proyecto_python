from django.contrib import admin

# Register your models here.
from .models import Estatus, Guia, Usuario

admin.site.register(Guia)
admin.site.register(Estatus)
admin.site.register(Usuario)
