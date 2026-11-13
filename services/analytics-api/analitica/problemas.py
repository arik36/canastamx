"""El formato único de error: `application/problem+json`, RFC 9457 (P-03)."""


class Problema(Exception):
    def __init__(self, status, tipo, titulo, detalle):
        super().__init__(detalle)
        self.status, self.tipo, self.titulo, self.detalle = status, tipo, titulo, detalle

    def cuerpo(self):
        return {"type": self.tipo, "title": self.titulo, "status": self.status,
                "detail": self.detalle}


class SinSesion(Problema):
    """Falta la sesión, no pasa la verificación o no tiene el rol de la ruta (P-07).
    El mismo `type` que usa el dominio."""

    def __init__(self, detalle):
        super().__init__(401, "/problemas/sin-sesion", "Sin sesión", detalle)


class SinDatos(Problema):
    def __init__(self, detalle):
        super().__init__(404, "/problemas/sin-datos", "Sin datos", detalle)


class DatosInvalidos(Problema):
    def __init__(self, detalle):
        super().__init__(400, "/problemas/datos-invalidos", "Datos inválidos", detalle)


class NoSeCierra(Problema):
    """`cerrarIncidente` sobre un aviso, o sobre un incidente que ya estaba cerrado."""

    def __init__(self, detalle):
        super().__init__(409, "/problemas/no-se-cierra", "No se puede cerrar", detalle)


class DominioNoDisponible(Problema):
    """No se pudo preguntar al dominio de quién es la sesión (D-11)."""

    def __init__(self, detalle):
        super().__init__(503, "/problemas/dominio-no-disponible", "Dominio no disponible",
                         detalle)
