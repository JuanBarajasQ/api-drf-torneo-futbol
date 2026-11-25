import django_filters
from .models import Jugador, Partido


class JugadorFilter(django_filters.FilterSet):
    class Meta:
        model = Jugador
        fields = ["equipo", "posicion"]


class PartidoFilter(django_filters.FilterSet):
    fecha_desde = django_filters.DateTimeFilter(field_name="fecha", lookup_expr="gte")
    fecha_hasta = django_filters.DateTimeFilter(field_name="fecha", lookup_expr="lte")
    fecha__gte = django_filters.DateTimeFilter(field_name="fecha", lookup_expr="gte")
    fecha__lte = django_filters.DateTimeFilter(field_name="fecha", lookup_expr="lte")
    fecha__date__gte = django_filters.DateFilter(field_name="fecha__date", lookup_expr="gte")
    fecha__date__lte = django_filters.DateFilter(field_name="fecha__date", lookup_expr="lte")

    class Meta:
        model = Partido
        fields = [
            "estado",
            "local",
            "visitante",
            "fecha_desde",
            "fecha_hasta",
            "fecha__gte",
            "fecha__lte",
            "fecha__date__gte",
            "fecha__date__lte",
        ]

