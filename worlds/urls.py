from django.urls import path

from . import views

urlpatterns = [
    path('', views.world_list, name='world_list'),
    path('new/', views.world_create, name='world_create'),
    path('<int:world_id>/edit/', views.world_edit, name='world_edit'),
    path('<int:world_id>/delete/', views.world_delete, name='world_delete'),
    path('<int:world_id>/characters/', views.character_list, name='character_list'),
    path('<int:world_id>/characters/new/', views.character_create, name='character_create'),
    path('<int:world_id>/characters/<int:character_id>/edit/', views.character_edit, name='character_edit'),
    path('<int:world_id>/characters/<int:character_id>/delete/', views.character_delete, name='character_delete'),
]
