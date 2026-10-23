package mx.tecnm.canastamx.domain_service.infrastructure.web;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import mx.tecnm.canastamx.domain_service.application.service.InicioSesionService;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;

/**
 * Sólo la capa web de /sesiones, sin base de datos: el servicio es un doble.
 * Lo que no pasa la validación responde el mismo 401 que unas credenciales
 * inválidas y no llega al servicio; un error inesperado no se vuelve 401.
 */
@WebMvcTest(controllers = SesionController.class)
class SesionControllerTest {

    private static final String SESIONES = "/api/v1/sesiones";
    private static final String SIN_SESION = "/problemas/sin-sesion";

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private InicioSesionService inicioSesionService;

    @Test
    void camposAusentesNulosOConTipoIncorrectoDevuelven401SinLlegarAlServicio() throws Exception {
        String[] cuerpos = {
                "{}",
                "{\"correo\": null, \"contrasena\": null}",
                "{\"correo\": \"prueba@canastamx.mx\"}",
                "{\"contrasena\": \"Prueba123\"}",
                "{\"correo\": 123, \"contrasena\": true}",
                "{\"correo\": [\"prueba@canastamx.mx\"], \"contrasena\": \"Prueba123\"}",
                "null",
                ""
        };
        for (String cuerpo : cuerpos) {
            esSinSesion(enviar(cuerpo));
        }
        verifyNoInteractions(inicioSesionService);
    }

    @Test
    void laValidacionRespondeLoMismoQueCredencialesInvalidas() throws Exception {
        when(inicioSesionService.iniciar(any(), any()))
                .thenThrow(new InicioSesionService.CredencialesInvalidasException());

        String porCredenciales = esSinSesion(enviar(
                "{\"correo\": \"prueba@canastamx.mx\", \"contrasena\": \"Incorrecta123\"}"))
                .andReturn().getResponse().getContentAsString();
        String porValidacion = esSinSesion(enviar("{}"))
                .andReturn().getResponse().getContentAsString();

        assertEquals(porCredenciales, porValidacion);
    }

    @Test
    void unErrorInesperadoNoSeConvierteEn401() {
        IllegalStateException inesperado = new IllegalStateException("fallo inesperado");
        when(inicioSesionService.iniciar(any(), any())).thenThrow(inesperado);

        // Ningún manejador lo atiende: sale del controlador tal cual, envuelto
        // por el servlet, en lugar de convertirse en un 401.
        Exception error = assertThrows(Exception.class, () -> enviar(
                "{\"correo\": \"prueba@canastamx.mx\", \"contrasena\": \"Prueba123\"}"));

        assertSame(inesperado, causaRaiz(error));
    }

    private ResultActions enviar(String cuerpo) throws Exception {
        return mockMvc.perform(post(SESIONES)
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)
                .content(cuerpo));
    }

    private ResultActions esSinSesion(ResultActions resultado) throws Exception {
        return resultado
                .andExpect(status().isUnauthorized())
                .andExpect(content().contentTypeCompatibleWith(
                        MediaType.APPLICATION_PROBLEM_JSON))
                .andExpect(jsonPath("$.type").value(SIN_SESION))
                .andExpect(jsonPath("$.title").isNotEmpty())
                .andExpect(jsonPath("$.status").value(401))
                .andExpect(jsonPath("$.mensaje").doesNotExist());
    }

    private static Throwable causaRaiz(Throwable error) {
        Throwable causa = error;
        while (causa.getCause() != null && causa.getCause() != causa) {
            causa = causa.getCause();
        }
        return causa;
    }
}
