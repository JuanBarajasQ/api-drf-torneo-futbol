from rest_framework.routers import DefaultRouter
from .views import EquipoViewSet, JugadorViewSet, PartidoViewSet

router = DefaultRouter()
router.register("equipos", EquipoViewSet, basename="equipo")
router.register("jugadores", JugadorViewSet, basename="jugador")
router.register("partidos", PartidoViewSet, basename="partido")

urlpatterns = router.urls

