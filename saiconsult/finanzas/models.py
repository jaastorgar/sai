from django.db import models


class Pago(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
        ('ATRASADO', 'Atrasado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    METODOS = [
        ('TRANSFERENCIA', 'Transferencia Bancaria'),
        ('EFECTIVO', 'Efectivo'),
        ('TARJETA', 'Tarjeta de Crédito/Débito'),
        ('YAPE', 'Yape'),
        ('PLIN', 'Plin'),
    ]
    
    proyecto = models.ForeignKey(
        'gestion.Proyecto',
        on_delete=models.CASCADE,
        related_name='pagos'
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_emision = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField()
    fecha_pago = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    metodo_pago = models.CharField(max_length=20, choices=METODOS, blank=True)
    comprobante = models.CharField(max_length=50, blank=True)
    notas = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-fecha_emision']
    
    def __str__(self):
        return f"Pago {self.id} - {self.proyecto.nombre}"