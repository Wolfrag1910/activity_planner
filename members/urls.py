from django.contrib.auth.views import LogoutView
from django.urls import path

from . import admin_pages, pages, views

urlpatterns = [
    path("login/", views.login_page, name="login"),
    path("login/email/", views.request_sign_in_link, name="request_sign_in_link"),
    path("login/link/<str:uidb64>/<str:token>/", views.sign_in_with_link, name="sign_in_link"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("invite/<str:token>/", views.invite_page, name="invite"),
    path("invite/<str:token>/email/", views.invite_email, name="invite_email"),
    path("invite/<str:token>/confirm/<str:payload>/", views.invite_confirm, name="invite_confirm"),
    path("me/", pages.profile, name="me"),
    path("me/edit/", pages.profile_edit, name="profile_edit"),
    path("members/", pages.members_list, name="members"),
    path("members/<int:pk>/", pages.member_detail, name="member"),
    path("admin/", admin_pages.admin_page, name="admin_page"),
    path("admin/invites/", admin_pages.create_invite, name="create_invite"),
    path("admin/invites/<int:pk>/cancel/", admin_pages.cancel_invite, name="cancel_invite"),
    path("admin/members/<int:pk>/deactivate/", admin_pages.set_member_active, {"active": False}, name="deactivate_member"),
    path("admin/members/<int:pk>/reactivate/", admin_pages.set_member_active, {"active": True}, name="reactivate_member"),
]
