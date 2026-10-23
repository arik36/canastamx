package mx.tecnm.canastamx.domain_service.infrastructure.security;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.time.Duration;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Base64;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;

import mx.tecnm.canastamx.domain_service.domain.usuario.CorreoElectronico;
import mx.tecnm.canastamx.domain_service.domain.usuario.Rol;
import mx.tecnm.canastamx.domain_service.domain.usuario.Usuario;

import org.junit.jupiter.api.Test;

/**
 * JwtService sin Spring ni base de datos. El segundo argumento del constructor
 * es el valor de security.jwt.expiration-minutes.
 */
class JwtServiceTest {

    // Clave aleatoria creada en cada corrida: el repositorio no guarda ninguna.
    private static final String SECRETO = claveDePrueba();

    private static final Usuario USUARIO = new Usuario(
            "u1",
            new CorreoElectronico("prueba@canastamx.mx"),
            "$2a$10$abcdefghijklmnopqrstuv",
            Rol.CONSUMIDOR,
            null);

    @Test
    void conQuinceMinutosExpMenosIatEsNovecientosYExpiraEnEsExp() {
        JwtService servicio = new JwtService(SECRETO, 15);

        Instant antes = Instant.now().truncatedTo(ChronoUnit.SECONDS);
        JwtService.TokenEmitido emitido = servicio.generarToken(USUARIO);
        Instant despues = Instant.now();

        Claims claims = Jwts.parser()
                .verifyWith(Keys.hmacShaKeyFor(SECRETO.getBytes(StandardCharsets.UTF_8)))
                .build()
                .parseSignedClaims(emitido.token())
                .getPayload();
        Instant iat = claims.getIssuedAt().toInstant();
        Instant exp = claims.getExpiration().toInstant();

        assertEquals(900L, Duration.between(iat, exp).getSeconds());
        assertEquals(exp, emitido.expiraEn());
        assertFalse(iat.isBefore(antes) || iat.isAfter(despues));
    }

    @Test
    void rechazaCeroMinutos() {
        IllegalArgumentException error = assertThrows(
                IllegalArgumentException.class,
                () -> new JwtService(SECRETO, 0));
        assertEquals("JWT_EXPIRATION_MINUTES debe ser mayor que 0", error.getMessage());
    }

    @Test
    void rechazaMinutosNegativos() {
        IllegalArgumentException error = assertThrows(
                IllegalArgumentException.class,
                () -> new JwtService(SECRETO, -5));
        assertEquals("JWT_EXPIRATION_MINUTES debe ser mayor que 0", error.getMessage());
    }

    @Test
    void unTokenPropioDevuelveElIdDeLaCuenta() {
        JwtService servicio = new JwtService(SECRETO, 15);

        String token = servicio.generarToken(USUARIO).token();

        assertEquals(Optional.of("u1"), servicio.verificar(token));
    }

    @Test
    void unTokenAjenoVencidoAlteradoOMalFormadoNoDevuelveCuenta() {
        JwtService servicio = new JwtService(SECRETO, 15);
        Instant ahora = Instant.now().truncatedTo(ChronoUnit.SECONDS);

        String deOtraClave = new JwtService(claveDePrueba(), 15)
                .generarToken(USUARIO).token();
        String vencido = firmado("u1",
                ahora.minus(Duration.ofHours(2)), ahora.minus(Duration.ofHours(1)));
        String sinCuenta = firmado(null, ahora, ahora.plus(Duration.ofMinutes(15)));
        String sinFirma = Jwts.builder().subject("u1").compact();

        // El cuerpo de otro, con la firma de un token auténtico.
        String[] partes = servicio.generarToken(USUARIO).token().split("\\.");
        String alterado = partes[0] + "."
                + Base64.getUrlEncoder().withoutPadding().encodeToString(
                        "{\"sub\":\"u2\",\"rol\":\"OPERADOR\"}".getBytes(StandardCharsets.UTF_8))
                + "." + partes[2];

        Map<String, String> tokens = new LinkedHashMap<>();
        tokens.put("de otra clave", deOtraClave);
        tokens.put("vencido", vencido);
        tokens.put("sin cuenta", sinCuenta);
        tokens.put("sin firma", sinFirma);
        tokens.put("alterado", alterado);
        tokens.put("mal formado", "no-es-un-token");
        tokens.put("vacío", "");
        tokens.put("en blanco", "   ");
        tokens.put("nulo", null);

        tokens.forEach((caso, token) ->
                assertEquals(Optional.empty(), servicio.verificar(token), caso));
    }

    /** Firmado con SECRETO, con el sujeto y las fechas que se le pidan. */
    private static String firmado(String sujeto, Instant emitidoEn, Instant expiraEn) {
        return Jwts.builder()
                .subject(sujeto)
                .claim("rol", Rol.CONSUMIDOR.name())
                .issuedAt(Date.from(emitidoEn))
                .expiration(Date.from(expiraEn))
                .signWith(Keys.hmacShaKeyFor(SECRETO.getBytes(StandardCharsets.UTF_8)))
                .compact();
    }

    private static String claveDePrueba() {
        byte[] bytes = new byte[32];
        new SecureRandom().nextBytes(bytes);
        return Base64.getEncoder().encodeToString(bytes); // 44 caracteres
    }
}