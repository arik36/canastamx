"""De quién es la sesión: el correo que firma el cierre de un incidente (D-11).

El token trae `sub`, `rol`, `iat` y `exp`, y nada más de la persona (ADR 020). El
esquema de operación guarda el correo de quien cierra (RNF-22), así que se le
pregunta al dominio con el mismo token: `GET /api/v1/cuentas/yo` (D-10).

`DOMINIO_URL` dice dónde corre el dominio; vacía, es el de desarrollo, como en el
cliente web. El token no se guarda ni se imprime, y ningún error lo repite.
"""

import json
import os
import urllib.error
import urllib.request

from .problemas import DominioNoDisponible, SinSesion

POR_OMISION = "http://localhost:8081"
ESPERA_SEGUNDOS = 5


def url_del_dominio():
    return (os.environ.get("DOMINIO_URL") or POR_OMISION).rstrip("/")


class Dominio:
    """Lo único que la interfaz analítica le pide al dominio."""

    def correo(self, token, cuenta):
        """El correo de la cuenta `cuenta`, que es el `sub` del token ya verificado.

        Si el dominio no reconoce la sesión, `SinSesion`. Si no responde, o responde
        otra cosa, `DominioNoDisponible`: sin saber quién cierra no se cierra nada.
        """
        pedido = urllib.request.Request(f"{url_del_dominio()}/api/v1/cuentas/yo",
                                        headers={"Authorization": f"Bearer {token}",
                                                 "Accept": "application/json"})
        try:
            with urllib.request.urlopen(pedido, timeout=ESPERA_SEGUNDOS) as r:
                cuerpo = json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise SinSesion("La sesión no es válida o ya venció.") from None
            raise DominioNoDisponible(f"El dominio respondió {e.code} al preguntar de quién "
                                      "es la sesión. El incidente no se cerró.") from None
        except (OSError, ValueError):
            # `from None`: el traceback de urllib trae el pedido, con el token.
            raise DominioNoDisponible("No se pudo preguntar al dominio de quién es la "
                                      "sesión. El incidente no se cerró.") from None
        correo = cuerpo.get("correo") if isinstance(cuerpo, dict) else None
        if not isinstance(correo, str) or "@" not in correo or cuerpo.get("id") != cuenta:
            raise DominioNoDisponible("El dominio no devolvió la cuenta de la sesión. "
                                      "El incidente no se cerró.")
        return correo
