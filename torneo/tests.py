from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from torneo.models import Equipo, Jugador, Partido


class TorneoAPITests(APITestCase):
    def setUp(self):
        self.equipo_a = Equipo.objects.create(nombre="Cúcuta Deportivo", ciudad="Cúcuta")
        self.equipo_b = Equipo.objects.create(nombre="Atlético Bucaramanga", ciudad="Bucaramanga")
        self.equipo_c = Equipo.objects.create(nombre="Junior", ciudad="Barranquilla")

        self.jugador_1 = Jugador.objects.create(
            nombre="Juan Pérez",
            numero=10,
            posicion="medio",
            equipo=self.equipo_a,
        )

        self.partido_1 = Partido.objects.create(
            local=self.equipo_a,
            visitante=self.equipo_b,
            fecha="2026-12-01T15:00:00Z",
            estadio="General Santander",
        )

    def test_numero_camiseta_rango_valido(self):
        # Número fuera de rango (0 y 100)
        url = reverse("jugador-list")
        res_0 = self.client.post(url, {
            "nombre": "Test Menor",
            "numero": 0,
            "posicion": "delantero",
            "equipo": self.equipo_a.id,
        })
        self.assertEqual(res_0.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("numero", res_0.data)

        res_100 = self.client.post(url, {
            "nombre": "Test Mayor",
            "numero": 100,
            "posicion": "delantero",
            "equipo": self.equipo_a.id,
        })
        self.assertEqual(res_100.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("numero", res_100.data)

    def test_mismo_numero_mismo_equipo(self):
        url = reverse("jugador-list")
        res = self.client.post(url, {
            "nombre": "Carlos Gómez",
            "numero": 10,  # Ya lo tiene jugador_1 en equipo_a
            "posicion": "defensa",
            "equipo": self.equipo_a.id,
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("numero", res.data)

        # Mismo número en OTRO equipo sí debe ser permitido
        res_otro = self.client.post(url, {
            "nombre": "Carlos Gómez",
            "numero": 10,
            "posicion": "defensa",
            "equipo": self.equipo_b.id,
        })
        self.assertEqual(res_otro.status_code, status.HTTP_201_CREATED)

    def test_equipo_no_puede_jugar_contra_si_mismo(self):
        url = reverse("partido-list")
        res = self.client.post(url, {
            "local": self.equipo_a.id,
            "visitante": self.equipo_a.id,
            "fecha": "2026-12-05T18:00:00Z",
            "estadio": "General Santander",
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("visitante", res.data)

    def test_goles_y_estado_son_readonly_en_partido(self):
        url = reverse("partido-list")
        res = self.client.post(url, {
            "local": self.equipo_a.id,
            "visitante": self.equipo_c.id,
            "fecha": "2026-12-05T18:00:00Z",
            "estadio": "General Santander",
            "goles_local": 5,
            "goles_visitante": 3,
            "estado": "jugado",
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["estado"], "programado")
        self.assertIsNone(res.data["goles_local"])
        self.assertIsNone(res.data["goles_visitante"])

    def test_accion_partidos_equipo(self):
        # Partido donde equipo_a es local
        url = reverse("equipo-partidos", kwargs={"pk": self.equipo_a.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

        # Partido donde equipo_a es visitante
        Partido.objects.create(
            local=self.equipo_c,
            visitante=self.equipo_a,
            fecha="2026-12-10T20:00:00Z",
            estadio="Metropolitano",
        )
        res = self.client.get(url)
        self.assertEqual(len(res.data), 2)

    def test_accion_registrar_resultado(self):
        url = reverse("partido-registrar-resultado", kwargs={"pk": self.partido_1.pk})

        # Negativo
        res_neg = self.client.post(url, {"goles_local": -1, "goles_visitante": 2})
        self.assertEqual(res_neg.status_code, status.HTTP_400_BAD_REQUEST)

        # Falta valor
        res_falta = self.client.post(url, {"goles_local": 2})
        self.assertEqual(res_falta.status_code, status.HTTP_400_BAD_REQUEST)

        # Registro exitoso
        res_ok = self.client.post(url, {"goles_local": 2, "goles_visitante": 1})
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(res_ok.data["estado"], "jugado")
        self.assertEqual(res_ok.data["goles_local"], 2)
        self.assertEqual(res_ok.data["goles_visitante"], 1)

        # Intentar volver a registrar cuando ya tenía resultado
        res_repetido = self.client.post(url, {"goles_local": 3, "goles_visitante": 0})
        self.assertEqual(res_repetido.status_code, status.HTTP_400_BAD_REQUEST)

    def test_recurso_principal_paginacion_filtros_orden(self):
        url = reverse("jugador-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("count", res.data)
        self.assertIn("results", res.data)

        # Filtrar por equipo
        res_filtro = self.client.get(f"{url}?equipo={self.equipo_a.id}&posicion=medio")
        self.assertEqual(res_filtro.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_filtro.data["results"]), 1)

    def test_reto_opcional_protect_delete(self):
        # Intentar borrar equipo_a teniendo a jugador_1
        url = reverse("equipo-detail", kwargs={"pk": self.equipo_a.pk})
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No se puede eliminar", res.data["detail"])
