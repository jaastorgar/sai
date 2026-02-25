from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UsuarioManager(BaseUserManager):
    """
    Manager personalizado para el modelo Usuario con email como identificador.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('El correo electrónico es obligatorio'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('El superusuario debe tener is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('El superusuario debe tener is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuario personalizado que usa email en lugar de username.
    """
    email = models.EmailField(
        _('correo electrónico'),
        unique=True,
        error_messages={
            'unique': _('Ya existe un usuario con este correo electrónico.'),
        }
    )
    is_staff = models.BooleanField(_('es staff'), default=False)
    is_active = models.BooleanField(_('activo'), default=True)
    date_joined = models.DateTimeField(_('fecha de registro'), auto_now_add=True)
    first_name = models.CharField(_('nombres'), max_length=150, blank=True)
    last_name = models.CharField(_('apellidos'), max_length=150, blank=True)
    telefono = models.CharField(_('teléfono'), max_length=20, blank=True)
    
    objects = UsuarioManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = _('usuario')
        verbose_name_plural = _('usuarios')
        ordering = ['email']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name


class Perfil(models.Model):
    ROLES = [
        ('SOCIO', 'Socio'),
        ('CONSULTOR', 'Consultor'),
        ('CLIENTE', 'Cliente'),
    ]

    SUBTIPOS_CLIENTE = [
        ('NATURAL', 'Persona Natural'),
        ('JURIDICA', 'Persona Jurídica'),
    ]

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='perfil',
        verbose_name=_('usuario')
    )
    
    rol = models.CharField(_('rol'), max_length=20, choices=ROLES, default='CLIENTE')
    subtipo_cliente = models.CharField(_('subtipo de cliente'), max_length=20, choices=SUBTIPOS_CLIENTE, blank=True, null=True)
    razon_social = models.CharField(_('razón social'), max_length=255, blank=True)
    ruc = models.CharField(_('RUC'), max_length=20, blank=True)
    direccion = models.TextField(_('dirección'), blank=True)
    especialidad = models.CharField(_('especialidad'), max_length=255, blank=True)
    tarifa_hora = models.DecimalField(_('tarifa por hora'), max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('perfil')
        verbose_name_plural = _('perfiles')
    
    def __str__(self):
        return f"{self.usuario.email} - {self.get_rol_display()}"
    
    def es_socio(self):
        return self.rol == 'SOCIO'
    
    def es_consultor(self):
        return self.rol == 'CONSULTOR'
    
    def es_cliente(self):
        return self.rol == 'CLIENTE'


class MensajeContacto(models.Model):
    """
    Modelo para guardar mensajes del formulario de contacto web.
    """
    CANALES_COMUNICACION = [
        ('WHATSAPP', 'WhatsApp'),
        ('EMAIL', 'Correo electrónico'),
    ]
    
    TIPOS_SERVICIO = [
        ('DESARROLLO', 'Desarrollo'),
        ('CONSULTORIA', 'Consultoría'),
        ('CAPACITACION', 'Capacitación'),
        ('OTROS', 'Otros'),
    ]
    
    # Campos del formulario
    nombre = models.CharField(_('nombre'), max_length=150)
    empresa = models.CharField(_('empresa'), max_length=255, blank=True)
    email = models.EmailField(_('correo electrónico'))
    telefono = models.CharField(_('teléfono'), max_length=20)
    canal_preferido = models.CharField(
        _('¿cómo prefieres que nos comuniquemos?'),
        max_length=20,
        choices=CANALES_COMUNICACION,
        default='EMAIL'
    )
    mensaje = models.TextField(_('mensaje'))
    tipo_servicio = models.CharField(
        _('tipo de servicio de interés'),
        max_length=20,
        choices=TIPOS_SERVICIO,
        default='DESARROLLO'
    )
    
    # Estados de envío
    enviado_email = models.BooleanField(default=False)
    enviado_whatsapp = models.BooleanField(default=False)
    leido = models.BooleanField(default=False)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Mensaje de Contacto'
        verbose_name_plural = 'Mensajes de Contacto'
    
    def __str__(self):
        return f"{self.nombre} - {self.email} ({self.get_canal_preferido_display()})"