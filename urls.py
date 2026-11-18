from django.urls import path
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [
    # Главная страница
    path("", views.index, name="index"),

    # Учебные группы
    path("groups/", views.group_list, name="group_list"),
    path("groups/<int:pk>/", views.group_detail, name="group_detail"),

    # Личный кабинет и запись на вождение
    path("cabinet/", views.cabinet, name="cabinet"),
    path("booking/<int:slot_id>/", views.booking_create, name="booking"),

    # Информационные страницы
    path("prices/", views.prices, name="prices"),
    path("contacts/", views.contacts, name="contacts"),
    path("policy/", views.policy, name="policy"),

    # Авторизация
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="index"),
        name="logout",
    ),
]
