
package mx.tecnm.canastamx.domain_service.application.service;

import java.time.Instant;
import java.util.UUID;

import mx.tecnm.canastamx.domain_service.domain.usuario.CorreoElectronico;
import mx.tecnm.canastamx.domain_service.domain.usuario.Rol;
import mx.tecnm.canastamx.domain_service.domain.usuario.Usuario;
import mx.tecnm.canastamx.domain_service.infrastructure.persistence.UsuarioRepository;

import org.springframework.dao.DuplicateKeyException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class RegistroCuentaService {

    private final UsuarioRepository usuarioRepository;
    private final PasswordEncoder passwordEncoder;

    public RegistroCuentaService(
            UsuarioRepository usuarioRepository,
            PasswordEncoder passwordEncoder) {
        this.usuarioRepository = usuarioRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Transactional
    public Usuario registrar(String correo, String contrasena) {
        if (contrasena == null
                || contrasena.length() < 8
                || !contrasena.matches(".*[A-Z].*")
                || !contrasena.matches(".*\\d.*")) {
            throw new IllegalArgumentException(
                    "La contraseña debe tener al menos 8 caracteres, "
                    + "una mayúscula y un número");
        }

        CorreoElectronico correoElectronico =
                new CorreoElectronico(correo);

        if (usuarioRepository.buscarPorCorreo(correoElectronico).isPresent()) {
            throw new CuentaDuplicadaException();
        }

        String hash = passwordEncoder.encode(contrasena);

        Usuario usuario = new Usuario(
                UUID.randomUUID().toString(),
                correoElectronico,
                hash,
                Rol.CONSUMIDOR,
                Instant.now()
        );

        try {
            return usuarioRepository.guardar(usuario);
        } catch (DuplicateKeyException ex) {
            throw new CuentaDuplicadaException();
        }
    }

    public static class CuentaDuplicadaException extends RuntimeException {
        public CuentaDuplicadaException() {
            super("Ya existe una cuenta con ese correo electrónico");
        }
    }
}
