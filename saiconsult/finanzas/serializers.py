from rest_framework import serializers
from django.db import transaction
from decimal import Decimal
from .models import Pago


class PagoListSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para listados de pagos.
    """
    proyecto_nombre = serializers.CharField(source='proyecto.nombre', read_only=True)
    cliente_nombre = serializers.CharField(source='proyecto.cliente.get_full_name', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    metodo_display = serializers.CharField(source='get_metodo_pago_display', read_only=True)
    
    class Meta:
        model = Pago
        fields = [
            'id', 'proyecto_nombre', 'cliente_nombre', 'monto',
            'estado', 'estado_display', 'fecha_vencimiento', 'metodo_display'
        ]


class PagoDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo para detalle de pago.
    """
    proyecto_nombre = serializers.CharField(source='proyecto.nombre', read_only=True)
    cliente_nombre = serializers.CharField(source='proyecto.cliente.get_full_name', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    metodo_display = serializers.CharField(source='get_metodo_pago_display', read_only=True)
    
    class Meta:
        model = Pago
        fields = [
            'id', 'proyecto', 'proyecto_nombre', 'cliente_nombre',
            'monto', 'fecha_emision', 'fecha_vencimiento', 'fecha_pago',
            'estado', 'estado_display', 'metodo_pago', 'metodo_display',
            'comprobante', 'notas'
        ]
        read_only_fields = ['fecha_emision']


class PagoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para creación de pagos.
    """
    proyecto_id = serializers.PrimaryKeyRelatedField(
        source='proyecto',
        write_only=True,
        queryset=Pago._meta.get_field('proyecto').related_model.objects.all()
    )
    
    class Meta:
        model = Pago
        fields = [
            'id', 'proyecto_id', 'monto', 'fecha_vencimiento',
            'metodo_pago', 'notas'
        ]
    
    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError('El monto debe ser mayor a cero.')
        return value


class PagoUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualización de pagos (campos limitados).
    """
    class Meta:
        model = Pago
        fields = ['fecha_vencimiento', 'metodo_pago', 'notas']


class PagoRegistrarPagoSerializer(serializers.Serializer):
    """
    Serializer para registrar un pago realizado.
    """
    fecha_pago = serializers.DateField(required=True)
    metodo_pago = serializers.ChoiceField(choices=Pago.METODOS, required=True)
    comprobante = serializers.CharField(max_length=50, required=False, allow_blank=True)
    monto_pagado = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    
    def validate(self, attrs):
        pago = self.context['pago']
        
        # Validar que no esté ya pagado
        if pago.estado == 'PAGADO':
            raise serializers.ValidationError('Este pago ya ha sido registrado.')
        
        # Validar monto
        if attrs['monto_pagado'] != pago.monto:
            raise serializers.ValidationError({
                'monto_pagado': f'El monto pagado ({attrs["monto_pagado"]}) no coincide con el monto del pago ({pago.monto}).'
            })
        
        return attrs
    
    @transaction.atomic
    def save(self):
        pago = self.context['pago']
        pago.fecha_pago = self.validated_data['fecha_pago']
        pago.metodo_pago = self.validated_data['metodo_pago']
        pago.comprobante = self.validated_data.get('comprobante', '')
        pago.estado = 'PAGADO'
        pago.save()
        return pago


class ResumenFinancieroSerializer(serializers.Serializer):
    """
    Serializer para resumen financiero de un proyecto.
    """
    proyecto_id = serializers.IntegerField()
    total_pagos = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_pagado = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_pendiente = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_atrasado = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    pagos_por_estado = serializers.DictField(
        child=serializers.IntegerField()
    )