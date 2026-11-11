#!/usr/bin/env python3
"""Auditoría estática sin dependencias: NO sustituye `manage.py test`."""
import ast
import re
import sqlite3
import sys
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
fallos = []
exitos = []

def verificar(condicion, etiqueta):
    (exitos if condicion else fallos).append(etiqueta)
    print(f"{'[OK]' if condicion else '[FALLO]'} {etiqueta}")

# 1) Sintaxis: cada módulo Python debe compilar.
archivos = sorted(ROOT.rglob('*.py'))
compilan = True
for archivo in archivos:
    try:
        compile(archivo.read_text(encoding='utf8'), str(archivo), 'exec')
    except (SyntaxError, UnicodeError) as exc:
        compilan = False
        print(f"    Problema: {archivo.relative_to(ROOT)}: {exc}")
verificar(compilan, f"Sintaxis Python en {len(archivos)} archivos")

# 2) Vistas basadas en funciones y protección de rutas.
urls = (ROOT/'facturacion/urls.py').read_text()
vistas_ast = ast.parse((ROOT/'facturacion/views.py').read_text())
funciones = {n.name:n for n in vistas_ast.body if isinstance(n,ast.FunctionDef)}
nombres_en_urls = re.findall(r'views\.(\w+)',urls)
verificar(len(nombres_en_urls) >= 19 and all(n in funciones for n in nombres_en_urls),
         f"Rutas conectadas a vistas reales ({len(nombres_en_urls)})")
verificar(all(any(isinstance(d,ast.Name) and d.id=='login_required' for d in funciones[n].decorator_list)
             for n in nombres_en_urls if n in funciones),
         "Todas las vistas de facturación tienen @login_required")
verificar(not re.search(r'\b(?:ListView|CreateView|UpdateView|DeleteView)\b',
                      (ROOT/'facturacion/views.py').read_text()),
         "Vistas basadas en funciones (sin CRUD genérico de clases)")
crud = ['marca','producto','categoria','cliente']
verificar(all(all(f'{s}_{accion}' in funciones for accion in ['lista','crear','editar','eliminar'])
             for s in crud), "CRUD completo de los cuatro módulos")

def tiene_guardia_post(fn):
    return any(isinstance(n,ast.If) and 'request.method' in ast.unparse(n.test) and
               'POST' in ast.unparse(n.test)
               for n in ast.walk(fn))
verificar(all(tiene_guardia_post(funciones[f'{s}_{accion}'])
             for s in crud for accion in ('crear','editar','eliminar'))
         ,"Todos los POST de creación, edición y borrado se comprueban explícitamente")
verificar('mi_perfil' in funciones and tiene_guardia_post(funciones['mi_perfil']),
         "Mi perfil usa el patrón GET/POST")

# 3) Templates: heredan de base.html y cuentan con token CSRF.
plantillas = sorted(ROOT.glob('facturacion/templates/**/*.html')) + sorted(ROOT.glob('templates/**/*.html'))
pl_ok = all('{% extends "base.html" %}' in f.read_text() for f in plantillas
            if f.name != 'base.html')
verificar(pl_ok, f"Herencia de base.html en {len(plantillas)-1} vistas HTML")
csrf_ok = True
for f in plantillas:
    codigo=f.read_text()
    if re.search(r'<form[^>]+method=["\']post["\']',codigo,re.IGNORECASE):
        if '{% csrf_token %}' not in codigo:
            csrf_ok=False
            print('    Sin csrf_token:',f.relative_to(ROOT))
verificar(csrf_ok, 'Formularios POST llevan {% csrf_token %}')
menu=(ROOT/'templates/base.html').read_text()
verificar(all(f'facturacion:{s}_lista' in menu for s in crud)
         and 'facturacion:mi_perfil' in menu,"Menú incluye los cinco módulos")

# 4) BD real incluida: integridad e información de evaluación.
conn=sqlite3.connect(ROOT/'db.sqlite3')
verificar(conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok',
         'SQLite PRAGMA integrity_check = ok')
verificar(not conn.execute('PRAGMA foreign_key_check').fetchall(),
         'SQLite sin claves foráneas rotas')
minimos={'facturacion_categoria':4,'facturacion_cliente':7,'facturacion_producto':5}
for tabla,minimo in minimos.items():
    total=conn.execute('SELECT COUNT(*) FROM '+tabla).fetchone()[0]
    verificar(total>=minimo,f'{tabla}: {total} registros (mínimo {minimo})')
verificar(conn.execute('SELECT COUNT(*) FROM facturacion_marca').fetchone()[0] > 0,
         'Existen marcas para los productos')
verificar(conn.execute('SELECT COUNT(*) FROM facturacion_perfil').fetchone()[0] > 0,
         'Existe al menos un perfil 1:1')
verificar(not conn.execute('SELECT nombre, COUNT(*) n FROM facturacion_categoria GROUP BY lower(nombre) HAVING n>1').fetchall(),
         'No hay categorías duplicadas por mayúsculas/minúsculas')
verificar(not conn.execute('SELECT cedula, COUNT(*) n FROM facturacion_cliente GROUP BY cedula HAVING n>1').fetchall(),
         'No hay cédulas duplicadas')
verificar(not conn.execute('SELECT id FROM facturacion_producto WHERE precio<=0 OR stock<0').fetchall(),
         'Productos con precio positivo y stock no negativo')
verificar(conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='facturacion_producto_categorias'").fetchone()[0]==1,
         'Existe tabla intermedia muchos a muchos Producto ↔ Categoria')
conn.close()

# 5) Landing: links, imágenes locales y componentes esenciales.
class Detector(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.enlaces=[];self.imagenes=[];self.tarjetas=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a' and a.get('href','').startswith('#'):self.enlaces.append(a['href'][1:])
        if tag=='img':self.imagenes.append((a.get('src'),a.get('alt')))
        if tag=='article' and 'tarjeta' in a.get('class','').split():self.tarjetas+=1
html=ROOT/'landing/index.html'
d=Detector();d.feed(html.read_text())
verificar(d.tarjetas>=4, f'Landing HTML contiene {d.tarjetas} tarjetas de producto')
verificar(len(d.ids)==len(set(d.ids)) and all(not e or e in d.ids for e in d.enlaces),
         'Landing sin IDs repetidos ni anclas rotas')
verificar(all(src and alt and (html.parent/src).is_file() for src,alt in d.imagenes),
         'Landing con imágenes locales y texto alternativo')
verificar((ROOT/'landing/css/estilos.css').is_file(),'Landing tiene hoja CSS separada')

print(f'\nRESULTADO: {len(exitos)} comprobaciones correctas y {len(fallos)} fallos estáticos.')
if fallos:
    sys.exit(1)
print('IMPORTANTE: para pruebas funcionales se requiere instalar Django y ejecutar manage.py test.')
