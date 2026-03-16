from django.urls import path

from . import views

urlpatterns = [
    path('', views.world_list, name='world_list'),
    path('new/', views.world_create, name='world_create'),
    path('<int:world_id>/timeline/', views.world_timeline, name='world_timeline'),
    path('<int:world_id>/post/', views.post_create, name='post_create'),
    path('<int:world_id>/moderation/', views.world_moderation, name='world_moderation'),
    path('<int:world_id>/edit/', views.world_edit, name='world_edit'),
    path('<int:world_id>/delete/', views.world_delete, name='world_delete'),
    path('<int:world_id>/characters/', views.character_list, name='character_list'),
    path('<int:world_id>/characters/new/', views.character_create, name='character_create'),
    path('<int:world_id>/characters/bring-in/', views.character_bring_in, name='character_bring_in'),
    path('<int:world_id>/characters/<int:character_id>/edit/', views.character_edit, name='character_edit'),
    path('<int:world_id>/characters/<int:character_id>/delete/', views.character_delete, name='character_delete'),
]
