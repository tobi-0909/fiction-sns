from django.urls import path

from . import views

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("settings/", views.profile_settings, name="profile_settings"),
    path("follow-requests/", views.follow_request_list, name="follow_request_list"),
    path("u/<str:handle>/", views.public_profile, name="public_profile"),
    path("u/<str:handle>/following/", views.following_list, name="following_list"),
    path("u/<str:handle>/followers/", views.follower_list, name="follower_list"),
    path("u/<str:handle>/follow/", views.follow_create, name="follow_create"),
    path("u/<str:handle>/unfollow/", views.follow_delete, name="follow_delete"),
    path("u/<str:handle>/follow-accept/", views.follow_accept, name="follow_accept"),
    path("u/<str:handle>/follow-reject/", views.follow_reject, name="follow_reject"),
    path("u/<int:user_id>/block/", views.block_user, name="block_user"),
    path("u/<int:user_id>/unblock/", views.unblock_user, name="unblock_user"),
]
