from django import forms
from django.db.models import Q
from .models import Categoria, Cliente, Marca, Perfil, Producto


class MarcaForm(forms.ModelForm):
    class Meta:
        model = Marca
        fields = ["nombre", "pais_origen", "activo"]
        labels = {"nombre": "Nombre de la marca"}
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Samsung"}),
            "pais_origen": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Corea del Sur"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()
        if len(nombre) < 2:
            raise forms.ValidationError("El nombre debe tener al menos 2 letras.")
        return nombre.title()


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["nombre", "descripcion", "marca", "categorias", "precio", "stock", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Laptop Pro 14"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "marca": forms.Select(attrs={"class": "form-select"}),
            "categorias": forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
            "precio": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "stock": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Al editar, conservar la marca actual aunque se haya desactivado.
        # De otro modo, un POST sin cambiar marca produce un falso error.
        marcas = Marca.objects.filter(activo=True)
        if self.instance.pk and self.instance.marca_id:
            marcas = Marca.objects.filter(Q(activo=True) | Q(pk=self.instance.marca_id))
        self.fields["marca"].queryset = marcas.distinct()
        self.fields["marca"].empty_label = "— Elige una marca —"

    def clean_precio(self):
        precio = self.cleaned_data["precio"]
        if precio <= 0:
            raise forms.ValidationError("El precio debe ser mayor que 0.")
        return precio


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Laptops"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3,
                                                 "placeholder": "Descripción opcional"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_nombre(self):
        # Normaliza espacios y pone la primera letra en mayúscula.
        nombre = " ".join(self.cleaned_data["nombre"].split())
        if sum(letra.isalpha() for letra in nombre) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 letras.")
        if not nombre[0].isalpha():
            raise forms.ValidationError("El nombre debe comenzar con una letra.")
        nombre = nombre[0].upper() + nombre[1:]
        # unique=True es sensible a mayúsculas en algunas BD; evita
        # categorías duplicadas con variantes OFERTAS / Ofertas.
        repetidas = Categoria.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            repetidas = repetidas.exclude(pk=self.instance.pk)
        if repetidas.exists():
            raise forms.ValidationError("Ya existe una categoría con ese nombre.")
        return nombre


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["cedula", "nombres", "apellidos", "email", "telefono", "direccion"]
        widgets = {
            "cedula": forms.TextInput(attrs={"class": "form-control", "placeholder": "10 dígitos", "maxlength": "10"}),
            "nombres": forms.TextInput(attrs={"class": "form-control"}),
            "apellidos": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "correo@ejemplo.com"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "direccion": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_cedula(self):
        # Exactamente 10 caracteres y solo números
        cedula = self.cleaned_data["cedula"].strip()
        if len(cedula) != 10:
            raise forms.ValidationError("La cédula debe tener exactamente 10 dígitos.")
        if not cedula.isascii() or not cedula.isdigit():
            raise forms.ValidationError("La cédula debe tener solo números.")
        return cedula


class PerfilForm(forms.ModelForm):
    # Sin 'usuario': siempre es request.user
    class Meta:
        model = Perfil
        fields = ["cedula", "telefono", "direccion", "cargo"]
        widgets = {
            "cedula": forms.TextInput(attrs={"class": "form-control", "maxlength": "10"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "direccion": forms.TextInput(attrs={"class": "form-control"}),
            "cargo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Vendedor"}),
        }

    def clean_cedula(self):
        # El perfil admite cédula vacía; si se informa, debe tener 10 dígitos.
        cedula = self.cleaned_data["cedula"].strip()
        if cedula and (len(cedula) != 10 or not cedula.isascii() or not cedula.isdigit()):
            raise forms.ValidationError("La cédula debe tener exactamente 10 dígitos numéricos.")
        return cedula
