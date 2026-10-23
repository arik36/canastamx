package mx.tecnm.canastamx.domain_service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.Map;
import java.util.UUID;

import com.fasterxml.jackson.databind.ObjectMapper;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;

/**
 * Errores de /cuentas y /sesiones tal como los declara dominio.yaml (P-03):
 * application/problem+json con type, title y status.
 */
@SpringBootTest
@AutoConfigureMockMvc
class ErroresDelContratoTests {

    private static final String CUENTAS = "/api/v1/cuentas";
    private static final String SESIONES = "/api/v1/sesiones";
    private static final String DATOS_INVALIDOS = "/problemas/datos-invalidos";
    private static final String CUENTA_DUPLICADA = "/problemas/cuenta-duplicada";
    private static final String SIN_SESION = "/problemas/sin-sesion";

    @Autowired
    private MockMvc mockMvc;

    private final ObjectMapper objectMapper = new ObjectMapper();

    // ---------- POST /api/v1/cuentas ----------

    @Test
    void registrarConCorreoInvalidoDevuelve400() throws Exception {
        // El primero lo rechaza @Email; el segundo pasa @Email y lo rechaza
        // CorreoElectronico (no tiene dominio con punto).
        for (String correo : new String[] {"no-es-correo", "persona@dominio"}) {
            esProblema(enviar(CUENTAS, credenciales(correo, "Prueba123")),
                    400, DATOS_INVALIDOS);
        }
    }

    @Test
    void registrarConContrasenaQueNoCumpleLaReglaDevuelve400() throws Exception {
        // Sin mayúscula, sin número y de 7 caracteres.
        for (String contrasena : new String[] {"prueba123", "PruebaSinNumero", "Prue123"}) {
            esProblema(enviar(CUENTAS, credenciales(correoNuevo(), contrasena)),
                    400, DATOS_INVALIDOS);
        }
    }

    @Test
    void registrarConCuerpoIlegibleDevuelve400() throws Exception {
        esProblema(enviar(CUENTAS, "{\"correo\": "), 400, DATOS_INVALIDOS);
    }

    @Test
    void registrarDosVecesElMismoCorreoDevuelve409() throws Exception {
        String correo = correoNuevo();
        enviar(CUENTAS, credenciales(correo, "Prueba123"))
                .andExpect(status().isCreated());

        esProblema(enviar(CUENTAS, credenciales(correo, "Prueba123")),
                409, CUENTA_DUPLICADA);
    }

    // ---------- POST /api/v1/sesiones ----------

    @Test
    void correoInexistenteYContrasenaIncorrectaDevuelvenElMismo401() throws Exception {
        String correo = correoNuevo();
        enviar(CUENTAS, credenciales(correo, "Prueba123"))
                .andExpect(status().isCreated());

        String conContrasenaIncorrecta = esProblema(
                enviar(SESIONES, credenciales(correo, "Incorrecta123")),
                401, SIN_SESION)
                .andReturn().getResponse().getContentAsString();

        String conCorreoInexistente = esProblema(
                enviar(SESIONES, credenciales(correoNuevo(), "Prueba123")),
                401, SIN_SESION)
                .andReturn().getResponse().getContentAsString();

        // Mismo cuerpo: la respuesta no revela si el correo tiene cuenta.
        assertEquals(conContrasenaIncorrecta, conCorreoInexistente);
    }

    @Test
    void correoMalFormadoOCamposVaciosDevuelven401YNo400() throws Exception {
        esProblema(enviar(SESIONES, credenciales("no-es-correo", "Prueba123")),
                401, SIN_SESION);
        esProblema(enviar(SESIONES, credenciales("", "")),
                401, SIN_SESION);
    }

    @Test
    void iniciarSesionConCuerpoIlegibleDevuelve401() throws Exception {
        esProblema(enviar(SESIONES, "{\"correo\": "), 401, SIN_SESION);
    }

    // ---------- ayudas ----------

    private ResultActions enviar(String ruta, String cuerpo) throws Exception {
        return mockMvc.perform(post(ruta)
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)
                .content(cuerpo));
    }

    /** Lo que exige P-03 a cualquier error: código, tipo de contenido y campos. */
    private ResultActions esProblema(ResultActions resultado, int estado, String tipo)
            throws Exception {
        return resultado
                .andExpect(status().is(estado))
                .andExpect(content().contentTypeCompatibleWith(
                        MediaType.APPLICATION_PROBLEM_JSON))
                .andExpect(jsonPath("$.type").value(tipo))
                .andExpect(jsonPath("$.title").isNotEmpty())
                .andExpect(jsonPath("$.status").value(estado))
                .andExpect(jsonPath("$.mensaje").doesNotExist());
    }

    private String credenciales(String correo, String contrasena) throws Exception {
        return objectMapper.writeValueAsString(
                Map.of("correo", correo, "contrasena", contrasena));
    }

    private String correoNuevo() {
        return "prueba-" + UUID.randomUUID() + "@canastamx.mx";
    }
}