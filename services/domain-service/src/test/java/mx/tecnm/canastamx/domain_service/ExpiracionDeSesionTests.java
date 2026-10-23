package mx.tecnm.canastamx.domain_service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

/**
 * La sesión dura lo que dice security.jwt.expiration-minutes y expiraEn es el
 * claim exp del token. Usa 15 minutos, no los 60 por omisión, para demostrar
 * que la propiedad se lee.
 */
@SpringBootTest(properties = "security.jwt.expiration-minutes=15")
@AutoConfigureMockMvc
class ExpiracionDeSesionTests {

    @Autowired
    private MockMvc mockMvc;

    @Value("${security.jwt.secret}")
    private String secreto;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Test
    void expiraEnEsElExpDelTokenYLaSesionDuraQuinceMinutos() throws Exception {
        String credenciales = objectMapper.writeValueAsString(Map.of(
                "correo", "prueba-" + UUID.randomUUID() + "@canastamx.mx",
                "contrasena", "Prueba123"));

        mockMvc.perform(post("/api/v1/cuentas")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(credenciales))
                .andExpect(status().isCreated());

        String cuerpo = mockMvc.perform(post("/api/v1/sesiones")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(credenciales))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.token").isNotEmpty())
                .andExpect(jsonPath("$.expiraEn").isNotEmpty())
                .andReturn().getResponse().getContentAsString();

        JsonNode sesion = objectMapper.readTree(cuerpo);
        Claims claims = Jwts.parser()
                .verifyWith(Keys.hmacShaKeyFor(secreto.getBytes(StandardCharsets.UTF_8)))
                .build()
                .parseSignedClaims(sesion.get("token").asText())
                .getPayload();
        Instant iat = claims.getIssuedAt().toInstant();
        Instant exp = claims.getExpiration().toInstant();

        assertEquals(exp, Instant.parse(sesion.get("expiraEn").asText()));
        assertEquals(900L, Duration.between(iat, exp).getSeconds());
    }
}