package mx.tecnm.canastamx.domain_service.infrastructure.security;

import java.time.Duration;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Base64;
import java.util.Date;
import java.util.Optional;

import javax.crypto.SecretKey;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.JwtParser;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import io.jsonwebtoken.security.MacAlgorithm;

import mx.tecnm.canastamx.domain_service.domain.usuario.Rol;
import mx.tecnm.canastamx.domain_service.domain.usuario.Usuario;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

/**
 * Emite y verifica el token de sesión según el ADR 020 (en propuesta): HS256 y
 * ningún otro algoritmo, con la clave que resulta de DECODIFICAR {@code JWT_SECRET}
 * (Base64 estándar de 32 bytes aleatorios). El texto Base64 no es la clave; sus
 * 32 bytes decodificados, sí.
 */
@Service
public class JwtService {

    /** El único algoritmo que se firma y el único que se acepta. */
    static final MacAlgorithm ALGORITMO = Jwts.SIG.HS256;

    /** Bytes de la clave ya decodificada: los 256 bits de HS256. */
    static final int BYTES_DE_LA_CLAVE = 32;

    private static final String CLAIM_ROL = "rol";
    private static final String COMO_GENERARLA = "Genera una con: openssl rand -base64 32";

    private final SecretKey clave;
    private final Duration duracion;
    private final JwtParser lector;

    public JwtService(
            @Value("${security.jwt.secret}") String secreto,
            @Value("${security.jwt.expiration-minutes}") long minutos) {

        this.clave = claveDe(secreto);

        if (minutos <= 0) {
            throw new IllegalArgumentException(
                    "JWT_EXPIRATION_MINUTES debe ser mayor que 0");
        }

        this.duracion = Duration.ofMinutes(minutos);
        this.lector = lectorDe(clave);
    }

    /**
     * El lector de tokens del servicio. Sólo admite {@link #ALGORITMO}: un token
     * que declare otro se rechaza aunque su firma cuadrara con él. Es de paquete
     * para que JwtServiceTest pruebe esa regla con una clave que también sirve para
     * HS512, cosa que la de 32 bytes del ADR 020 no permite.
     */
    static JwtParser lectorDe(SecretKey clave) {
        return Jwts.parser()
                .sig().clear().add(ALGORITMO).and()
                .verifyWith(clave)
                .build();
    }

    /**
     * La clave de HS256 guardada en {@code JWT_SECRET}: se decodifica el Base64 y
     * deben quedar exactamente 32 bytes. Ningún mensaje incluye el valor.
     */
    static SecretKey claveDe(String secreto) {
        if (secreto == null || secreto.isBlank()) {
            throw new IllegalArgumentException("JWT_SECRET está vacía. " + COMO_GENERARLA);
        }
        byte[] bytes;
        try {
            bytes = Base64.getDecoder().decode(secreto.strip());
        } catch (IllegalArgumentException noEsBase64) {
            // Sin la causa: su mensaje cita el carácter que no es Base64.
            throw new IllegalArgumentException(
                    "JWT_SECRET no es Base64 estándar (¿lleva comillas o espacios?). "
                            + COMO_GENERARLA);
        }
        if (bytes.length != BYTES_DE_LA_CLAVE) {
            throw new IllegalArgumentException(
                    "JWT_SECRET debe decodificar a " + BYTES_DE_LA_CLAVE
                            + " bytes y decodifica a " + bytes.length + ". " + COMO_GENERARLA);
        }
        return Keys.hmacShaKeyFor(bytes);
    }

    public TokenEmitido generarToken(Usuario usuario) {
        // Usar el mismo instante para iat, exp y expiraEn.
        Instant emitidoEn = Instant.now().truncatedTo(ChronoUnit.SECONDS);
        Instant expiraEn = emitidoEn.plus(duracion);

        String token = Jwts.builder()
                .subject(usuario.id())
                .claim(CLAIM_ROL, usuario.rol().name())
                .issuedAt(Date.from(emitidoEn))
                .expiration(Date.from(expiraEn))
                .signWith(clave, ALGORITMO)
                .compact();

        return new TokenEmitido(token, expiraEn);
    }

    /**
     * De qué cuenta es y con qué rol se emitió un token que lo pasa todo: HS256,
     * firmado con esta clave, sin vencer y con {@code sub}, {@code rol}, {@code iat}
     * y {@code exp}. Vacío en cualquier otro caso, sin decir cuál: quien llama no
     * lo necesita y el cliente no debe saberlo.
     */
    public Optional<TokenVerificado> verificar(String token) {
        if (token == null || token.isBlank()) {
            return Optional.empty();
        }

        try {
            // parseSignedClaims revisa algoritmo, firma y vencimiento antes de
            // devolver un solo claim: nada del cuerpo se lee sin verificar.
            Claims claims = lector.parseSignedClaims(token).getPayload();
            String cuenta = claims.getSubject();
            String rol = claims.get(CLAIM_ROL, String.class);
            if (cuenta == null || cuenta.isBlank() || rol == null
                    || claims.getIssuedAt() == null || claims.getExpiration() == null) {
                return Optional.empty();
            }
            return Optional.of(new TokenVerificado(cuenta, Rol.valueOf(rol)));
        } catch (JwtException | IllegalArgumentException ex) {
            return Optional.empty();
        }
    }

    /** El token firmado y el instante exacto de su claim exp. */
    public record TokenEmitido(String token, Instant expiraEn) {}

    /** Lo que dice un token verificado: de qué cuenta es y con qué rol se emitió. */
    public record TokenVerificado(String cuentaId, Rol rol) {}
}
