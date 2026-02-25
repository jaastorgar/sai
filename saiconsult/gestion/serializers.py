from rest_framework import serializers
from django.db import transaction
from .models import Proyecto
from usuarios.serializers import UsuarioListSerializer


class ProyectoListSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para listados de proyectos.
    """
    cliente_nombre = serializers.CharField(source='cliente.get_full_name', read_only=True)
    cliente_email = serializers.CharField(source='cliente.email', read_only=True)
    consultor_nombre = serializers.CharField(source='consultor.get_full_name', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Proyecto
        fields = [
            'id', 'nombre', 'estado', 'estado_display',
            'fecha_inicio', 'fecha_fin',
            'cliente_nombre', 'cliente_email', 'consultor_nombre'
        ]


class ProyectoDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo para detalle de proyecto con relaciones anidadas.
    """
    cliente = UsuarioListSerializer(read_only=True)
    consultor = UsuarioListSerializer(read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    total_pagos = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = Proyecto
        fields = [
            'id', 'nombre', 'descripcion', 'estado', 'estado_display',
            'fecha_inicio', 'fecha_fin', 'cliente', 'consultor',
            'total_pagos', 'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']


class ProyectoCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para creación/actualización de proyectos.
    """
    cliente_id = serializers.PrimaryKeyRelatedField(
        queryset=serializers.CurrentUserDefault(),
        source='cliente',
        write_only=True
    )
    consultor_id = serializers.PrimaryKeyRelatedField(
        queryset=serializers.CurrentUserDefault(),
        source='consultor',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Proyecto
        fields = [
            'id', 'nombre', 'descripcion', 'estado',
            'fecha_inicio', 'fecha_fin', 'cliente_id', 'consultor_id'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar clientes y consultores válidos
        from django.contrib.auth import get_user_model
        Usuario = get_user_model()
        
        self.fields['cliente_id'].queryset = Usuario.objects.filter(
            perfil__rol='CLIENTE'
        )
        self.fields['consultor_id'].queryset = Usuario.objects.filter(
            perfil__rol='CONSULTOR'
        )
    
    def validate(self, attrs):
        # Validar fechas
        fecha_inicio = attrs.get('fecha_inicio')
        fecha_fin = attrs.get('fecha_fin')
        
        if fecha_fin and fecha_inicio and fecha_fin < fecha_inicio:
            raise serializers.ValidationError({
                'fecha_fin': 'La fecha de fin no puede ser anterior a la fecha de inicio.'
            })
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        return super().create(validated_data)


class ProyectoAsignarConsultorSerializer(serializers.Serializer):
    """
    Serializer para asignar consultor a un proyecto.
    """
    consultor_id = serializers.IntegerField(required=True)
    
    def validate_consultor_id(self, value):
        from django.contrib.auth import get_user_model
        Usuario = get_user_model()
        
        try:
            consultor = Usuario.objects.get(id=value, perfil__rol='CONSULTOR')
        except Usuario.DoesNotExist:
            raise serializers.ValidationError('El consultor no existe o no tiene rol válido.')
        
        return value


class ProyectoCambiarEstadoSerializer(serializers.Serializer):
    """
    Serializer para cambiar estado de proyecto con validación de transiciones.
    """
    estado = serializers.ChoiceField(choices=Proyecto.ESTADO_CHOICES)
    
    def validate_estado(self, value):
        proyecto = self.context['proyecto']
        
        # Validar transiciones de estado permitidas
        transiciones_validas = {
            'PENDIENTE': ['EN_PROGRESO', 'CANCELADO'],
            'EN_PROGRESO': ['COMPLETADO', 'CANCELADO'],
            'COMPLETADO': [],
            'CANCELADO': []
        }
        
        estado_actual = proyecto.estado
        if value not in transiciones_validas.get(estado_actual, []):
            raise serializers.ValidationError(
                f'No se puede cambiar de {estado_actual} a {value}.'
            )
        
        return value