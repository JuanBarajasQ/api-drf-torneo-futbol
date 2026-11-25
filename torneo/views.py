from django.db.models import ProtectedError, Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import JugadorFilter, PartidoFilter
from .models import Equipo, Jugador, Partido
from .serializers import (
    EquipoSerializer,
    JugadorSerializer,
    PartidoSerializer,
    RegistrarResultadoSerializer,
)


class ProtectDeleteMixin:
    """Reto opcional: responder 400 amigable cuando un registro protegido no pueda borrarse."""
    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError as error:
            elementos = len(error.protected_objects)
            return Response(
                {
                    "detail": f"No se puede eliminar este registro porque tiene {elementos} registro(s) asociado(s)."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class EquipoViewSet(ProtectDeleteMixin, viewsets.ModelViewSet):
    queryset = Equipo.objects.all()
    serializer_class = EquipoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombre", "ciudad"]
    ordering_fields = ["nombre", "ciudad"]
    ordering = ["nombre"]

    @extend_schema(
        summary="Listar partidos de un equipo",
        description="Devuelve todos los partidos donde el equipo participa como local o como visitante.",
        responses={200: PartidoSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="partidos")
    def partidos(self, request, pk=None):
        equipo = self.get_object()
        partidos = Partido.objects.filter(Q(local=equipo) | Q(visitante=equipo)).select_related("local", "visitante")
        serializer = PartidoSerializer(partidos, many=True)
        return Response(serializer.data)


class JugadorViewSet(ProtectDeleteMixin, viewsets.ModelViewSet):
    """
    Recurso principal:
    - Filtros: equipo y posicion
    - Búsqueda: por nombre
    - Ordenación: por numero y nombre
    - Orden por defecto: numero
    """
    queryset = Jugador.objects.select_related("equipo").all()
    serializer_class = JugadorSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = JugadorFilter
    search_fields = ["nombre"]
    ordering_fields = ["numero", "nombre"]
    ordering = ["numero"]


class PartidoViewSet(ProtectDeleteMixin, viewsets.ModelViewSet):
    queryset = Partido.objects.select_related("local", "visitante").all()
    serializer_class = PartidoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PartidoFilter
    search_fields = ["estadio", "local__nombre", "visitante__nombre"]
    ordering_fields = ["fecha", "goles_local", "goles_visitante"]
    ordering = ["fecha"]

    @extend_schema(
        summary="Registrar resultado de un partido",
        description="Recibe goles_local y goles_visitante, guarda el marcador y actualiza el estado a jugado.",
        request=RegistrarResultadoSerializer,
        responses={200: PartidoSerializer, 400: dict},
    )
    @action(detail=True, methods=["post"], url_path="registrar-resultado")
    def registrar_resultado(self, request, pk=None):
        partido = self.get_object()

        if partido.estado == "jugado" or partido.goles_local is not None or partido.goles_visitante is not None:
            return Response(
                {"estado": ["El partido ya tenía un resultado registrado."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RegistrarResultadoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        partido.goles_local = serializer.validated_data["goles_local"]
        partido.goles_visitante = serializer.validated_data["goles_visitante"]
        partido.estado = "jugado"
        partido.save()

        salida = PartidoSerializer(partido)
        return Response(salida.data, status=status.HTTP_200_OK)
