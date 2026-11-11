from django.urls import path
from . import views

app_name = "facturacion"      # En templates: {% url 'facturacion:...' %}

urlpatterns = [
    # ---------- MARCAS (Unidad 2) ----------
    path("marcas/", views.marca_lista, name="marca_lista"),
    path("marcas/crear/", views.marca_crear, name="marca_crear"),
    path("marcas/editar/<int:pk>/", views.marca_editar, name="marca_editar"),
    path("marcas/eliminar/<int:pk>/", views.marca_eliminar, name="marca_eliminar"),
    # ---------- PRODUCTOS (Unidad 3) ----------
    path("productos/", views.producto_lista, name="producto_lista"),
    path("productos/crear/", views.producto_crear, name="producto_crear"),
    path("productos/<int:pk>/", views.producto_detalle, name="producto_detalle"),
    path("productos/editar/<int:pk>/", views.producto_editar, name="producto_editar"),
    path("productos/eliminar/<int:pk>/", views.producto_eliminar, name="producto_eliminar"),
    # ---------- CATEGORÍAS (Unidad 5 · Tarea 1) ----------
    path("categorias/", views.categoria_lista, name="categoria_lista"),
    path("categorias/crear/", views.categoria_crear, name="categoria_crear"),
    path("categorias/editar/<int:pk>/", views.categoria_editar, name="categoria_editar"),
    path("categorias/eliminar/<int:pk>/", views.categoria_eliminar, name="categoria_eliminar"),
    # ---------- CLIENTES (Unidad 5 · Tarea 2) ----------
    path("clientes/", views.cliente_lista, name="cliente_lista"),
    path("clientes/crear/", views.cliente_crear, name="cliente_crear"),
    path("clientes/<int:pk>/", views.cliente_detalle, name="cliente_detalle"),
    path("clientes/editar/<int:pk>/", views.cliente_editar, name="cliente_editar"),
    path("clientes/eliminar/<int:pk>/", views.cliente_eliminar, name="cliente_eliminar"),
    # ---------- MI PERFIL (reto 1:1) · sin <int:pk>: siempre es el usuario conectado ----------
    path("mi-perfil/", views.mi_perfil, name="mi_perfil"),
]
