from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import shortuuid


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    image = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.user.username


def generate_short_token():
    return shortuuid.uuid()[:9]

class Endpoint(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    token = models.CharField(
        max_length=12,
        default=generate_short_token,
        unique=True,
        editable=False
    )
    schema = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_trashed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.user.username}"


class DynamicData(models.Model):
    endpoint = models.ForeignKey(Endpoint, on_delete=models.CASCADE)
    data = models.JSONField()
    serial_number = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            last = DynamicData.objects.filter(endpoint=self.endpoint).order_by('-serial_number').first()
            self.serial_number = (last.serial_number + 1) if last else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.endpoint.name} #{self.serial_number}"



class UploadedImage(models.Model):
    image = models.ImageField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

