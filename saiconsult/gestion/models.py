from django.db import models


class Proyecto(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROGRESO', 'En Progreso'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    cliente = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='proyectos_cliente',
        limit_choices_to={'perfil__rol': 'CLIENTE'}
    )
    consultor = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proyectos_consultor',
        limit_choices_to={'perfil__rol': 'CONSULTOR'}
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return self.nombre