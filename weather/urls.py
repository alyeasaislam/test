from django.urls import path
from . import views

app_name = 'weather'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('favorites/', views.favorites, name='favorites'),
    path('add-favorite/', views.add_favorite, name='add_favorite'),
    path('remove-favorite/<int:favorite_id>/', views.remove_favorite, name='remove_favorite'),
] 