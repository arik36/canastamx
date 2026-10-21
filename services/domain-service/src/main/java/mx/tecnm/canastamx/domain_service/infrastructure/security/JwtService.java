
package mx.tecnm.canastamx.domain_service.infrastructure.security;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;

import javax.crypto.SecretKey;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;

import mx.tecnm.canastamx.domain_service.domain.usuario.Usuario;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class JwtService {

    private final SecretKey clave;
    private final long duracionSegundos = 3600;

    public JwtService(@Value("${security.jwt.secret}") String secreto) {
        byte[] bytes = secreto.getBytes(StandardCharsets.UTF_8);

        if (bytes.length < 32) {
            throw new IllegalArgumentException(
                    "JWT_SECRET debe tener al menos 32 bytes");
        }

        this.clave = Keys.hmacShaKeyFor(bytes);
    }

    public String generarToken(Usuario usuario) {
        Instant ahora = Instant.now();
        Instant expiracion = ahora.plusSeconds(duracionSegundos);

        return Jwts.builder()
                .subject(usuario.id())
                .claim("rol", usuario.rol().name())
                .issuedAt(Date.from(ahora))
                .expiration(Date.from(expiracion))
                .signWith(clave)
                .compact();
    }

    public Instant calcularExpiracion() {
        return Instant.now().plusSeconds(duracionSegundos);
    }
}
