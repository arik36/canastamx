package mx.tecnm.canastamx.domain_service.infrastructure.web;

import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * El parámetro {@code Usuario} que recibe la cuenta de quien tiene la sesión.
 * Sin un token Bearer válido de una cuenta que existe, el método no se llama y
 * la respuesta es el 401 de {@link SinSesionHandler}.
 *
 * <p>Toda operación implementada que {@code dominio.yaml} declara protegida lo
 * lleva (por su seguridad propia o la global); {@code RutasProtegidasTests} lo comprueba.
 */
@Target(ElementType.PARAMETER)
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface CuentaDeLaSesion {
}
