from django.db import models


class ModelModel(models.Model):
    id = models.AutoField(primary_key=True)


class LiteModelModel(models.Model):
    id = models.AutoField(primary_key=True)
