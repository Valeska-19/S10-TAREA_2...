from django.contrib import admin
from django.urls import include, path
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("login/", views.ingresar, name="login"),
    path("logout/", views.salir, name="logout"),
    path("registro/", views.registro, name="registro"),
    path("facturacion/", include("facturacion.urls")),
]
