from django.contrib import admin
from django.urls import path, include
from users.views import CustomLoginView, public_profile

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('users/', include('users.urls')),
    path('u/<str:handle>/', public_profile, name='public_profile'),
    path('worlds/', include('worlds.urls')),
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
]