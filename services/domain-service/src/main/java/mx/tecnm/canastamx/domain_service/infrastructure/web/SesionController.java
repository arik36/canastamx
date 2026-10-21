
package mx.tecnm.canastamx.domain_service.infrastructure.web;

import java.time.Instant;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

import mx.tecnm.canastamx.domain_service.application.service.InicioSesionService;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestController
@RequestMapping("/api/v1/sesiones")
public class SesionController {

    private final InicioSesionService inicioSesionService;

    public SesionController(InicioSesionService inicioSesionService) {
        this.inicioSesionService = inicioSesionService;
    }

    @PostMapping
    public InicioSesionService.ResultadoInicioSesion iniciar(
            @Valid @RequestBody InicioSolicitud solicitud) {
        return inicioSesionService.iniciar(
                solicitud.correo(),
                solicitud.contrasena());
    }

    public record InicioSolicitud(
            @NotBlank @Email String correo,
            @NotBlank String contrasena) {}
}

@RestControllerAdvice
class SesionErrorHandler {

    @ExceptionHandler(
            InicioSesionService.CredencialesInvalidasException.class)
    public ResponseEntity<ErrorRespuesta> credencialesInvalidas(
            InicioSesionService.CredencialesInvalidasException ex) {
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                .body(new ErrorRespuesta(ex.getMessage()));
    }

    public record ErrorRespuesta(String mensaje) {}
}
