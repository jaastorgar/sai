from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Perfil, MensajeContacto
from .serializers import (
    UsuarioListSerializer,
    UsuarioDetailSerializer,
    UsuarioCreateSerializer,
    UsuarioUpdateSerializer,
    CambiarPasswordSerializer,
    LoginSerializer,
    MensajeContactoSerializer
)

Usuario = get_user_model()


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de usuarios con perfiles.
    """
    queryset = Usuario.objects.all().select_related('perfil')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UsuarioCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UsuarioUpdateSerializer
        elif self.action == 'list':
            return UsuarioListSerializer
        return UsuarioDetailSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        queryset = Usuario.objects.all().select_related('perfil')
        
        # Filtrar por rol si se proporciona
        rol = self.request.query_params.get('rol', None)
        if rol:
            queryset = queryset.filter(perfil__rol=rol)
        
        # Buscar por email o nombre
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cambiar_password(self, request, pk=None):
        """
        Endpoint para cambiar la contraseña del usuario.
        """
        usuario = self.get_object()
        serializer = CambiarPasswordSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            usuario.set_password(serializer.validated_data['new_password'])
            usuario.save()
            return Response({'message': 'Contraseña actualizada correctamente.'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Endpoint para obtener el usuario actual autenticado.
        """
        serializer = UsuarioDetailSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def consultores(self, request):
        """
        Endpoint para listar solo consultores y socios.
        """
        queryset = self.get_queryset().filter(perfil__rol__in=['CONSULTOR', 'SOCIO'])
        serializer = UsuarioListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def clientes(self, request):
        """
        Endpoint para listar solo clientes.
        """
        queryset = self.get_queryset().filter(perfil__rol='CLIENTE')
        serializer = UsuarioListSerializer(queryset, many=True)
        return Response(serializer.data)


class MensajeContactoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de mensajes de contacto.
    """
    queryset = MensajeContacto.objects.all()
    serializer_class = MensajeContactoSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def marcar_leido(self, request, pk=None):
        """
        Marcar mensaje como leído.
        """
        mensaje = self.get_object()
        mensaje.leido = True
        mensaje.save()
        return Response({'status': 'mensaje marcado como leído'})