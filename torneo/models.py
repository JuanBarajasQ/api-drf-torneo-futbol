from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Equipo(models.Model):
    nombre = models.CharField(max_length=120, unique=True, verbose_name="Nombre")
    ciudad = models.CharField(max_length=120, verbose_name="Ciudad")

    class Meta:
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.ciudad})"


class Jugador(models.Model):
    POSICION_CHOICES = [
        ("portero", "Portero"),
        ("defensa", "Defensa"),
        ("medio", "Medio"),
        ("delantero", "Delantero"),
    ]

    nombre = models.CharField(max_length=150, verbose_name="Nombre")
    numero = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1, message="El número de camiseta debe ser al menos 1."),
            MaxValueValidator(99, message="El número de camiseta no puede ser mayor a 99."),
        ],
        verbose_name="Número de camiseta",
    )
    posicion = models.CharField(
        max_length=20,
        choices=POSICION_CHOICES,
        verbose_name="Posición",
    )
    equipo = models.ForeignKey(
        Equipo,
        on_delete=models.PROTECT,
        related_name="jugadores",
        verbose_name="Equipo",
    )

    class Meta:
        verbose_name = "Jugador"
        verbose_name_plural = "Jugadores"
        ordering = ["numero"]
        constraints = [
            models.UniqueConstraint(
                fields=["equipo", "numero"],
                name="unique_numero_por_equipo",
            )
        ]

    def __str__(self):
        return f"#{self.numero} {self.nombre} - {self.equipo.nombre}"


class Partido(models.Model):
    ESTADO_CHOICES = [
        ("programado", "Programado"),
        ("jugado", "Jugado"),
    ]

    local = models.ForeignKey(
        Equipo,
        on_delete=models.PROTECT,
        related_name="partidos_local",
        verbose_name="Equipo Local",
    )
    visitante = models.ForeignKey(
        Equipo,
        on_delete=models.PROTECT,
        related_name="partidos_visitante",
        verbose_name="Equipo Visitante",
    )
    fecha = models.DateTimeField(verbose_name="Fecha y hora")
    estadio = models.CharField(max_length=150, verbose_name="Estadio")
    goles_local = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Goles Local",
    )
    goles_visitante = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Goles Visitante",
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="programado",
        verbose_name="Estado",
    )

    class Meta:
        verbose_name = "Partido"
        verbose_name_plural = "Partidos"
        ordering = ["fecha"]

    def __str__(self):
        return f"{self.local.nombre} vs {self.visitante.nombre} ({self.fecha.strftime('%Y-%m-%d %H:%M')})"
