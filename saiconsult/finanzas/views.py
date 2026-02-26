from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Sum, Count
from .models import Pago
from .serializers import (
    PagoListSerializer, 
    PagoDetailSerializer, 
    PagoCreateSerializer,
    PagoUpdateSerializer,
    PagoRegistrarPagoSerializer,
    ResumenFinancieroSerializer
)

class PagoViewSet(viewsets.ModelViewSet):
    """
    Controlador para la gestión financiera de SAI.
    Administra cobros, vencimientos y registros de pago.
    """
    queryset = Pago.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return PagoListSerializer
        if self.action == 'retrieve':
            return PagoDetailSerializer
        if self.action == 'create':
            return PagoCreateSerializer
        if self.action in ['update', 'partial_update']:
            return PagoUpdateSerializer
        if self.action == 'registrar_pago':
            return PagoRegistrarPagoSerializer
        return PagoDetailSerializer

    @action(detail=True, methods=['post'], url_path='registrar-pago')
    def registrar_pago(self, request, pk=None):
        """
        Acción para marcar un pago como realizado.
        URL: /api/pagos/{id}/registrar-pago/
        """
        pago = self.get_object()
        serializer = self.get_serializer(data=request.data, context={'pago': pago})
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'Pago registrado exitosamente',
                'pago_id': pago.id
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='resumen-proyecto/(?P<proyecto_id>[0-9]+)')
    def resumen_por_proyecto(self, request, proyecto_id=None):
        """
        Genera un informe financiero rápido de un proyecto específico.
        URL: /api/pagos/resumen-proyecto/{id}/
        """
        pagos = self.queryset.filter(proyecto_id=proyecto_id)
        
        # Cálculos de totales
        resumen = {
            'proyecto_id': proyecto_id,
            'total_pagos': pagos.aggregate(Sum('monto'))['monto__sum'] or 0,
            'total_pagado': pagos.filter(estado='PAGADO').aggregate(Sum('monto'))['monto__sum'] or 0,
            'total_pendiente': pagos.filter(estado='PENDIENTE').aggregate(Sum('monto'))['monto__sum'] or 0,
            'total_atrasado': pagos.filter(estado='ATRASADO').aggregate(Sum('monto'))['monto__sum'] or 0,
            'pagos_por_estado': dict(pagos.values_list('estado').annotate(Count('id')))
        }
        
        serializer = ResumenFinancieroSerializer(resumen)
        return Response(serializer.data)