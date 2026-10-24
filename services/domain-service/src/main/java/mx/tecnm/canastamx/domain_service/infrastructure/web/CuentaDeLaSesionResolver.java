package mx.tecnm.canastamx.domain_service.infrastructure.web;

import mx.tecnm.canastamx.domain_service.application.service.CuentaDeLaSesionService;
import mx.tecnm.canastamx.domain_service.domain.usuario.Usuario;

import org.springframework.beans.factory.ObjectProvider;
import org.springframework.core.MethodParameter;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.support.WebDataBinderFactory;
import org.springframework.web.context.request.NativeWebRequest;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.method.support.ModelAndViewContainer;

/**
 * Llena los parámetros {@link CuentaDeLaSesion}: lee {@code Authorization: Bearer}
 * y pide la cuenta a {@link CuentaDeLaSesionService}. Si no hay sesión, el servicio
 * lanza {@code SinSesionException} y el método del controlador no llega a correr.
 *
 * <p>El servicio se pide al resolver, no al crear el resolvedor: así las pruebas
 * de un solo controlador ({@code @WebMvcTest}) arrancan sin él.
 */
public final class CuentaDeLaSesionResolver implements HandlerMethodArgumentResolver {

    private static final String ESQUEMA = "Bearer ";

    private final ObjectProvider<CuentaDeLaSesionService> cuentaDeLaSesion;

    public CuentaDeLaSesionResolver(ObjectProvider<CuentaDeLaSesionService> cuentaDeLaSesion) {
        this.cuentaDeLaSesion = cuentaDeLaSesion;
    }

    @Override
    public boolean supportsParameter(MethodParameter parametro) {
        return parametro.hasParameterAnnotation(CuentaDeLaSesion.class);
    }

    @Override
    public Object resolveArgument(MethodParameter parametro,
                                  ModelAndViewContainer modelo,
                                  NativeWebRequest solicitud,
                                  WebDataBinderFactory enlazador) {
        if (!Usuario.class.equals(parametro.getParameterType())) {
            throw new IllegalStateException(
                    "@CuentaDeLaSesion sólo va en un parámetro Usuario: " + parametro);
        }
        String token = tokenBearer(solicitud.getHeader(HttpHeaders.AUTHORIZATION));
        return cuentaDeLaSesion.getObject().obtener(token);
    }

    /**
     * El token de {@code Bearer <token>}; null si el encabezado falta o es de otro
     * esquema. El nombre del esquema no distingue mayúsculas (RFC 9110 §11.1).
     */
    static String tokenBearer(String autorizacion) {
        if (autorizacion == null
                || !autorizacion.regionMatches(true, 0, ESQUEMA, 0, ESQUEMA.length())) {
            return null;
        }
        return autorizacion.substring(ESQUEMA.length()).strip();
    }
}
