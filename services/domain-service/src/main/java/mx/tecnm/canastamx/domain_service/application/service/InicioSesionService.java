
package mx.tecnm.canastamx.domain_service.application.service;

import java.time.Instant;

import mx.tecnm.canastamx.domain_service.domain.usuario.CorreoElectronico;
import mx.tecnm.canastamx.domain_service.domain.usuario.Usuario;
import mx.tecnm.canastamx.domain_service.infrastructure.persistence.UsuarioRepository;
import mx.tecnm.canastamx.domain_service.infrastructure.security.JwtService;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class InicioSesionService {

    private final UsuarioRepository usuarioRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;

    public InicioSesionService(
            UsuarioRepository usuarioRepository,
            PasswordEncoder passwordEncoder,
            JwtService jwtService) {
        this.usuarioRepository = usuarioRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
    }

    public ResultadoInicioSesion iniciar(String correo, String contrasena) {
        if (correo == null || correo.isBlank()
                || contrasena == null || contrasena.isBlank()) {
            throw new CredencialesInvalidasException();
        }

        Usuario usuario;
        try {
            usuario = usuarioRepository
                    .buscarPorCorreo(new CorreoElectronico(correo))
                    .orElseThrow(CredencialesInvalidasException::new);
        } catch (IllegalArgumentException ex) {
            throw new CredencialesInvalidasException();
        }

        if (!passwordEncoder.matches(
                contrasena, usuario.contrasenaCifrada())) {
            throw new CredencialesInvalidasException();
        }

        Instant expiraEn = jwtService.calcularExpiracion();
        String token = jwtService.generarToken(usuario);

        return new ResultadoInicioSesion(
                token, expiraEn, usuario.rol().name());
    }

    public record ResultadoInicioSesion(
            String token,
            Instant expiraEn,
            String rol) {}

    public static class CredencialesInvalidasException
            extends RuntimeException {
        public CredencialesInvalidasException() {
            super("Correo o contraseña incorrectos");
        }
    }
}
