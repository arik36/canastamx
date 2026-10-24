
package mx.tecnm.canastamx.domain_service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;

import java.util.Base64;
import java.util.Map;
import java.util.UUID;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.transaction.annotation.Transactional;

// Cada prueba corre en una transacción que se revierte: no deja cuentas en la base.
@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class AutenticacionTests {

    @Autowired
    private MockMvc mockMvc;


    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${security.jwt.secret}")
    private String secreto;

    private String registrarCuenta() throws Exception {
        String correo = "prueba-" + UUID.randomUUID()
                + "@canastamx.mx";

        mockMvc.perform(post("/api/v1/cuentas")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(
                        Map.of(
                                "correo", correo,
                                "contrasena", "Prueba123"
                        )
                )))
                .andExpect(status().isCreated());

        return correo;
    }

    @Test
    void respuestaDeCuentaNoExponeLaContrasena() throws Exception {
        String correo = "prueba-" + UUID.randomUUID()
                + "@canastamx.mx";

        MvcResult resultado = mockMvc.perform(
                post("/api/v1/cuentas")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(
                                Map.of(
                                        "correo", correo,
                                        "contrasena", "Prueba123"
                                )
                        )))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").exists())
                .andExpect(jsonPath("$.correo").value(correo))
                .andExpect(jsonPath("$.rol").value("CONSUMIDOR"))
                .andExpect(jsonPath("$.fechaDeRegistro").exists())
                .andExpect(jsonPath("$.contrasena").doesNotExist())
                .andExpect(jsonPath("$.contrasenaHash").doesNotExist())
                .andReturn();

        JsonNode respuesta = objectMapper.readTree(
                resultado.getResponse().getContentAsString());

        assertEquals(4, respuesta.size());
    }

    @Test
    void tokenIncluyeElRolDelUsuario() throws Exception {
        String correo = registrarCuenta();

        MvcResult resultado = mockMvc.perform(
                post("/api/v1/sesiones")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(
                                Map.of(
                                        "correo", correo,
                                        "contrasena", "Prueba123"
                                )
                        )))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.token").isNotEmpty())
                .andExpect(jsonPath("$.expiraEn").exists())
                .andExpect(jsonPath("$.rol").value("CONSUMIDOR"))
                .andReturn();

        JsonNode respuesta = objectMapper.readTree(
                resultado.getResponse().getContentAsString());

        // La clave es JWT_SECRET decodificada (ADR 020), no su texto.
        var clave = Keys.hmacShaKeyFor(
                Base64.getDecoder().decode(secreto));

        var claims = Jwts.parser()
                .verifyWith(clave)
                .build()
                .parseSignedClaims(respuesta.get("token").asText())
                .getPayload();

        assertEquals("CONSUMIDOR", claims.get("rol", String.class));
    }

    @Test
    void contrasenaIncorrectaDevuelveHttp401() throws Exception {
        String correo = registrarCuenta();

        mockMvc.perform(
                post("/api/v1/sesiones")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(
                                Map.of(
                                        "correo", correo,
                                        "contrasena", "Incorrecta123"
                                )
                        )))
                .andExpect(status().isUnauthorized())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_PROBLEM_JSON))
                .andExpect(jsonPath("$.type").value("/problemas/sin-sesion"))
                .andExpect(jsonPath("$.title").isNotEmpty())
                .andExpect(jsonPath("$.status").value(401))
                .andExpect(jsonPath("$.mensaje").doesNotExist());
    }
}
