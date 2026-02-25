from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import Perfil

Usuario = get_user_model()


class PerfilSerializer(serializers.ModelSerializer):
    """
    Serializer para lectura de Perfil con campos display.
    """
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    subtipo_cliente_display = serializers.CharField(source='get_subtipo_cliente_display', read_only=True)
    
    class Meta:
        model = Perfil
        fields = [
            'id', 'rol', 'rol_display', 'subtipo_cliente', 'subtipo_cliente_display',
            'razon_social', 'ruc', 'direccion', 'especialidad', 'tarifa_hora',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']


class PerfilCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para creación/actualización de Perfil con validaciones de negocio.
    """
    class Meta:
        model = Perfil
        fields = [
            'rol', 'subtipo_cliente', 'razon_social', 'ruc', 
            'direccion', 'especialidad', 'tarifa_hora'
        ]
    
    def validate(self, attrs):
        """
        Validación a nivel de objeto para reglas de negocio.
        """
        rol = attrs.get('rol')
        subtipo = attrs.get('subtipo_cliente')
        
        # Si el rol no es CLIENTE, no debe haber subtipo
        if rol != 'CLIENTE' and subtipo:
            raise serializers.ValidationError({
                'subtipo_cliente': 'El subtipo de cliente solo aplica para el rol CLIENTE.'
            })
        
        # Si el rol es CLIENTE, debe haber subtipo
        if rol == 'CLIENTE' and not subtipo:
            raise serializers.ValidationError({
                'subtipo_cliente': 'El cliente debe tener un subtipo (NATURAL o JURIDICA).'
            })
        
        # Validar campos de persona jurídica
        if subtipo == 'JURIDICA':
            if not attrs.get('razon_social'):
                raise serializers.ValidationError({
                    'razon_social': 'La razón social es obligatoria para personas jurídicas.'
                })
            if not attrs.get('ruc'):
                raise serializers.ValidationError({
                    'ruc': 'El RUC es obligatorio para personas jurídicas.'
                })
        
        # Validar campos de consultor/socio
        if rol in ['CONSULTOR', 'SOCIO']:
            if not attrs.get('especialidad'):
                raise serializers.ValidationError({
                    'especialidad': 'La especialidad es obligatoria para consultores y socios.'
                })
        
        return attrs


class UsuarioListSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para listados (campos mínimos).
    """
    rol = serializers.CharField(source='perfil.rol', read_only=True)
    rol_display = serializers.CharField(source='perfil.get_rol_display', read_only=True)
    nombre_completo = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'nombre_completo', 'first_name', 'last_name',
            'telefono', 'is_active', 'rol', 'rol_display', 'date_joined'
        ]


class UsuarioDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo para detalle de usuario con perfil anidado.
    """
    perfil = PerfilSerializer(read_only=True)
    nombre_completo = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'first_name', 'last_name', 'nombre_completo',
            'telefono', 'is_active', 'is_staff', 'date_joined', 'last_login',
            'perfil'
        ]
        read_only_fields = ['date_joined', 'last_login']


class UsuarioCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para creación de usuarios con contraseña y perfil.
    Usa transacción atómica para garantizar integridad.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    perfil = PerfilCreateUpdateSerializer(required=True)
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'telefono', 'perfil'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden.'
            })
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        perfil_data = validated_data.pop('perfil')
        validated_data.pop('password_confirm')
        
        # Crear usuario
        usuario = Usuario.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            telefono=validated_data.get('telefono', '')
        )
        
        # Crear perfil asociado
        Perfil.objects.create(usuario=usuario, **perfil_data)
        
        return usuario


class UsuarioUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualización de usuarios (sin cambio de contraseña).
    """
    perfil = PerfilCreateUpdateSerializer(required=False)
    
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'telefono', 'is_active', 'perfil']
    
    @transaction.atomic
    def update(self, instance, validated_data):
        perfil_data = validated_data.pop('perfil', None)
        
        # Actualizar campos del usuario
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Actualizar perfil si se proporcionaron datos
        if perfil_data and hasattr(instance, 'perfil'):
            perfil = instance.perfil
            for attr, value in perfil_data.items():
                setattr(perfil, attr, value)
            perfil.save()
        
        return instance


class CambiarPasswordSerializer(serializers.Serializer):
    """
    Serializer para cambio de contraseña con validación de contraseña actual.
    """
    old_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Las contraseñas no coinciden.'
            })
        return data
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('La contraseña actual es incorrecta.')
        return value


class LoginSerializer(serializers.Serializer):
    """
    Serializer para autenticación con email y contraseña.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )


class TokenResponseSerializer(serializers.Serializer):
    """
    Serializer para respuesta de tokens JWT.
    """
    refresh = serializers.CharField()
    access = serializers.CharField()
    user = UsuarioDetailSerializer()