package mx.tecnm.canastamx.domain_service.infrastructure.security;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.time.Duration;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Base64;
import java.util.Date;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jws;
import io.jsonwebtoken.JwtParser;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.UnsupportedJwtException;
import io.jsonwebtoken.security.Keys;
import io.jsonwebtoken.security.MacAlgorithm;
import io.jsonwebtoken.security.SignatureException;

import mx.tecnm.canastamx.domain_service.domain.usuario.CorreoElectronico;
import mx.tecnm.canastamx.domain_service.domain.usuario.Rol;
import mx.tecnm.canastamx.domain_service.domain.usuario.Usuario;

import org.junit.jupiter.api.Test;

/**
 * JwtService sin Spring ni base de datos. El segundo argumento del constructor
 * es el valor de security.jwt.expiration-minutes. La clave sigue el ADR 020:
 * JWT_SECRET es Base64 de 32 bytes, y lo que firma son esos bytes decodificados.
 */
class JwtServiceTest {

    // Clave aleatoria creada en cada corrida: el repositorio no guarda ninguna.
    private static final String SECRETO = claveDePrueba(32);
    private static final byte[] CLAVE = Base64.getDecoder().decode(SECRETO);

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

        Claims claims = leer(emitido.token()).getPayload();
        Instant iat = claims.getIssuedAt().toInstant();
        Instant exp = claims.getExpiration().toInstant();

