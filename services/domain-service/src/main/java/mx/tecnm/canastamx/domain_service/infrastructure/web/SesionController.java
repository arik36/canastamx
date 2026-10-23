package mx.tecnm.canastamx.domain_service.infrastructure.web;

import java.net.URI;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

import mx.tecnm.canastamx.domain_service.application.service.InicioSesionService;

import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
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

@RestControllerAdvice(assignableTypes = SesionController.class)
class SesionErrorHandler {

    private static final URI SIN_SESION =
            URI.create("/problemas/sin-sesion");

    @ExceptionHandler({
            InicioSesionService.CredencialesInvalidasException.class,
            HttpMessageNotReadableException.class,
            MethodArgumentNotValidException.class
    })
    public ProblemDetail sinSesion() {
        ProblemDetail problema = ProblemDetail.forStatusAndDetail(
                HttpStatus.UNAUTHORIZED,
                "El correo o la contraseña no son válidos.");

        problema.setType(SIN_SESION);
        problema.setTitle("Sin sesión");

        return problema;
    }
}