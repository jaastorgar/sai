from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Sum
from .models import Proyecto
from .serializers import (
    ProyectoListSerializer, 
    ProyectoDetailSerializer, 
    ProyectoCreateUpdateSerializer,
    ProyectoAsignarConsultorSerializer,
    ProyectoCambiarEstadoSerializer
)

class ProyectoViewSet(viewsets.ModelViewSet):
    """
    Controlador para gestionar los proyectos de la consultora SAI.
    Permite listar, crear, ver detalles, asignar consultores y cambiar estados.
    """
    queryset = Proyecto.objects.all()

    def get_serializer_class(self):
        # Elegimos el serializer según la acción para optimizar el envío de datos
        if self.action == 'list':
            return ProyectoListSerializer
        if self.action == 'retrieve':
            return ProyectoDetailSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ProyectoCreateUpdateSerializer
        if self.action == 'asignar_consultor':
            return ProyectoAsignarConsultorSerializer
        if self.action == 'cambiar_estado':
            return ProyectoCambiarEstadoSerializer
        return ProyectoDetailSerializer

    def get_queryset(self):
        """
        Calcula el total de pagos recibidos por proyecto al consultar el detalle.
        """
        queryset = super().get_queryset()
        if self.action == 'retrieve':
            # Anotamos el total de pagos vinculados desde la app 'finanzas'
            queryset = queryset.annotate(total_pagos=Sum('pagos__monto'))
        return queryset

    @action(detail=True, methods=['post'], url_path='asignar-consultor')
    def asignar_consultor(self, request, pk=None):
        """
        Acción personalizada para asignar un consultor a un proyecto existente.
        URL: /api/proyectos/{id}/asignar-consultor/
        """
        proyecto = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            from django.contrib.auth import get_user_model
            Usuario = get_user_model()
            consultor = Usuario.objects.get(id=serializer.validated_data['consultor_id'])
            
            proyecto.consultor = consultor
            proyecto.save()
            return Response({'status': 'Consultor asignado correctamente'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='cambiar-estado')
    def cambiar_estado(self, request, pk=None):
        """
        Acción para transicionar el estado del proyecto con validación de lógica.
        URL: /api/proyectos/{id}/cambiar-estado/
        """
        proyecto = self.get_object()
        # Pasamos el proyecto al contexto del serializer para validar la transición
        serializer = self.get_serializer(data=request.data, context={'proyecto': proyecto})
        
        if serializer.is_valid():
            proyecto.estado = serializer.validated_data['estado']
            proyecto.save()
            return Response({
                'status': 'Estado actualizado',
                'nuevo_estado': proyecto.get_estado_display()
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)