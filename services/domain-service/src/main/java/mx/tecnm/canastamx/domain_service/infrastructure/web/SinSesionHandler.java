package mx.tecnm.canastamx.domain_service.infrastructure.web;

import java.net.URI;

import mx.tecnm.canastamx.domain_service.application.service.CuentaDeLaSesionService;

import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * El 401 de toda ruta protegida por Bearer, venga del controlador que venga.
 *
 * <ul>
 *   <li>El cuerpo es el mismo {@code problem+json} para cualquier causa: no dice si
 *       el token venció, lo firmó otra clave o su cuenta ya no existe.</li>
 *   <li>Lleva el desafío que exige RFC 9110 §15.5.2. Si llegó un token que no
 *       sirve, el desafío agrega {@code error="invalid_token"} (RFC 6750 §3.1);
 *       si no llegó ninguno, no lleva código de error (RFC 6750 §3).</li>
 * </ul>
 *
 * <p>{@code POST /api/v1/sesiones} no pasa por aquí: recibe las credenciales en el
 * cuerpo y no acepta Bearer. Su 401 queda sin {@code WWW-Authenticate} como
 * excepción explícita (D-12, opción B, votada el 2 de noviembre de 2026): anunciar
 * Bearer nombraría un mecanismo que esta ruta no acepta. No cambia el
 * comportamiento ni los clientes; los 401 de las rutas protegidas conservan su desafío.
 */
@RestControllerAdvice
class SinSesionHandler {

    static final String DESAFIO = "Bearer";
    static final String DESAFIO_TOKEN_INVALIDO = "Bearer error=\"invalid_token\"";

    private static final URI SIN_SESION = URI.create("/problemas/sin-sesion");

    @ExceptionHandler(CuentaDeLaSesionService.SinSesionException.class)
    public ResponseEntity<ProblemDetail> sinSesion(
            CuentaDeLaSesionService.SinSesionException ex) {
        ProblemDetail problema = ProblemDetail.forStatusAndDetail(
                HttpStatus.UNAUTHORIZED, "Falta la sesión, no es válida o ya venció.");
        problema.setType(SIN_SESION);
        problema.setTitle("Sin sesión");

        return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                .header(HttpHeaders.WWW_AUTHENTICATE,
                        ex.llegoUnToken() ? DESAFIO_TOKEN_INVALIDO : DESAFIO)
                .body(problema);
    }
}
