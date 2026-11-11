"""Pruebas de regresión de la Tarea 2 (ejecutar: python manage.py test)."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import CategoriaForm, ClienteForm, PerfilForm, ProductoForm
from .models import Categoria, Cliente, Marca, Perfil, Producto


class BaseDatosDePrueba(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username="alumna", password="ClaveSeguraTest123!"
        )
        cls.otro_usuario = get_user_model().objects.create_user(
            username="otra", password="OtraClaveTest123!"
        )
        cls.marca = Marca.objects.create(nombre="Marca Prueba", activo=True)
        cls.inactiva = Marca.objects.create(nombre="Marca Antigua", activo=False)
        cls.categoria = Categoria.objects.create(nombre="Ofertas", descripcion="Promo")
        cls.segunda_categoria = Categoria.objects.create(nombre="Accesorios")
        cls.producto = Producto.objects.create(
            nombre="Producto prueba", marca=cls.marca, precio=Decimal("25.50"), stock=6
        )
        cls.producto.categorias.add(cls.categoria)
        cls.clientes = [
            Cliente.objects.create(
                cedula=f"09{i:08d}", nombres=f"Nombre{i}", apellidos=f"Apellido{i}"
            )
            for i in range(7)
        ]

    def autenticar(self):
        self.client.force_login(self.usuario)


class PruebasFormularios(BaseDatosDePrueba):
    def test_categoria_normaliza_espacios_y_mayuscula(self):
        form = CategoriaForm({"nombre": "  novedades   especiales  ", "descripcion": "", "activo": "on"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().nombre, "Novedades especiales")

    def test_categoria_rechaza_menos_de_tres_letras(self):
        for nombre in ("ab", "123", "1a2"):
            with self.subTest(nombre=nombre):
                form = CategoriaForm({"nombre": nombre})
                self.assertFalse(form.is_valid())
                self.assertIn("nombre", form.errors)

    def test_categoria_rechaza_duplicado_sin_importar_mayusculas(self):
        for nombre in ("Ofertas", "ofertas", "OFERTAS"):
            with self.subTest(nombre=nombre):
                form = CategoriaForm({"nombre": nombre})
                self.assertFalse(form.is_valid())
                self.assertIn("nombre", form.errors)

    def test_categoria_se_puede_editar_sin_cambiar_su_nombre(self):
        form = CategoriaForm(
            {"nombre": "Ofertas", "descripcion": "Actualizada"}, instance=self.categoria
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_cedula_debe_tener_diez_digitos_ascii(self):
        for cedula in ("12345", "12345abcde", "١٢٣٤٥٦٧٨٩٠"):
            with self.subTest(cedula=cedula):
                form = ClienteForm({"cedula": cedula, "nombres": "Ana", "apellidos": "López"})
                self.assertFalse(form.is_valid())
                self.assertIn("cedula", form.errors)
        valida = ClienteForm({"cedula": "1234567890", "nombres": "Ana", "apellidos": "López"})
        self.assertTrue(valida.is_valid(), valida.errors)

    def test_cedula_repetida_se_rechaza(self):
        form = ClienteForm({
            "cedula": self.clientes[0].cedula, "nombres": "Duplicada", "apellidos": "Prueba"
        })
        self.assertFalse(form.is_valid())
        self.assertIn("cedula", form.errors)

    def test_precio_debe_ser_positivo(self):
        form = ProductoForm({
            "nombre": "Mal precio", "marca": self.marca.pk,
            "precio": "0.00", "stock": 0
        })
        self.assertFalse(form.is_valid())
        self.assertIn("precio", form.errors)

    def test_edicion_permite_marca_inactiva_ya_asignada(self):
        producto = Producto.objects.create(
            nombre="Histórico", marca=self.inactiva, precio=Decimal("10.00")
        )
        form = ProductoForm({
            "nombre": "Histórico editado", "marca": self.inactiva.pk,
            "precio": "11.00", "stock": "2"
        }, instance=producto)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        producto.refresh_from_db()
        self.assertEqual(producto.marca, self.inactiva)

    def test_producto_nuevo_no_acepta_marca_inactiva(self):
        form = ProductoForm({
            "nombre": "Nuevo", "marca": self.inactiva.pk,
            "precio": "12.00", "stock": "1"
        })
        self.assertFalse(form.is_valid())
        self.assertIn("marca", form.errors)

    def test_perfil_cedula_opcional_pero_validada(self):
        perfil = Perfil.objects.create(usuario=self.usuario)
        form = PerfilForm({"cedula": "abcd", "cargo": "Vendedor"}, instance=perfil)
        self.assertFalse(form.is_valid())
        form = PerfilForm({"cedula": "", "cargo": "Vendedor"}, instance=perfil)
        self.assertTrue(form.is_valid(), form.errors)


class PruebasSeguridad(BaseDatosDePrueba):
    def test_todas_las_vistas_de_facturacion_exigen_sesion(self):
        rutas = [
            ("marca_lista", []), ("marca_crear", []),
            ("marca_editar", [self.marca.pk]), ("marca_eliminar", [self.marca.pk]),
            ("producto_lista", []), ("producto_crear", []),
            ("producto_detalle", [self.producto.pk]),
            ("producto_editar", [self.producto.pk]),
            ("producto_eliminar", [self.producto.pk]),
            ("categoria_lista", []), ("categoria_crear", []),
            ("categoria_editar", [self.categoria.pk]),
            ("categoria_eliminar", [self.categoria.pk]),
            ("cliente_lista", []), ("cliente_crear", []),
            ("cliente_detalle", [self.clientes[0].pk]),
            ("cliente_editar", [self.clientes[0].pk]),
            ("cliente_eliminar", [self.clientes[0].pk]),
            ("mi_perfil", []),
        ]
        for nombre, argumentos in rutas:
            url = reverse(f"facturacion:{nombre}", args=argumentos)
            with self.subTest(url=url):
                respuesta = self.client.get(url)
                self.assertEqual(respuesta.status_code, 302)
                self.assertIn("/login/", respuesta["Location"])

    def test_logout_no_cierra_sesion_por_get(self):
        self.autenticar()
        url = reverse("logout")
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertEqual(self.client.get(reverse("facturacion:cliente_lista")).status_code, 302)

    def test_registro_y_login(self):
        registro = self.client.post(reverse("registro"), {
            "username": "nuevousuario", "password1": "ClaveLargaNueva123!",
            "password2": "ClaveLargaNueva123!",
        })
        self.assertRedirects(registro, reverse("home"))
        self.assertTrue(get_user_model().objects.filter(username="nuevousuario").exists())
        self.assertEqual(self.client.get(reverse("facturacion:categoria_lista")).status_code, 200)

    def test_login_no_redirige_a_un_sitio_externo(self):
        respuesta = self.client.post(reverse("login"), {
            "username": "alumna", "password": "ClaveSeguraTest123!",
            "next": "https://ejemplo-externo.com/"
        })
        self.assertRedirects(respuesta, reverse("home"))

    def test_formularios_mutables_exigen_csrf(self):
        from django.test import Client
        self.autenticar()
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)
        urls = [
            reverse("facturacion:categoria_crear"),
            reverse("facturacion:cliente_crear"),
            reverse("facturacion:categoria_eliminar", args=[self.categoria.pk]),
            reverse("facturacion:cliente_eliminar", args=[self.clientes[0].pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(cliente.post(url, {}).status_code, 403)


class PruebasCategorias(BaseDatosDePrueba):
    def setUp(self):
        self.autenticar()

    def test_lista_buscador_y_cuenta_productos(self):
        respuesta = self.client.get(reverse("facturacion:categoria_lista"), {"q": "ofert"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Ofertas")
        self.assertNotContains(respuesta, "Accesorios")
        self.assertEqual(respuesta.context["categorias"][0].num_productos, 1)

    def test_crud_get_post_y_confirmacion(self):
        lista = reverse("facturacion:categoria_lista")
        crear = reverse("facturacion:categoria_crear")
        self.assertEqual(self.client.get(crear).status_code, 200)
        respuesta = self.client.post(crear, {
            "nombre": "  perifericos  ", "descripcion": "Para PC", "activo": "on"
        })
        self.assertRedirects(respuesta, lista)
        categoria = Categoria.objects.get(nombre="Perifericos")
        editar = reverse("facturacion:categoria_editar", args=[categoria.pk])
        self.assertEqual(self.client.get(editar).status_code, 200)
        self.assertRedirects(self.client.post(editar, {
            "nombre": "Perifericos", "descripcion": "Actualizados", "activo": "on"
        }), lista)
        categoria.refresh_from_db()
        self.assertEqual(categoria.descripcion, "Actualizados")
        eliminar = reverse("facturacion:categoria_eliminar", args=[categoria.pk])
        self.assertEqual(self.client.get(eliminar).status_code, 200)
        self.assertTrue(Categoria.objects.filter(pk=categoria.pk).exists())
        self.assertRedirects(self.client.post(eliminar), lista)
        self.assertFalse(Categoria.objects.filter(pk=categoria.pk).exists())

    def test_eliminar_categoria_mantiene_producto_y_quita_relacion(self):
        url = reverse("facturacion:categoria_eliminar", args=[self.categoria.pk])
        self.assertContains(self.client.get(url), "Se quitará de")
        self.client.post(url)
        self.assertTrue(Producto.objects.filter(pk=self.producto.pk).exists())
        self.assertEqual(self.producto.categorias.count(), 0)

    def test_repetido_retorna_error_sin_guardar(self):
        anterior = Categoria.objects.count()
        respuesta = self.client.post(reverse("facturacion:categoria_crear"), {"nombre": "ofertas"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Ya existe una categoría")
        self.assertEqual(Categoria.objects.count(), anterior)


class PruebasClientes(BaseDatosDePrueba):
    def setUp(self):
        self.autenticar()

    def test_paginacion_cinco_y_busqueda_sin_perder_q(self):
        url = reverse("facturacion:cliente_lista")
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.context["page_obj"]), 5)
        self.assertContains(respuesta, "Página 1 de 2")
        respuesta = self.client.get(url, {"page": "2"})
        self.assertEqual(len(respuesta.context["page_obj"]), 2)
        self.assertEqual(respuesta.context["page_obj"].number, 2)
        respuesta = self.client.get(url, {"q": "Apellido", "page": "1"})
        self.assertContains(respuesta, "q=Apellido")
        self.assertEqual(respuesta.context["page_obj"].paginator.count, 7)

    def test_busqueda_apellidos_y_cedula_con_q(self):
        url = reverse("facturacion:cliente_lista")
        self.assertEqual(self.client.get(url, {"q": "Apellido1"}).context["page_obj"].paginator.count, 1)
        self.assertEqual(self.client.get(url, {"q": self.clientes[0].cedula}).context["page_obj"].paginator.count, 1)

    def test_crear_editar_eliminar_no_duplica_con_get(self):
        lista = reverse("facturacion:cliente_lista")
        crear = reverse("facturacion:cliente_crear")
        self.assertEqual(self.client.get(crear).status_code, 200)
        datos = {"cedula": "1234567890", "nombres": "Natalia", "apellidos": "Medina", "email": ""}
        respuesta = self.client.post(crear, datos)
        self.assertRedirects(respuesta, lista)
        cliente = Cliente.objects.get(cedula="1234567890")
        self.client.get(lista)
        self.assertEqual(Cliente.objects.filter(cedula="1234567890").count(), 1)
        editar = reverse("facturacion:cliente_editar", args=[cliente.pk])
        self.assertEqual(self.client.get(editar).status_code, 200)
        self.assertRedirects(self.client.post(editar, {**datos, "apellidos": "Morales"}), lista)
        cliente.refresh_from_db()
        self.assertEqual(cliente.apellidos, "Morales")
        eliminar = reverse("facturacion:cliente_eliminar", args=[cliente.pk])
        self.assertEqual(self.client.get(eliminar).status_code, 200)
        self.assertTrue(Cliente.objects.filter(pk=cliente.pk).exists())
        self.assertRedirects(self.client.post(eliminar), lista)
        self.assertFalse(Cliente.objects.filter(pk=cliente.pk).exists())

    def test_cedula_erronea_no_crea_clientes(self):
        anterior = Cliente.objects.count()
        respuesta = self.client.post(reverse("facturacion:cliente_crear"), {
            "cedula": "ab123", "nombres": "Ana", "apellidos": "Torres"
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "10 dígitos")
        self.assertEqual(Cliente.objects.count(), anterior)


class PruebasProductosYMarcas(BaseDatosDePrueba):
    def setUp(self):
        self.autenticar()

    def test_marca_protegida_no_provoca_error_500(self):
        url = reverse("facturacion:marca_eliminar", args=[self.marca.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        respuesta = self.client.post(url)
        self.assertRedirects(respuesta, reverse("facturacion:marca_lista"))
        self.assertTrue(Marca.objects.filter(pk=self.marca.pk).exists())

    def test_producto_creacion_y_relacion_muchos_a_muchos(self):
        datos = {
            "nombre": "Auriculares", "descripcion": "Prueba", "marca": self.marca.pk,
            "categorias": [self.categoria.pk, self.segunda_categoria.pk],
            "precio": "19.90", "stock": "3", "activo": "on",
        }
        respuesta = self.client.post(reverse("facturacion:producto_crear"), datos)
        self.assertRedirects(respuesta, reverse("facturacion:producto_lista"))
        producto = Producto.objects.get(nombre="Auriculares")
        self.assertEqual(producto.categorias.count(), 2)
        self.assertEqual(producto.precio, Decimal("19.90"))
        editar = reverse("facturacion:producto_editar", args=[producto.pk])
        self.assertRedirects(self.client.post(editar, {**datos, "precio": "20.99"}),
                             reverse("facturacion:producto_lista"))
        producto.refresh_from_db()
        self.assertEqual(producto.precio, Decimal("20.99"))
        eliminar = reverse("facturacion:producto_eliminar", args=[producto.pk])
        self.assertEqual(self.client.get(eliminar).status_code, 200)
        self.assertRedirects(self.client.post(eliminar), reverse("facturacion:producto_lista"))
        self.assertFalse(Producto.objects.filter(pk=producto.pk).exists())

    def test_marca_crud(self):
        datos = {"nombre": "NuevaMarca", "pais_origen": "Ecuador", "activo": "on"}
        self.assertRedirects(self.client.post(reverse("facturacion:marca_crear"), datos),
                             reverse("facturacion:marca_lista"))
        marca = Marca.objects.get(nombre="Nuevamarca")
        self.assertRedirects(self.client.post(reverse("facturacion:marca_editar", args=[marca.pk]),
                                              {**datos, "pais_origen": "Colombia"}),
                             reverse("facturacion:marca_lista"))
        marca.refresh_from_db()
        self.assertEqual(marca.pais_origen, "Colombia")
        self.assertRedirects(self.client.post(reverse("facturacion:marca_eliminar", args=[marca.pk])),
                             reverse("facturacion:marca_lista"))


class PruebasPerfil(BaseDatosDePrueba):
    def test_cada_cuenta_edita_solo_su_perfil(self):
        url = reverse("facturacion:mi_perfil")
        self.autenticar()
        self.assertEqual(self.client.get(url).status_code, 200)
        respuesta = self.client.post(url, {
            "cedula": "1234567890", "telefono": "0991234567",
            "direccion": "Ecuador", "cargo": "Vendedora"
        })
        self.assertRedirects(respuesta, url)
        self.assertEqual(Perfil.objects.get(usuario=self.usuario).cargo, "Vendedora")
        self.client.force_login(self.otro_usuario)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(Perfil.objects.get(usuario=self.otro_usuario).cargo, "")
        self.assertNotContains(self.client.get(url), "Vendedora")
