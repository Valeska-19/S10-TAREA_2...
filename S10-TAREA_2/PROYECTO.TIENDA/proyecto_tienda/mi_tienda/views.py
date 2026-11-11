import re
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST



def home(request):
    nombre = ""
    error_nombre = ""
    valor_nombre = ""

    if request.method == "POST":
        valor_nombre = " ".join(
            request.POST.get("nombre", "").split()
        )

        patron = (
            r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+"
            r"(?:[ '-][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*"
        )

        if not valor_nombre:
            error_nombre = "Debes ingresar tu nombre."

        elif not 2 <= len(valor_nombre) <= 60:
            error_nombre = "El nombre debe tener entre 2 y 60 caracteres."

        elif not re.fullmatch(patron, valor_nombre):
            error_nombre = "El nombre solo puede contener letras, espacios, guiones y apóstrofos."

        else:
            nombre = valor_nombre

    contexto = {
        "titulo": "Mi Tienda",
        "nombre": nombre,
        "error_nombre": error_nombre,
        "valor_nombre": valor_nombre,
        "productos": ["Laptop", "Mouse", "Teclado"],
    }

    return render(request, "home.html", contexto)



def ingresar(request):
    # LOGIN · GET muestra formulario; POST valida y crea sesión
    if request.user.is_authenticated:
        return redirect("home")
    siguiente = request.POST.get("next") or request.GET.get("next") or ""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            usuario = form.get_user()
            login(request, usuario)
            messages.success(request, f"Hola, {usuario.username}.")
            if siguiente and url_has_allowed_host_and_scheme(siguiente, allowed_hosts={request.get_host()}):
                return redirect(siguiente)
            return redirect("home")
    else:
        form = AuthenticationForm(request)
    return render(request, "registration/login.html", {"form": form, "next": siguiente})


@require_POST
def salir(request):
    # LOGOUT · solo POST
    logout(request)
    messages.info(request, "Cerraste sesión.")
    return redirect("login")


def registro(request):
    # REGISTRO · GET formulario vacío; POST crea usuario e inicia sesión
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(request, f"¡Bienvenido, {usuario.username}! Tu cuenta fue creada.")
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "registration/registro.html", {"form": form})
