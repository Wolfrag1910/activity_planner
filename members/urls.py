from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login_page, name="login"),
    path("login/email/", views.request_sign_in_link, name="request_sign_in_link"),
    path("login/link/<str:uidb64>/<str:token>/", views.sign_in_with_link, name="sign_in_link"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("invite/<str:token>/", views.invite_page, name="invite"),
    path("invite/<str:token>/email/", views.invite_email, name="invite_email"),
    path("invite/<str:token>/confirm/<str:payload>/", views.invite_confirm, name="invite_confirm"),
]
