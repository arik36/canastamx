package mx.tecnm.canastamx.domain_service.infrastructure.config;

import java.util.List;

import mx.tecnm.canastamx.domain_service.application.service.CuentaDeLaSesionService;
import mx.tecnm.canastamx.domain_service.infrastructure.web.CuentaDeLaSesionResolver;

import org.springframework.beans.factory.ObjectProvider;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/** Registra {@code @CuentaDeLaSesion} para todos los controladores. */
@Configuration
public class WebConfig implements WebMvcConfigurer {

    private final ObjectProvider<CuentaDeLaSesionService> cuentaDeLaSesion;

    public WebConfig(ObjectProvider<CuentaDeLaSesionService> cuentaDeLaSesion) {
        this.cuentaDeLaSesion = cuentaDeLaSesion;
    }

    @Override
    public void addArgumentResolvers(List<HandlerMethodArgumentResolver> resolvers) {
        resolvers.add(new CuentaDeLaSesionResolver(cuentaDeLaSesion));
    }
}
