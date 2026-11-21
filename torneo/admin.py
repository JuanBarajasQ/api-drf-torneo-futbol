from django.contrib import admin
from .models import Equipo, Jugador, Partido


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "ciudad")
    search_fields = ("nombre", "ciudad")
    list_filter = ("ciudad",)


@admin.register(Jugador)
class JugadorAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "numero", "posicion", "equipo")
    search_fields = ("nombre", "equipo__nombre")
    list_filter = ("posicion", "equipo")


@admin.register(Partido)
class PartidoAdmin(admin.ModelAdmin):
    list_display = ("id", "local", "visitante", "fecha", "estadio", "estado", "goles_local", "goles_visitante")
    search_fields = ("local__nombre", "visitante__nombre", "estadio")
    list_filter = ("estado", "fecha", "local", "visitante")
