from rest_framework import serializers
from decimal import Decimal
from .models import Servicio


class ServicioListSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para listados de servicios.
    """
    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'precio_base', 'duracion_horas', 'activo']


class ServicioDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo para detalle de servicio.
    """
    class Meta:
        model = Servicio
        fields = [
            'id', 'nombre', 'descripcion', 'precio_base',
            'duracion_horas', 'activo', 'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']


class ServicioCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para creación/actualización de servicios con validaciones.
    """
    class Meta:
        model = Servicio
        fields = [
            'id', 'nombre', 'descripcion', 'precio_base',
            'duracion_horas', 'activo'
        ]
    
    def validate_precio_base(self, value):
        if value <= 0:
            raise serializers.ValidationError('El precio base debe ser mayor a cero.')
        return value
    
    def validate_duracion_horas(self, value):
        if value <= 0:
            raise serializers.ValidationError('La duración debe ser mayor a cero.')
        return value


class ServicioCalcularPresupuestoSerializer(serializers.Serializer):
    """
    Serializer para calcular presupuesto basado en cantidad de servicios.
    """
    servicio_id = serializers.IntegerField(required=True)
    cantidad = serializers.IntegerField(min_value=1, required=True)
    descuento_porcentaje = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=0, max_value=100, default=0
    )
    
    def validate_servicio_id(self, value):
        try:
            Servicio.objects.get(id=value, activo=True)
        except Servicio.DoesNotExist:
            raise serializers.ValidationError('El servicio no existe o está inactivo.')
        return value
    
    def calculate(self):
        servicio = Servicio.objects.get(id=self.validated_data['servicio_id'])
        cantidad = self.validated_data['cantidad']
        descuento = self.valid