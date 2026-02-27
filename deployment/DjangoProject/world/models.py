from django.db import models

# Create your models here.
class City(models.Model):
    name = models.CharField(max_length=120)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    long = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self) -> str:
        return self.name