package mx.tecnm.canastamx.domain_service.application.service;

import mx.tecnm.canastamx.domain_service.domain.usuario.Usuario;
import mx.tecnm.canastamx.domain_service.infrastructure.persistence.UsuarioRepository;
import mx.tecnm.canastamx.domain_service.infrastructure.security.JwtService;

import org.springframework.stereotype.Service;

/**
 * La cuenta de quien tiene la sesión (D-10, opción A): con ella, la app y la
 * web muestran el correo sin guardarlo en el teléfono.
 */
@Service
public class CuentaDeLaSesionService {

    private final UsuarioRepository usuarioRepository;
    private final JwtService jwtService;

    public CuentaDeLaSesionService(
            UsuarioRepository usuarioRepository,
            JwtService jwtService) {
        this.usuarioRepository = usuarioRepository;
        this.jwtService = jwtService;
    }

    /** Sin un token válido, o si su cuenta ya no existe, no hay sesión. */
    public Usuario obtener(String token) {
        return jwtService.verificar(token)
                .flatMap(usuarioRepository::buscarPorId)
                .orElseThrow(SinSesionException::new);
    }

    public static class SinSesionException extends RuntimeException {
        public SinSesionException() {
            super("Falta la sesión, no es válida o ya venció");
        }
    }
}
