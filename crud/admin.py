from django.contrib import admin
from .models import Profile, Endpoint, DynamicData, UploadedImage

admin.site.register(Profile)
admin.site.register(Endpoint)
admin.site.register(DynamicData)
admin.site.register(UploadedImage)