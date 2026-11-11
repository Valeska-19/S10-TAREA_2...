# facturacion/views.py · Vistas basadas en funciones + @login_required
# GET → muestra (lista / form / confirmación)  |  POST → guarda/actualiza/borra + redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (CategoriaForm, ClienteForm, MarcaForm, PerfilForm,
                    ProductoForm)
from .models import Categoria, Cliente, Marca, Perfil, Producto


# ---------- MARCAS ----------
@login_required
def marca_lista(request):                                  # READ · solo GET
    q = request.GET.get("q", "").strip()
    marcas = Marca.objects.all()
    if q:
        marcas = marcas.filter(nombre__icontains=q)
    return render(request, "facturacion/marca_lista.html",
                  {"titulo": "Marcas", "marcas": marcas, "q": q})


@login_required
def marca_crear(request):                                  # CREATE
    if request.method == "POST":                           # POST: guardar
        form = MarcaForm(request.POST)
        if form.is_valid():
            marca = form.save()
            messages.success(request, f"Marca «{marca.nombre}» creada correctamente.")
            return redirect("facturacion:marca_lista")
        messages.error(request, "No se pudo crear la marca. Revisa los campos.")
    else:                                                  # GET: formulario vacío
        form = MarcaForm()
    return render(request, "facturacion/marca_form.html",
                  {"titulo": "Nueva marca", "form": form, "boton": "Guardar"})


@login_required
def marca_editar(request, pk):                             # UPDATE
    marca = get_object_or_404(Marca, pk=pk)
    if request.method == "POST":                           # POST: actualizar
        form = MarcaForm(request.POST, instance=marca)
        if form.is_valid():
            form.save()
            messages.success(request, f"Marca «{marca.nombre}» actualizada.")
            return redirect("facturacion:marca_lista")
        messages.error(request, "No se pudo actualizar la marca. Revisa los campos.")
    else:                                                  # GET: formulario lleno
        form = MarcaForm(instance=marca)
    return render(request, "facturacion/marca_form.html",
                  {"titulo": f"Editar marca: {marca.nombre}", "form": form, "boton": "Actualizar"})


@login_required
def marca_eliminar(request, pk):                           # DELETE
    marca = get_object_or_404(Marca, pk=pk)
    if request.method == "POST":                           # POST: borrar
        try:
            nombre = marca.nombre
            marca.delete()
            messages.success(request, f"Marca «{nombre}» eliminada.")
        except ProtectedError:                             # PROTECT: la marca tiene productos
            messages.error(request, f"No se puede eliminar «{marca.nombre}» porque tiene productos. Desactívala en su lugar.")
        return redirect("facturacion:marca_lista")
    return render(request, "facturacion/marca_eliminar.html",    # GET: pregunta "¿Seguro?"
                  {"titulo": "Eliminar marca", "marca": marca})


# ---------- PRODUCTOS ----------
@login_required
def producto_lista(request):                               # READ · solo GET
    q = request.GET.get("q", "").strip()
    productos = Producto.objects.select_related("marca").prefetch_related("categorias")
    if q:
        productos = productos.filter(nombre__icontains=q)
    paginador = Paginator(productos, 5)
    page_obj = paginador.get_page(request.GET.get("page"))
    return render(request, "facturacion/producto_lista.html",
                  {"titulo": "Productos", "page_obj": page_obj, "q": q})


@login_required
def producto_crear(request):                               # CREATE
    if request.method == "POST":
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()                         # Guarda el producto y sus categorías (N:M)
            messages.success(request, f"Producto «{producto.nombre}» creado.")
            return redirect("facturacion:producto_lista")
        messages.error(request, "No se pudo crear el producto. Revisa los campos.")
    else:
        form = ProductoForm()
    return render(request, "facturacion/producto_form.html",
                  {"titulo": "Nuevo producto", "form": form, "boton": "Guardar"})


@login_required
def producto_editar(request, pk):                          # UPDATE
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f"Producto «{producto.nombre}» actualizado.")
            return redirect("facturacion:producto_lista")
        messages.error(request, "Revisa los campos marcados en rojo.")
    else:
        form = ProductoForm(instance=producto)
    return render(request, "facturacion/producto_form.html",
                  {"titulo": f"Editar producto: {producto.nombre}", "form": form, "boton": "Actualizar"})


@login_required
def producto_detalle(request, pk):                         # READ (uno) · solo GET
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, "facturacion/producto_detalle.html", {"producto": producto})


@login_required
def producto_eliminar(request, pk):                        # DELETE
    # GET: pide confirmación y NO modifica datos. POST: elimina y redirige.
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f"Producto «{nombre}» eliminado.")
        return redirect("facturacion:producto_lista")
    return render(request, "facturacion/producto_eliminar.html",
                  {"titulo": "Eliminar producto", "producto": producto})


