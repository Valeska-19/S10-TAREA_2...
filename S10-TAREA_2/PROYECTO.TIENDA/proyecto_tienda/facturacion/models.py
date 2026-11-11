from django.contrib.auth.models import User
from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=60, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Marca(models.Model):
    # Lado "1" de la relación 1:N con Producto
    nombre = models.CharField(max_length=60, unique=True)
    pais_origen = models.CharField("País de origen", max_length=60, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField("Descripción", blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    # 1:N → una marca tiene muchos productos
    marca = models.ForeignKey(Marca, on_delete=models.PROTECT, related_name="productos")
    # N:M → un producto en varias categorías
    categorias = models.ManyToManyField(Categoria, related_name="productos", blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.marca})"


class Cliente(models.Model):
    cedula = models.CharField("Cédula", max_length=10, unique=True)
    nombres = models.CharField(max_length=80)
    apellidos = models.CharField(max_length=80)
    email = models.EmailField("Correo", blank=True)
    telefono = models.CharField("Teléfono", max_length=15, blank=True)
    direccion = models.CharField("Dirección", max_length=200, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["apellidos", "nombres"]

    def __str__(self):
        return f"{self.apellidos} {self.nombres}"


class Perfil(models.Model):
    # 1:1 con el User de Django
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    cedula = models.CharField("Cédula", max_length=10, blank=True)
    telefono = models.CharField("Teléfono", max_length=15, blank=True)
    direccion = models.CharField("Dirección", max_length=200, blank=True)
    cargo = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"

    def __str__(self):
        return f"Perfil de {self.usuario.username}"
