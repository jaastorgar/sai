"""
URL configuration for sai project.

The `urlpatterns` list routes URLs to views.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Importamos las vistas de cada aplicación
from usuarios.views import UsuarioViewSet
from gestion.views import ProyectoViewSet
from servicios.views import ServicioViewSet
from finanzas.views import PagoViewSet

# Creamos un router único para centralizar la API
router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'proyectos', ProyectoViewSet, basename='proyecto')
router.register(r'servicios', ServicioViewSet, basename='servicio')
router.register(r'pagos', PagoViewSet, basename='pago')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]