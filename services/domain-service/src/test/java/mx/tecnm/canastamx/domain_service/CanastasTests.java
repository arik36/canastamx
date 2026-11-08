package mx.tecnm.canastamx.domain_service;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import java.util.List;
import java.util.UUID;
import com.fasterxml.jackson.databind.ObjectMapper;
import mx.tecnm.canastamx.domain_service.infrastructure.security.JwtService;
import mx.tecnm.canastamx.domain_service.infrastructure.persistence.UsuarioRepository;
import mx.tecnm.canastamx.domain_service.domain.usuario.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;
import org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder;
import org.springframework.transaction.annotation.Transactional;

@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class CanastasTests {
    @Autowired MockMvc mvc;
    @Autowired JdbcTemplate jdbc;
    @Autowired JwtService jwt;
    @Autowired UsuarioRepository usuarios;
    private final ObjectMapper json = new ObjectMapper();
    private static final String RUTA = "/api/v1/canastas";
    private static final String LECHE = "{\"articulo\":{\"producto\":\"Léche\",\"presentacion\":\"1 L\"},\"cantidad\":3}";

    private String cuenta() {
        String id = UUID.randomUUID().toString();
        jdbc.update("INSERT INTO usuario (id, correo_electronico, contrasena_hash) VALUES (?, ?, ?)",
                id, "prueba-" + id + "@canastamx.mx", "$2a$hash-de-prueba");
        return jwt.generarToken(usuarios.buscarPorId(id).orElseThrow()).token();
    }

    private ResultActions enviar(MockHttpServletRequestBuilder peticion, String token, String cuerpo)
            throws Exception {
        if (token != null) peticion.header("Authorization", "Bearer " + token);
        if (cuerpo != null) peticion.contentType(MediaType.APPLICATION_JSON).content(cuerpo);
        return mvc.perform(peticion);
    }

    private String crear(String token, String nombre) throws Exception {
        String cuerpo = enviar(post(RUTA), token, json.writeValueAsString(java.util.Map.of("nombre", nombre)))
                .andExpect(status().isCreated()).andExpect(jsonPath("$.lineas").isEmpty())
                .andExpect(jsonPath("$.usuarioId").doesNotExist()).andReturn().getResponse().getContentAsString();
        assertEquals(3, json.readTree(cuerpo).size());
        return RUTA + "/" + json.readTree(cuerpo).get("id").asText();
    }

    private void problema(ResultActions resultado, int codigo) throws Exception {
        resultado.andExpect(status().is(codigo))
                .andExpect(content().contentTypeCompatibleWith("application/problem+json"))
                .andExpect(jsonPath("$.type").isNotEmpty())
                .andExpect(jsonPath("$.title").isNotEmpty())
                .andExpect(jsonPath("$.status").value(codigo));
    }

    @Test
    void ochoOperacionesPersistenYRespetanElContrato() throws Exception {
        String token = cuenta();
        String ruta = crear(token, "Despensa");
        enviar(post(ruta + "/lineas"), token, LECHE).andExpect(status().isOk())
                .andExpect(jsonPath("$.lineas[0].cantidad").value(3))
                .andExpect(jsonPath("$.lineas[0].articulo.producto").value("leche"));
        enviar(post(ruta + "/lineas"), token, LECHE).andExpect(status().isOk())
                .andExpect(jsonPath("$.lineas.length()").value(1))
                .andExpect(jsonPath("$.lineas[0].cantidad").value(6));
        enviar(put(ruta + "/lineas"), token, LECHE.replace(":3", ":2"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.lineas[0].cantidad").value(2));
        enviar(patch(ruta), token, "{\"nombre\":\"Semanal\"}").andExpect(status().isOk())
                .andExpect(jsonPath("$.nombre").value("Semanal"));
        enviar(get(ruta), token, null).andExpect(status().isOk())
                .andExpect(jsonPath("$.nombre").value("Semanal"))
                .andExpect(jsonPath("$.lineas[0].cantidad").value(2));
        enviar(get(RUTA), token, null).andExpect(status().isOk())
                .andExpect(jsonPath("$.total").value(1))
                .andExpect(jsonPath("$.canastas[0].lineas[0].cantidad").value(2));
        enviar(delete(ruta + "/lineas").param("producto", "leche").param("presentacion", "1 l"), token, null)
                .andExpect(status().isOk()).andExpect(jsonPath("$.lineas").isEmpty());
        enviar(delete(ruta), token, null).andExpect(status().isNoContent()).andExpect(content().string(""));
        problema(enviar(get(ruta), token, null), 404);
    }

    @Test
    void canastaAjenaONoExistenteEs404EnLasSeisOperaciones() throws Exception {
        String propio = cuenta();
        String ajeno = cuenta();
        String ruta = crear(propio, "Privada");
        for (String destino : List.of(ruta, RUTA + "/inexistente")) {
            problema(enviar(get(destino), ajeno, null), 404);
            problema(enviar(patch(destino), ajeno, "{\"nombre\":\"Ajena\"}"), 404);
            problema(enviar(delete(destino), ajeno, null), 404);
            problema(enviar(post(destino + "/lineas"), ajeno, LECHE), 404);
            problema(enviar(put(destino + "/lineas"), ajeno, LECHE), 404);
            problema(enviar(delete(destino + "/lineas").param("producto", "leche")
                    .param("presentacion", "1 l"), ajeno, null), 404);
        }
        enviar(get(RUTA), ajeno, null).andExpect(jsonPath("$.total").value(0));
        enviar(get(ruta), propio, null).andExpect(jsonPath("$.nombre").value("Privada"))
                .andExpect(jsonPath("$.lineas").isEmpty());
    }

    @Test
    void fijarOQuitarArticuloAusenteNoCambiaLaCanasta() throws Exception {
        String token = cuenta();
        String ruta = crear(token, "Prueba");
        enviar(post(ruta + "/lineas"), token, LECHE).andExpect(status().isOk());
        problema(enviar(put(ruta + "/lineas"), token, LECHE.replace("Léche", "Arroz")), 404);
        problema(enviar(delete(ruta + "/lineas").param("producto", "arroz").param("presentacion", "1 l"), token, null), 404);
        enviar(get(ruta), token, null).andExpect(jsonPath("$.lineas.length()").value(1))
                .andExpect(jsonPath("$.lineas[0].cantidad").value(3));
    }

    @Test
    void ochoOperacionesSinSesionSonProblem401() throws Exception {
        for (String token : new String[] {null, "invalido"}) {
            problema(enviar(get(RUTA), token, null), 401);
            problema(enviar(post(RUTA), token, "{\"nombre\":\"Prueba\"}"), 401);
            problema(enviar(get(RUTA + "/x"), token, null), 401);
            problema(enviar(patch(RUTA + "/x"), token, "{\"nombre\":\"Prueba\"}"), 401);
            problema(enviar(delete(RUTA + "/x"), token, null), 401);
            problema(enviar(post(RUTA + "/x/lineas"), token, LECHE), 401);
            problema(enviar(put(RUTA + "/x/lineas"), token, LECHE), 401);
            problema(enviar(delete(RUTA + "/x/lineas").param("producto", "leche").param("presentacion", "1 l"), token, null), 401);
        }
    }

    @Test
    void validaEntradasYPaginacionSinModificarDatos() throws Exception {
        String token = cuenta();
        String ruta = crear(token, "Prueba");
        for (String consulta : List.of("?limit=0", "?limit=101", "?offset=-1", "?limit=texto")) {
            problema(enviar(get(RUTA + consulta), token, null), 400);
        }
        for (String cuerpo : List.of("{}", "{", "{\"nombre\":\" \"}")) {
            problema(enviar(post(RUTA), token, cuerpo), 400);
            problema(enviar(patch(ruta), token, cuerpo), 400);
        }
        for (String cuerpo : List.of("{}", "{", LECHE.replace(":3", ":0"),
                LECHE.replace(":3", ":null"), LECHE.replace(":3", ":1.5"),
                LECHE.replace(":3", ":2147483648"), LECHE.replace("Léche", "..."))) {
            problema(enviar(post(ruta + "/lineas"), token, cuerpo), 400);
            problema(enviar(put(ruta + "/lineas"), token, cuerpo), 400);
        }
        problema(enviar(delete(ruta + "/lineas"), token, null), 400);
        problema(enviar(delete(ruta + "/lineas").param("producto", "...").param("presentacion", "1 l"), token, null), 400);
        enviar(get(ruta), token, null).andExpect(jsonPath("$.lineas").isEmpty());
        crear(token, "Otra");
        enviar(get(RUTA).param("limit", "1").param("offset", "1"), token, null)
                .andExpect(status().isOk()).andExpect(jsonPath("$.total").value(2))
                .andExpect(jsonPath("$.canastas.length()").value(1));
        enviar(get(RUTA).param("offset", "2"), token, null).andExpect(jsonPath("$.canastas").isEmpty())
                .andExpect(jsonPath("$.total").value(2));
    }

    @Test
    void borrarCanastaEliminaSusLineas() throws Exception {
        String token = cuenta();
        String ruta = crear(token, "Prueba");
        enviar(post(ruta + "/lineas"), token, LECHE).andExpect(status().isOk());
        enviar(delete(ruta), token, null).andExpect(status().isNoContent());
        assertEquals(0, jdbc.queryForObject("SELECT count(*) FROM linea_canasta WHERE canasta_id = ?",
                Integer.class, ruta.substring(ruta.lastIndexOf('/') + 1)));
    }
}
