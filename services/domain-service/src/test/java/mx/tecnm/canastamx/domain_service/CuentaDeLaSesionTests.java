package mx.tecnm.canastamx.domain_service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.time.Duration;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

import javax.crypto.SecretKey;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;

/**
 * GET /api/v1/cuentas/yo (D-10, opción A): con el token de /sesiones devuelve
 * la Cuenta de quien tiene la sesión, con sus cuatro campos y nada más. Sin una
 * sesión válida responde el 401 de dominio.yaml.
 */
@SpringBootTest
@AutoConfigureMockMvc
class CuentaDeLaSesionTests {

    private static final String YO = "/api/v1/cuentas/yo";
    private static final String SIN_SESION = "/problemas/sin-sesion";

    @Autowired
    private MockMvc mockMvc;

    @Value("${security.jwt.secret}")
    private String secreto;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Test
    void conElTokenDeSesionesDevuelveLaCuentaRegistradaYNadaMas() throws Exception {
        String correo = correoNuevo();
        JsonNode registrada = registrar(correo);
        String token = iniciarSesion(correo);

        String cuerpo = pedirMiCuenta("Bearer " + token)
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.id").value(registrada.get("id").asText()))
                .andExpect(jsonPath("$.correo").value(correo))
                .andExpect(jsonPath("$.rol").value("CONSUMIDOR"))
                .andReturn().getResponse().getContentAsString();

        JsonNode cuenta = objectMapper.readTree(cuerpo);
        assertEquals(4, cuenta.size());

        // La base guarda microsegundos y el registro responde con el reloj de
        // Java, que puede traer nanosegundos: se compara con un margen.
        Duration diferencia = Duration.between(
                Instant.parse(registrada.get("fechaDeRegistro").asText()),
                Instant.parse(cuenta.get("fechaDeRegistro").asText())).abs();
        assertTrue(diferencia.compareTo(Duration.ofMillis(1)) < 0);
    }

    @Test
    void sinUnaSesionValidaDevuelve401() throws Exception {
        String correo = correoNuevo();
        String id = registrar(correo).get("id").asText();
        String tokenValido = iniciarSesion(correo);

        SecretKey propia = Keys.hmacShaKeyFor(secreto.getBytes(StandardCharsets.UTF_8));
        SecretKey ajena = Keys.hmacShaKeyFor(bytesAleatorios());
        Instant ahora = Instant.now().truncatedTo(ChronoUnit.SECONDS);
        Instant enQuinceMinutos = ahora.plus(Duration.ofMinutes(15));

        // Cada caso se rechaza por una sola razón: los tokens firmados son de
        // una cuenta que existe, salvo el último.
        Map<String, String> casos = new LinkedHashMap<>();
        casos.put("sin encabezado", null);
        casos.put("token válido con otro esquema", "Token " + tokenValido);
        casos.put("token mal formado", "Bearer no-es-un-token");
        casos.put("firmado con otra clave",
                "Bearer " + token(id, ajena, ahora, enQuinceMinutos));
        casos.put("vencido", "Bearer " + token(id, propia,
                ahora.minus(Duration.ofHours(2)), ahora.minus(Duration.ofHours(1))));
        casos.put("de una cuenta que no existe", "Bearer "
                + token(UUID.randomUUID().toString(), propia, ahora, enQuinceMinutos));

        for (Map.Entry<String, String> caso : casos.entrySet()) {
            try {
                pedirMiCuenta(caso.getValue())
                        .andExpect(status().isUnauthorized())
                        .andExpect(content().contentTypeCompatibleWith(
                                MediaType.APPLICATION_PROBLEM_JSON))
                        .andExpect(jsonPath("$.type").value(SIN_SESION))
                        .andExpect(jsonPath("$.title").isNotEmpty())
                        .andExpect(jsonPath("$.status").value(401))
                        .andExpect(jsonPath("$.mensaje").doesNotExist());
            } catch (AssertionError error) {
                throw new AssertionError(caso.getKey() + ": " + error.getMessage(), error);
            }
        }
    }

    // ---------- ayudas ----------

    /** GET /cuentas/yo con ese Authorization; sin el encabezado si es null. */
    private ResultActions pedirMiCuenta(String autorizacion) throws Exception {
        if (autorizacion == null) {
            return mockMvc.perform(get(YO).accept(MediaType.APPLICATION_JSON));
        }
        return mockMvc.perform(get(YO)
                .header(HttpHeaders.AUTHORIZATION, autorizacion)
                .accept(MediaType.APPLICATION_JSON));
    }

    private JsonNode registrar(String correo) throws Exception {
        String cuerpo = mockMvc.perform(post("/api/v1/cuentas")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(credenciales(correo)))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();
        return objectMapper.readTree(cuerpo);
    }

    private String iniciarSesion(String correo) throws Exception {
        String cuerpo = mockMvc.perform(post("/api/v1/sesiones")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(credenciales(correo)))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString();
        return objectMapper.readTree(cuerpo).get("token").asText();
    }

    private String credenciales(String correo) throws Exception {
        return objectMapper.writeValueAsString(
                Map.of("correo", correo, "contrasena", "Prueba123"));
    }

    private static String correoNuevo() {
        return "prueba-" + UUID.randomUUID() + "@canastamx.mx";
    }

    private static String token(String id, SecretKey clave,
                                Instant emitidoEn, Instant expiraEn) {
        return Jwts.builder()
                .subject(id)
                .claim("rol", "CONSUMIDOR")
                .issuedAt(Date.from(emitidoEn))
                .expiration(Date.from(expiraEn))
                .signWith(clave)
                .compact();
    }

    // Clave aleatoria creada en cada corrida: el repositorio no guarda ninguna.
    private static byte[] bytesAleatorios() {
        byte[] bytes = new byte[32];
        new SecureRandom().nextBytes(bytes);
        return bytes;
    }
}
