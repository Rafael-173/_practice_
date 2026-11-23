from django.urls import path
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [
    # Главная страница
    path("", views.index, name="index"),

    # Учебные группы
    path("groups/", views.group_list, name="group_list"),
    path("groups/<int:pk>/", views.group_detail, name="group_detail"),
    path("groups/<int:pk>/package-price/", views.package_price, name="package_price"),

    # Личный кабинет и запись на вождение (курсант)
    path("cabinet/", views.cabinet, name="cabinet"),
    path("booking/<int:slot_id>/", views.booking_create, name="booking"),
    path('checkout/<int:group_id>/', views.checkout, name='checkout'),

    # Информационные страницы
    path("prices/", views.prices, name="prices"),
    path("contacts/", views.contacts, name="contacts"),
    path("policy/", views.policy, name="policy"),

    # Авторизация курсанта
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

    # Инструктор
    path('instructor/login/', views.InstructorLoginView.as_view(), name='instructor_login'),
    path('instructor/register/', views.instructor_register, name='instructor_register'),
    path('instructor/cabinet/', views.instructor_cabinet, name='instructor_cabinet'),

    path("cars/", views.car_list, name="car_list"),
    path("cars/upload/", views.car_upload, name="car_upload"),
]