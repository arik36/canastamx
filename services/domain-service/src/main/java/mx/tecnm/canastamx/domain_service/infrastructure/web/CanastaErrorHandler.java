package mx.tecnm.canastamx.domain_service.infrastructure.web;

import java.net.URI;
import mx.tecnm.canastamx.domain_service.application.service.CanastaService;
import mx.tecnm.canastamx.domain_service.domain.canasta.Canasta;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice(assignableTypes = CanastaController.class)
public class CanastaErrorHandler {
    @ExceptionHandler({CanastaService.NoExisteException.class, Canasta.ArticuloNoExisteException.class})
    public ProblemDetail noExiste() {
        return problema(HttpStatus.NOT_FOUND, "/problemas/no-existe", "No existe",
                "La canasta o el artículo no existe, o no pertenece a tu cuenta.");
    }

    @ExceptionHandler({IllegalArgumentException.class, MethodArgumentNotValidException.class,
            HttpMessageNotReadableException.class, MissingServletRequestParameterException.class,
            MethodArgumentTypeMismatchException.class, ArithmeticException.class})
    public ProblemDetail datosInvalidos() {
        return problema(HttpStatus.BAD_REQUEST, "/problemas/datos-invalidos", "Datos inválidos",
                "Revisa el nombre, el artículo, la cantidad y la paginación.");
    }

    private ProblemDetail problema(HttpStatus estado, String tipo, String titulo, String detalle) {
        var problema = ProblemDetail.forStatusAndDetail(estado, detalle);
        problema.setType(URI.create(tipo));
        problema.setTitle(titulo);
        return problema;
    }
}
