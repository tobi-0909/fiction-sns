from django.urls import path

from . import views

urlpatterns = [
    path('', views.world_list, name='world_list'),
    path('new/', views.world_create, name='world_create'),
    path('<int:world_id>/edit/', views.world_edit, name='world_edit'),
    path('<int:world_id>/delete/', views.world_delete, name='world_delete'),
]
