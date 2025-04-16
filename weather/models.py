from django.db import models
from django.contrib.auth.models import User

class FavoriteCity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_cities')
    city_name = models.CharField(max_length=100)
    country_code = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Favorite Cities"
        unique_together = ('user', 'city_name', 'country_code')
    
    def __str__(self):
        if self.country_code:
            return f"{self.city_name}, {self.country_code}"
        return self.city_name 