        assertEquals(900L, Duration.between(iat, exp).getSeconds());
        assertEquals(exp, emitido.expiraEn());
        assertFalse(iat.isBefore(antes) || iat.isAfter(despues));
    }

    @Test
    void firmaSiempreConHs256() {
        String token = new JwtService(SECRETO, 15).generarToken(USUARIO).token();

        assertEquals("HS256", leer(token).getHeader().getAlgorithm());
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
    void rechazaUnaClaveQueNoEsBase64DeTreintaYDosBytesSinMostrarla() {
        Map<String, String> claves = new LinkedHashMap<>();
        claves.put("nula", null);
        claves.put("vacía", "");
        claves.put("en blanco", "   ");
        claves.put("texto que no es Base64", "esto-no-es-base64!");
        claves.put("Base64 entre comillas", "\"" + SECRETO + "\"");
        claves.put("31 bytes", claveDePrueba(31));
        claves.put("48 bytes", claveDePrueba(48));
        claves.put("64 bytes", claveDePrueba(64));
        // 64 caracteres hexadecimales también son Base64 válido, pero de 48 bytes.
        claves.put("32 bytes en hexadecimal", HexFormat.of().formatHex(bytesAleatorios(32)));

        claves.forEach((caso, clave) -> {
            IllegalArgumentException error = assertThrows(
                    IllegalArgumentException.class, () -> new JwtService(clave, 15), caso);
            assertTrue(error.getMessage().startsWith("JWT_SECRET"), caso);
            if (clave != null && !clave.isBlank()) {
                assertFalse(error.getMessage().contains(clave.strip()),
                        caso + ": el mensaje no debe incluir la clave");
            }
        });
    }

    @Test
    void ignoraLosEspaciosAlrededorDeLaClave() {
        JwtService servicio = new JwtService("  " + SECRETO + "\t", 15);
        String token = servicio.generarToken(USUARIO).token();

        assertEquals("u1", leer(token).getPayload().getSubject());
    }

    @Test
    void unTokenPropioDevuelveSuCuentaYSuRol() {
        JwtService servicio = new JwtService(SECRETO, 15);

        String token = servicio.generarToken(USUARIO).token();

        assertEquals(Optional.of(new JwtService.TokenVerificado("u1", Rol.CONSUMIDOR)),
                servicio.verificar(token));
    }

    @Test
    void unTokenHechoAManoConHs256YTodosSusClaimsSeAcepta() throws Exception {
        // aMano arma tokens válidos: con HS256 y todos los claims, el servicio lo
        // acepta. Los casos HS512 de abajo usan el mismo armado.
        long ahora = Instant.now().getEpochSecond();
        String token = aMano("HS256", "HmacSHA256", CLAVE,
                "{\"sub\":\"u1\",\"rol\":\"CONSUMIDOR\",\"iat\":" + ahora
                        + ",\"exp\":" + (ahora + 900) + "}");

        assertEquals(Optional.of(new JwtService.TokenVerificado("u1", Rol.CONSUMIDOR)),
                new JwtService(SECRETO, 15).verificar(token));
    }

    @Test
    void elLectorDelServicioRechazaHs512PorElAlgoritmoAunqueLaClaveYLaFirmaSirvan() {
        // 64 bytes son los 512 bits que pide HS512: así la clave no puede ser el motivo.
        // El servicio nunca usa una clave así (ADR 020: 32 bytes); por eso se prueba
        // su lector y no verificar().
        var clave64 = Keys.hmacShaKeyFor(bytesAleatorios(64));
        Instant ahora = Instant.now().truncatedTo(ChronoUnit.SECONDS);
        Instant enQuince = ahora.plus(Duration.ofMinutes(15));
        String hs512 = firmado(clave64, Jwts.SIG.HS512, "u1", "CONSUMIDOR", ahora, enQuince);
        String hs256 = firmado(clave64, Jwts.SIG.HS256, "u1", "CONSUMIDOR", ahora, enQuince);
        JwtParser lector = JwtService.lectorDe(clave64);

        // Testigos: un lector de JJWT sin regla de algoritmos acepta el HS512 (firma,
        // clave, claims y vigencia en regla), y el lector del servicio acepta esta
        // clave en un HS256. Lo único que separa al caso rechazado es el algoritmo.
        assertEquals("u1", Jwts.parser().verifyWith(clave64).build()
                .parseSignedClaims(hs512).getPayload().getSubject());
        assertEquals("u1", lector.parseSignedClaims(hs256).getPayload().getSubject());

        SignatureException rechazo = assertThrows(SignatureException.class,
                () -> lector.parseSignedClaims(hs512));
        // Así informa JJWT 0.13 un alg que el lector no admite. Una firma que no cuadra
        // también es SignatureException, pero sin esta causa.
        UnsupportedJwtException causa = assertInstanceOf(UnsupportedJwtException.class,
                rechazo.getCause(), rechazo.getMessage());
        assertTrue(causa.getMessage().contains("'HS512'"), causa.getMessage());
    }

    @Test
    void conLaClaveDelServicioHs512SeRechazaPorElAlgoritmoAntesDeRevisarLaClave()
            throws Exception {
        // La clave del ADR 020 es corta para HS512. Sin la regla de algoritmos, JJWT
        // también rechazaría este token, pero por la clave (WeakKeyException); con la
        // regla, no llega a revisarla.
        long ahora = Instant.now().getEpochSecond();
        String hs512 = aMano("HS512", "HmacSHA512", CLAVE,
                "{\"sub\":\"u1\",\"rol\":\"CONSUMIDOR\",\"iat\":" + ahora
                        + ",\"exp\":" + (ahora + 900) + "}");
        JwtParser lector = JwtService.lectorDe(JwtService.claveDe(SECRETO));

        SignatureException rechazo = assertThrows(SignatureException.class,
                () -> lector.parseSignedClaims(hs512));
        assertInstanceOf(UnsupportedJwtException.class, rechazo.getCause(),
                rechazo.getMessage());
    }

    @Test
    void ningunTokenQueFalleEnAlgoDevuelveCuenta() throws Exception {
        JwtService servicio = new JwtService(SECRETO, 15);
        Instant ahora = Instant.now().truncatedTo(ChronoUnit.SECONDS);
        Instant enQuince = ahora.plus(Duration.ofMinutes(15));
        long segundos = ahora.getEpochSecond();

        Map<String, String> tokens = new LinkedHashMap<>();
        tokens.put("de otra clave",
                new JwtService(claveDePrueba(32), 15).generarToken(USUARIO).token());
        tokens.put("firmado con el TEXTO de la clave, como antes del ADR 020",
                firmado(Keys.hmacShaKeyFor(SECRETO.getBytes(StandardCharsets.UTF_8)),
                        "u1", "CONSUMIDOR", ahora, enQuince));
        // Se rechaza con la regla de algoritmos y sin ella (32 bytes no alcanzan para
        // HS512): por sí solo no prueba la regla. La prueban las dos pruebas de arriba.
        tokens.put("otro algoritmo (HS512) con esta misma clave", aMano("HS512", "HmacSHA512",
                CLAVE, "{\"sub\":\"u1\",\"rol\":\"CONSUMIDOR\",\"iat\":" + segundos
                        + ",\"exp\":" + (segundos + 900) + "}"));
        tokens.put("vencido", firmado(clave(), "u1", "CONSUMIDOR",
                ahora.minus(Duration.ofHours(2)), ahora.minus(Duration.ofHours(1))));
        tokens.put("sin sub", firmado(clave(), null, "CONSUMIDOR", ahora, enQuince));
        tokens.put("sin rol", firmado(clave(), "u1", null, ahora, enQuince));
        tokens.put("con un rol que no existe", firmado(clave(), "u1", "ADMIN", ahora, enQuince));
        tokens.put("sin iat", firmado(clave(), "u1", "CONSUMIDOR", null, enQuince));
        tokens.put("sin exp", firmado(clave(), "u1", "CONSUMIDOR", ahora, null));
        tokens.put("sin firma", Jwts.builder().subject("u1").claim("rol", "CONSUMIDOR")
                .issuedAt(Date.from(ahora)).expiration(Date.from(enQuince)).compact());

        // El cuerpo de otro, con la firma de un token auténtico.
        String[] partes = servicio.generarToken(USUARIO).token().split("\\.");
        tokens.put("alterado", partes[0] + "."
                + Base64.getUrlEncoder().withoutPadding().encodeToString(
                        "{\"sub\":\"u2\",\"rol\":\"OPERADOR\"}".getBytes(StandardCharsets.UTF_8))
                + "." + partes[2]);

        tokens.put("mal formado", "no-es-un-token");
        tokens.put("vacío", "");
        tokens.put("en blanco", "   ");
        tokens.put("nulo", null);

        tokens.forEach((caso, token) ->
                assertEquals(Optional.empty(), servicio.verificar(token), caso));
    }

    // ---------- ayudas ----------

    private static javax.crypto.SecretKey clave() {
        return Keys.hmacShaKeyFor(CLAVE);
    }

    private static Jws<Claims> leer(String token) {
        return Jwts.parser().verifyWith(clave()).build().parseSignedClaims(token);
    }

    /** HS256 con la clave dada; un argumento null deja fuera su claim. */
    private static String firmado(javax.crypto.SecretKey clave, String sujeto, String rol,
                                  Instant emitidoEn, Instant expiraEn) {
        return firmado(clave, Jwts.SIG.HS256, sujeto, rol, emitidoEn, expiraEn);
    }

    /** Con la clave y el algoritmo dados; un argumento null deja fuera su claim. */
    private static String firmado(javax.crypto.SecretKey clave, MacAlgorithm algoritmo,
                                  String sujeto, String rol,
                                  Instant emitidoEn, Instant expiraEn) {
        return Jwts.builder()
                .subject(sujeto)
                .claim("rol", rol)
                .issuedAt(emitidoEn == null ? null : Date.from(emitidoEn))
                .expiration(expiraEn == null ? null : Date.from(expiraEn))
                .signWith(clave, algoritmo)
                .compact();
    }

    /** Un JWS armado sin JJWT, para poder declarar el algoritmo que se quiera. */
    private static String aMano(String algoritmo, String algoritmoJava, byte[] clave,
                                String cuerpoJson) throws Exception {
        Base64.Encoder b64 = Base64.getUrlEncoder().withoutPadding();
        String cabecera = b64.encodeToString(
                ("{\"alg\":\"" + algoritmo + "\"}").getBytes(StandardCharsets.UTF_8));
        String cuerpo = b64.encodeToString(cuerpoJson.getBytes(StandardCharsets.UTF_8));
        Mac mac = Mac.getInstance(algoritmoJava);
        mac.init(new SecretKeySpec(clave, algoritmoJava));
        byte[] firma = mac.doFinal((cabecera + "." + cuerpo).getBytes(StandardCharsets.US_ASCII));
        return cabecera + "." + cuerpo + "." + b64.encodeToString(firma);
    }

    private static String claveDePrueba(int bytes) {
        return Base64.getEncoder().encodeToString(bytesAleatorios(bytes));
    }

    private static byte[] bytesAleatorios(int cuantos) {
        byte[] bytes = new byte[cuantos];
        new SecureRandom().nextBytes(bytes);
        return bytes;
    }
}