# ---------- CATEGORÍAS (Unidad 5) ----------
@login_required
def categoria_lista(request):
    # GET: lista + buscador por nombre. Cuenta productos de cada categoría.
    q = request.GET.get("q", "").strip()
    categorias = Categoria.objects.annotate(num_productos=Count("productos", distinct=True))
    if q:
        categorias = categorias.filter(nombre__icontains=q)
    return render(request, "facturacion/categoria_lista.html",
                  {"titulo": "Categorías", "categorias": categorias, "q": q})


@login_required
def categoria_crear(request):
    # GET: form vacío | POST: valida, guarda y redirige a la lista
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f"Categoría «{categoria.nombre}» creada correctamente.")
            return redirect("facturacion:categoria_lista")
        messages.error(request, "No se pudo guardar. Revisa los campos marcados en rojo.")
    else:
        form = CategoriaForm()
    return render(request, "facturacion/categoria_form.html",
                  {"titulo": "Nueva categoría", "form": form, "boton": "Guardar"})


@login_required
def categoria_editar(request, pk):
    # GET: form con datos actuales | POST: actualiza y redirige
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, f"Categoría «{categoria.nombre}» actualizada.")
            return redirect("facturacion:categoria_lista")
        messages.error(request, "No se pudo actualizar. Revisa los campos marcados en rojo.")
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, "facturacion/categoria_form.html",
                  {"titulo": f"Editar categoría: {categoria.nombre}", "form": form, "boton": "Actualizar"})


@login_required
def categoria_eliminar(request, pk):
    # GET: confirma | POST: borra (los productos se quedan, solo se quita la relación)
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        nombre = categoria.nombre
        categoria.delete()
        messages.success(request, f"Categoría «{nombre}» eliminada.")
        return redirect("facturacion:categoria_lista")
    return render(request, "facturacion/categoria_eliminar.html",
                  {"titulo": "Eliminar categoría", "categoria": categoria,
                   "num_productos": categoria.productos.count()})


# ---------- CLIENTES (Unidad 5) ----------
@login_required
def cliente_lista(request):
    # GET: buscador (apellidos, nombres o cédula) + paginación de 5
    q = request.GET.get("q", "").strip()
    clientes = Cliente.objects.all()
    if q:
        clientes = clientes.filter(
            Q(apellidos__icontains=q) | Q(nombres__icontains=q) | Q(cedula__startswith=q)
        )
    page_obj = Paginator(clientes, 5).get_page(request.GET.get("page"))
    return render(request, "facturacion/cliente_lista.html",
                  {"titulo": "Clientes", "page_obj": page_obj, "q": q})


@login_required
def cliente_detalle(request, pk):
    # GET: ficha de un cliente
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, "facturacion/cliente_detalle.html",
                  {"titulo": "Cliente", "cliente": cliente})


@login_required
def cliente_crear(request):
    # GET: form vacío | POST: valida (cédula 10 dígitos) y guarda
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f"Cliente «{cliente}» creado correctamente.")
            return redirect("facturacion:cliente_lista")
        messages.error(request, "No se pudo guardar. Revisa los campos marcados en rojo.")
    else:
        form = ClienteForm()
    return render(request, "facturacion/cliente_form.html",
                  {"titulo": "Nuevo cliente", "form": form, "boton": "Guardar"})


@login_required
def cliente_editar(request, pk):
    # GET: form con datos | POST: actualiza
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f"Cliente «{cliente}» actualizado.")
            return redirect("facturacion:cliente_lista")
        messages.error(request, "No se pudo actualizar. Revisa los campos marcados en rojo.")
    else:
        form = ClienteForm(instance=cliente)
    return render(request, "facturacion/cliente_form.html",
                  {"titulo": f"Editar cliente: {cliente}", "form": form, "boton": "Actualizar"})


@login_required
def cliente_eliminar(request, pk):
    # GET: confirma | POST: borra
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        nombre = str(cliente)
        cliente.delete()
        messages.success(request, f"Cliente «{nombre}» eliminado.")
        return redirect("facturacion:cliente_lista")
    return render(request, "facturacion/cliente_eliminar.html",
                  {"titulo": "Eliminar cliente", "cliente": cliente})


# ---------- MI PERFIL (1:1) ----------
@login_required
def mi_perfil(request):
    # Sin pk: siempre el perfil del usuario conectado
    # GET: form con datos | POST: guarda y vuelve aquí
    perfil, creado = Perfil.objects.get_or_create(usuario=request.user)
    if request.method == "POST":
        form = PerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, "Tu perfil se actualizó correctamente.")
            return redirect("facturacion:mi_perfil")
        messages.error(request, "No se pudo guardar. Revisa los campos marcados en rojo.")
    else:
        form = PerfilForm(instance=perfil)
    return render(request, "facturacion/perfil_form.html",
                  {"titulo": "Mi perfil", "form": form, "boton": "Actualizar", "perfil": perfil})
