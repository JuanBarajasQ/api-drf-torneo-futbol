from rest_framework import serializers
from .models import Equipo, Jugador, Partido


class EquipoSerializer(serializers.ModelSerializer):
    total_jugadores = serializers.IntegerField(
        source="jugadores.count",
        read_only=True,
    )

    class Meta:
        model = Equipo
        fields = ["id", "nombre", "ciudad", "total_jugadores"]


class JugadorSerializer(serializers.ModelSerializer):
    equipo_nombre = serializers.ReadOnlyField(source="equipo.nombre")

    class Meta:
        model = Jugador
        fields = ["id", "nombre", "numero", "posicion", "equipo", "equipo_nombre"]
        validators = []  # Para que la validación unique_together se maneje en validate() y se asocie a 'numero'

    def validate_numero(self, value):
        if value < 1 or value > 99:
            raise serializers.ValidationError("El número de camiseta va de 1 a 99.")
        return value

    def validate(self, attrs):
        equipo = attrs.get("equipo") or (self.instance.equipo if self.instance else None)
        numero = attrs.get("numero") if "numero" in attrs else (self.instance.numero if self.instance else None)

        if equipo and numero is not None:
            qs = Jugador.objects.filter(equipo=equipo, numero=numero)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    "numero": ["Dos jugadores del mismo equipo no pueden tener el mismo número."]
                })
        return attrs


class PartidoSerializer(serializers.ModelSerializer):
    local_nombre = serializers.ReadOnlyField(source="local.nombre")
    visitante_nombre = serializers.ReadOnlyField(source="visitante.nombre")
    goles_local = serializers.IntegerField(read_only=True)
    goles_visitante = serializers.IntegerField(read_only=True)
    estado = serializers.CharField(read_only=True)

    class Meta:
        model = Partido
        fields = [
            "id",
            "local",
            "local_nombre",
            "visitante",
            "visitante_nombre",
            "fecha",
            "estadio",
            "goles_local",
            "goles_visitante",
            "estado",
        ]

    def validate(self, attrs):
        local = attrs.get("local") or (self.instance.local if self.instance else None)
        visitante = attrs.get("visitante") or (self.instance.visitante if self.instance else None)

        if local and visitante and local == visitante:
            raise serializers.ValidationError({
                "visitante": ["Un equipo no puede jugar contra sí mismo."]
            })
        return attrs


class RegistrarResultadoSerializer(serializers.Serializer):
    goles_local = serializers.IntegerField(
        required=True,
        min_value=0,
        error_messages={
            "required": "Debe especificar los goles del equipo local.",
            "min_value": "Los goles del local no pueden ser negativos.",
            "invalid": "Ingrese un número entero válido para goles_local.",
        },
    )
    goles_visitante = serializers.IntegerField(
        required=True,
        min_value=0,
        error_messages={
            "required": "Debe especificar los goles del equipo visitante.",
            "min_value": "Los goles del visitante no pueden ser negativos.",
            "invalid": "Ingrese un número entero válido para goles_visitante.",
        },
    )
