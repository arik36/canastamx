
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

//Imports que permiten utilizar clases que ya existen en Java y Spring sin tener que escribir su nombre completo cada vez.
import java.net.URI;
import java.util.List;
import org.springframework.http.ProblemDetail;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.validation.FieldError;

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

//Dejar de responder los errores con un JSON propio que contiene mensaje y empezar a responder con ProblemDetail, siguiendo el contrato de errores de CanastaMX.
@RestControllerAdvice(assignableTypes = CuentaController.class)
class CuentaErrorHandler {

    private static final URI DATOS_INVALIDOS = URI.create("/problemas/datos-invalidos");
    private static final URI CUENTA_DUPLICADA = URI.create("/problemas/cuenta-duplicada");

    @ExceptionHandler(RegistroCuentaService.CuentaDuplicadaException.class)
    public ProblemDetail cuentaDuplicada() {
        return problema(HttpStatus.CONFLICT, CUENTA_DUPLICADA,
                "La cuenta ya existe", "Ya existe una cuenta con ese correo.");
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail solicitudInvalida(MethodArgumentNotValidException ex) {
        List<String> campos = ex.getBindingResult().getFieldErrors().stream()
                .map(FieldError::getField)
                .distinct()
                .sorted()
                .toList();
        return datosInvalidos("Revisa estos datos: " + String.join(", ", campos) + ".");
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ProblemDetail cuerpoIlegible() {
        return datosInvalidos("El cuerpo de la solicitud no es un JSON válido.");
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ProblemDetail reglaNoCumplida() {
        return datosInvalidos("Algún dato no cumple las reglas.");
    }

    private ProblemDetail datosInvalidos(String detalle) {
        return problema(HttpStatus.BAD_REQUEST, DATOS_INVALIDOS,
                "Datos inválidos", detalle);
    }

    private ProblemDetail problema(HttpStatus estado, URI tipo,
                                   String titulo, String detalle) {
        ProblemDetail problema = ProblemDetail.forStatusAndDetail(estado, detalle);
        problema.setType(tipo);
        problema.setTitle(titulo);
        return problema;
    }
}
