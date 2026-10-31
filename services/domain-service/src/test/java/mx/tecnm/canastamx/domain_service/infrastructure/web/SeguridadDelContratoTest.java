package mx.tecnm.canastamx.domain_service.infrastructure.web;

import static mx.tecnm.canastamx.domain_service.infrastructure.web.SeguridadDelContrato.declaradas;
import static mx.tecnm.canastamx.domain_service.infrastructure.web.SeguridadDelContrato.discrepancias;
import static mx.tecnm.canastamx.domain_service.infrastructure.web.SeguridadDelContrato.documento;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.util.List;
import java.util.Map;

import mx.tecnm.canastamx.domain_service.infrastructure.web.SeguridadDelContrato.Declarada;
import mx.tecnm.canastamx.domain_service.infrastructure.web.SeguridadDelContrato.Implementada;

import org.junit.jupiter.api.Test;
import org.yaml.snakeyaml.constructor.DuplicateKeyException;

/**
 * Cómo lee SeguridadDelContrato la security de OpenAPI y qué informa, sin Spring ni
 * base de datos. Los contratos de aquí son de prueba; el real lo compara
 * RutasProtegidasTests con los controladores.
 */
class SeguridadDelContratoTest {

    private static final String CON_GLOBAL = """
            security:
              - sesion: []
            """;

    @Test
    void omitirSecurityHeredaLaGlobalYSecurityVaciaLaAnula() {
        Map<String, Declarada> contrato = contrato(CON_GLOBAL + """
                paths:
                  /protegida:
                    get: {}
                  /publica:
                    get:
                      security: []
                """);

        assertEquals(new Declarada(true, "security: [sesion] heredada de la global"),
                contrato.get("GET /protegida"));
        assertEquals(new Declarada(false, "security: [] en la operación"),
                contrato.get("GET /publica"));
    }

    @Test
    void sinSecurityGlobalSoloExigeSesionLaOperacionQueDeclaraUnRequisito() {
        Map<String, Declarada> contrato = contrato("""
                paths:
                  /a:
                    get:
                      security:
                        - sesion: []
                    post: {}
                    put:
                      security: []
                """);

        assertEquals(new Declarada(true, "security: [sesion] en la operación"),
                contrato.get("GET /a"));
        assertEquals(new Declarada(false, "sin security en la operación ni global"),
                contrato.get("POST /a"));
        assertEquals(new Declarada(false, "security: [] en la operación"),
                contrato.get("PUT /a"));
    }

    @Test
    void conUnRequisitoVacioLaSesionEsOpcionalYNoSeExige() {
        Map<String, Declarada> contrato = contrato(CON_GLOBAL + """
                paths:
                  /a:
                    get:
                      security: [{}]
                    post:
                      security:
                        - sesion: []
                        - {}
                """);

        assertEquals(new Declarada(false,
                        "security: [{}] en la operación; con {} la sesión es opcional"),
                contrato.get("GET /a"));
        assertEquals(new Declarada(false,
                        "security: [sesion, {}] en la operación; con {} la sesión es opcional"),
                contrato.get("POST /a"));
    }

    @Test
    void soloLosMetodosSonOperacionesYLasVariablesSeNormalizan() {
        Map<String, Declarada> contrato = contrato(CON_GLOBAL + """
                paths:
                  /canastas/{canastaId}/lineas:
                    summary: Las líneas de una canasta
                    parameters:
                      - name: canastaId
                        in: path
                        required: true
                    delete: {}
                """);

        assertEquals(List.of("DELETE /canastas/{}/lineas"), List.copyOf(contrato.keySet()));
    }

    @Test
    void unaSecurityQueNoEsListaEsUnErrorQueNombraLaOperacion() {
        IllegalArgumentException error = assertThrows(IllegalArgumentException.class,
                () -> contrato(CON_GLOBAL + """
                        paths:
                          /a:
                            post:
                              security:
                        """));

        assertTrue(error.getMessage().contains("POST /a"), error.getMessage());
    }

    @Test
    void unaClaveRepetidaNoSeResuelveEnSilencio() {
        assertThrows(DuplicateKeyException.class, () -> contrato(CON_GLOBAL + """
                paths:
                  /a:
                    get:
                      security: []
                      security:
                        - sesion: []
                """));
    }

    @Test
    void cadaDiscrepanciaDiceMetodoRutaControladorYMotivo() {
        Map<String, Declarada> contrato = contrato(CON_GLOBAL + """
                paths:
                  /publica:
                    post:
                      security: []
                  /protegida/{id}:
                    get: {}
                  /futura:
                    get: {}
                """);
        List<Implementada> implementadas = List.of(
                new Implementada("POST", "/publica", true, "A#crear"),
                new Implementada("GET", "/protegida/{cuentaId}", false, "B#ver"),
                new Implementada("GET", "/sin-contrato", false, "C#ver"),
                new Implementada("*", "/cualquiera", false, "D#todo"));

        // GET /futura está declarada y sin implementar: no cuenta.
        assertEquals(List.of(
                "POST /publica (A#crear): dominio.yaml no exige sesión"
                        + " (security: [] en la operación) y el método recibe @CuentaDeLaSesion",
                "GET /protegida/{cuentaId} (B#ver): dominio.yaml exige sesión"
                        + " (security: [sesion] heredada de la global)"
                        + " y el método no recibe @CuentaDeLaSesion",
                "GET /sin-contrato (C#ver): está implementada, pero dominio.yaml no la declara",
                "* /cualquiera (D#todo): atiende cualquier método HTTP;"
                        + " dominio.yaml declara cada operación con el suyo"),
                discrepancias(contrato, implementadas));
    }

    @Test
    void cambiarLaSecurityEnElYamlSeDetectaSinTocarLaImplementacion() {
        String yaml = CON_GLOBAL + """
                paths:
                  /sesiones:
                    post:
                      summary: Iniciar sesión
                      security: []
                  /cuentas/yo:
                    get:
                      summary: La cuenta de la sesión
                """;
        List<Implementada> implementadas = List.of(
                new Implementada("POST", "/sesiones", false, "Sesiones#iniciar"),
                new Implementada("GET", "/cuentas/yo", true, "Cuentas#yo"));

        assertEquals(List.of(), discrepancias(contrato(yaml), implementadas));

        // Se borra «security: []»: la operación hereda la global y exige sesión.
        assertEquals(List.of("POST /sesiones (Sesiones#iniciar): dominio.yaml exige sesión"
                        + " (security: [sesion] heredada de la global)"
                        + " y el método no recibe @CuentaDeLaSesion"),
                discrepancias(contrato(yaml.replace("      security: []\n", "")), implementadas));

        // Se declara pública la de la cuenta.
        assertEquals(List.of("GET /cuentas/yo (Cuentas#yo): dominio.yaml no exige sesión"
                        + " (security: [] en la operación) y el método recibe @CuentaDeLaSesion"),
                discrepancias(contrato(yaml.replace("      summary: La cuenta de la sesión\n",
                        "      summary: La cuenta de la sesión\n      security: []\n")),
                        implementadas));
    }

    @Test
    void elDominioYamlRealSeLee() throws IOException {
        assertFalse(SeguridadDelContrato.leer(SeguridadDelContrato.DOMINIO_YAML).isEmpty());
    }

    private static Map<String, Declarada> contrato(String yaml) {
        return declaradas(documento(yaml));
    }
}
