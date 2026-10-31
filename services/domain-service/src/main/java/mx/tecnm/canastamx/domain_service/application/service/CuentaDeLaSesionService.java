package mx.tecnm.canastamx.domain_service.application.service;

import mx.tecnm.canastamx.domain_service.domain.usuario.Usuario;
import mx.tecnm.canastamx.domain_service.infrastructure.persistence.UsuarioRepository;
import mx.tecnm.canastamx.domain_service.infrastructure.security.JwtService;

import org.springframework.stereotype.Service;

/**
 * La cuenta de quien tiene la sesión (D-10, opción A). La usan
 * {@code GET /api/v1/cuentas/yo} y cualquier ruta protegida, a través de
 * {@code @CuentaDeLaSesion}: primero se verifica el token y sólo después se
 * confía en su {@code sub} para buscar la cuenta.
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
        boolean llegoUnToken = token != null && !token.isBlank();
        return jwtService.verificar(token)
                .map(JwtService.TokenVerificado::cuentaId)
                .flatMap(usuarioRepository::buscarPorId)
                .orElseThrow(() -> new SinSesionException(llegoUnToken));
    }

    /**
     * No hay sesión. Sólo dice si llegó un token, que es lo que el desafío
     * Bearer necesita (RFC 6750 §3); nunca por qué no sirvió.
     */
    public static class SinSesionException extends RuntimeException {

        private final boolean llegoUnToken;

        public SinSesionException(boolean llegoUnToken) {
            super("Falta la sesión, no es válida o ya venció");
            this.llegoUnToken = llegoUnToken;
        }

        public boolean llegoUnToken() {
            return llegoUnToken;
        }
    }
}
