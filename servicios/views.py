from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from decimal import Decimal
from .models import Servicio
from .serializers import (
    ServicioListSerializer, 
    ServicioDetailSerializer, 
    ServicioCreateUpdateSerializer,
    ServicioCalcularPresupuestoSerializer
)

class ServicioViewSet(viewsets.ModelViewSet):
    """
    Controlador para gestionar el catálogo de servicios de SAI.
    Permite listar, crear, ver detalles y calcular presupuestos rápidos.
    """
    # Filtramos por defecto para que el frontend vea servicios activos
    queryset = Servicio.objects.all()

    def get_serializer_class(self):
        # Selección dinámica de serializer según la acción
        if self.action == 'list':
            return ServicioListSerializer
        if self.action == 'retrieve':
            return ServicioDetailSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ServicioCreateUpdateSerializer
        if self.action == 'calcular_presupuesto':
            return ServicioCalcularPresupuestoSerializer
        return ServicioDetailSerializer

    @action(detail=False, methods=['post'], url_path='calcular-presupuesto')
    def calcular_presupuesto(self, request):
        """
        Acción personalizada para cotizar un servicio rápidamente sin crear registros.
        URL: /api/servicios/calcular-presupuesto/
        """
        serializer = ServicioCalcularPresupuestoSerializer(data=request.data)
        
        if serializer.is_valid():
            datos = serializer.validated_data
            servicio = Servicio.objects.get(id=datos['servicio_id'])
            
            # Lógica de cálculo
            subtotal = servicio.precio_base * datos['cantidad']
            descuento = subtotal * (datos['descuento_porcentaje'] / Decimal('100'))
            total = subtotal - descuento
            
            return Response({
                'servicio': servicio.nombre,
                'precio_unitario': servicio.precio_base,
                'cantidad': datos['cantidad'],
                'subtotal': subtotal,
                'descuento_aplicado': descuento,
                'total_presupuesto': total
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)