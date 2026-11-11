from django.contrib import admin
from .models import Categoria, Marca, Producto, Cliente, Perfil

admin.site.register(Categoria)
admin.site.register(Marca)
admin.site.register(Cliente)
admin.site.register(Perfil)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "marca", "precio", "stock", "activo")
    search_fields = ("nombre",)
    list_filter = ("marca", "categorias", "activo")
    filter_horizontal = ("categorias",)
