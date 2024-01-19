from django.contrib import admin
from .models import ModelModel, LiteModelModel

admin.site.register(ModelModel)
admin.site.register(LiteModelModel)