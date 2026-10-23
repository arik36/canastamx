package mx.tecnm.canastamx.domain_service.infrastructure.security;

import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import java.util.Optional;

import javax.crypto.SecretKey;

import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.JwtParser;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;

import mx.tecnm.canastamx.domain_service.domain.usuario.Usuario;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class JwtService {

    private final SecretKey clave;
    private final Duration duracion;
    private final JwtParser lector;

    public JwtService(
            @Value("${security.jwt.secret}") String secreto,
            @Value("${security.jwt.expiration-minutes}") long minutos) {

        byte[] bytes = secreto.getBytes(StandardCharsets.UTF_8);

        if (bytes.length < 32) {
            throw new IllegalArgumentException(
                    "JWT_SECRET debe tener al menos 32 bytes");
        }

        if (minutos <= 0) {
            throw new IllegalArgumentException(
                    "JWT_EXPIRATION_MINUTES debe ser mayor que 0");
        }

        this.clave = Keys.hmacShaKeyFor(bytes);
        this.duracion = Duration.ofMinutes(minutos);
        this.lector = Jwts.parser().verifyWith(clave).build();
    }

    public TokenEmitido generarToken(Usuario usuario) {
        // Usar el mismo instante para iat, exp y expiraEn.
        Instant emitidoEn = Instant.now().truncatedTo(ChronoUnit.SECONDS);
        Instant expiraEn = emitidoEn.plus(duracion);

        String token = Jwts.builder()
                .subject(usuario.id())
                .claim("rol", usuario.rol().name())
                .issuedAt(Date.from(emitidoEn))
                .expiration(Date.from(expiraEn))
                .signWith(clave)
                .compact();

        return new TokenEmitido(token, expiraEn);
    }

    /**
     * El id de la cuenta (claim sub) si el token lo firmó esta clave y no ha
     * vencido. Vacío si falta, está mal formado o alterado, lo firmó otra
     * clave o ya venció: quien llama no necesita saber cuál de ellas fue.
     */
    public Optional<String> verificar(String token) {
        if (token == null || token.isBlank()) {
            return Optional.empty();
        }

        try {
            String id = lector.parseSignedClaims(token).getPayload().getSubject();
            return Optional.ofNullable(id).filter(valor -> !valor.isBlank());
        } catch (JwtException | IllegalArgumentException ex) {
            return Optional.empty();
        }
    }

    /** El token firmado y el instante exacto de su claim exp. */
    public record TokenEmitido(String token, Instant expiraEn) {}
}
