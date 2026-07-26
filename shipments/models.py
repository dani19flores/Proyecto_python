from django.db import models
from django.utils import timezone


class AutoDateTimeField(models.DateTimeField):
    """DateTimeField that updates to now() on every save, like auto_now,
    but still accepts an explicit default for use outside of save()."""

    def pre_save(self, model_instance, add):
        value = timezone.now()
        setattr(model_instance, self.attname, value)
        return value


class Guia(models.Model):
    id = models.IntegerField(primary_key=True)
    trackingNumber = models.CharField(max_length=15)
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    createdAt = models.DateField(default=timezone.now)
    updatedAt = AutoDateTimeField(default=timezone.now)
    currentStatus = models.CharField(max_length=20)

    class Meta:
        db_table = 'Guide'

    def __str__(self):
        return self.trackingNumber


class Estatus(models.Model):
    id = models.IntegerField(primary_key=True)
    guideId = models.IntegerField()
    status = models.CharField(max_length=20)
    timestamp = AutoDateTimeField(default=timezone.now)
    updatedBy = models.CharField(max_length=20)

    class Meta:
        db_table = 'StatusHistory'

    def __str__(self):
        return f'{self.guideId} - {self.status}'


class Usuario(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=50)
    password = models.CharField(max_length=20)
    createdAt = models.DateField(default=timezone.now)
    updatedAt = AutoDateTimeField(default=timezone.now)

    class Meta:
        db_table = 'User'

    def __str__(self):
        return self.name
