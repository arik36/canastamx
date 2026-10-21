
package mx.tecnm.canastamx.domain_service.infrastructure.web;

import java.time.Instant;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

import mx.tecnm.canastamx.domain_service.application.service.RegistroCuentaService;
import mx.tecnm.canastamx.domain_service.domain.usuario.Usuario;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestController
@RequestMapping("/api/v1/cuentas")
public class CuentaController {

    private final RegistroCuentaService registroCuentaService;

    public CuentaController(RegistroCuentaService registroCuentaService) {
        this.registroCuentaService = registroCuentaService;
    }

    @PostMapping
    public ResponseEntity<CuentaRespuesta> registrar(
            @Valid @RequestBody RegistroSolicitud solicitud) {

        Usuario usuario = registroCuentaService.registrar(
                solicitud.correo(),
                solicitud.contrasena()
        );

        CuentaRespuesta respuesta = new CuentaRespuesta(
                usuario.id(),
                usuario.correo().valor(),
                usuario.rol().name(),
                usuario.fechaDeRegistro()
        );

        return ResponseEntity.status(HttpStatus.CREATED).body(respuesta);
    }

    public record RegistroSolicitud(
            @NotBlank
            @Email
            String correo,

            @NotBlank
            @Size(min = 8, max = 72)
            @Pattern(regexp = ".*[A-Z].*", message = "Debe incluir una mayúscula")
            @Pattern(regexp = ".*\\d.*", message = "Debe incluir un número")
            String contrasena
    ) {}

    public record CuentaRespuesta(
            String id,
            String correo,
            String rol,
            Instant fechaDeRegistro
    ) {}
}

@RestControllerAdvice
class CuentaErrorHandler {

    @ExceptionHandler(RegistroCuentaService.CuentaDuplicadaException.class)
    public ResponseEntity<ErrorRespuesta> cuentaDuplicada(
            RegistroCuentaService.CuentaDuplicadaException ex) {
        return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(new ErrorRespuesta(ex.getMessage()));
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ErrorRespuesta> datosInvalidos(
            IllegalArgumentException ex) {
        return ResponseEntity.badRequest()
                .body(new ErrorRespuesta(ex.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorRespuesta> solicitudInvalida(
            MethodArgumentNotValidException ex) {
        return ResponseEntity.badRequest()
                .body(new ErrorRespuesta("Los datos enviados no son válidos"));
    }

    public record ErrorRespuesta(String mensaje) {}
}
