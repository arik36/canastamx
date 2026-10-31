package mx.tecnm.canastamx.domain_service.infrastructure.web;

import static mx.tecnm.canastamx.domain_service.infrastructure.web.SeguridadDelContrato.DOMINIO_YAML;
import static mx.tecnm.canastamx.domain_service.infrastructure.web.SeguridadDelContrato.declaradas;
import static mx.tecnm.canastamx.domain_service.infrastructure.web.SeguridadDelContrato.discrepancias;
import static mx.tecnm.canastamx.domain_service.infrastructure.web.SeguridadDelContrato.documento;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assumptions.assumeTrue;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Set;

import mx.tecnm.canastamx.domain_service.domain.usuario.Usuario;
import mx.tecnm.canastamx.domain_service.infrastructure.web.SeguridadDelContrato.Declarada;
import mx.tecnm.canastamx.domain_service.infrastructure.web.SeguridadDelContrato.Implementada;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping;

/**
 * Cada ruta de los controladores recibe {@code @CuentaDeLaSesion} si y sólo si
 * {@code docs/analisis/openapi/dominio.yaml} exige sesión en esa operación, por su
 * {@code security} o por la global (ver {@link SeguridadDelContrato}). No hay una lista
 * de rutas públicas aparte: si cambia el contrato o un controlador sin el otro, la
 * prueba falla y dice el método, la ruta y el motivo. Las operaciones del contrato
 * que todavía no tienen controlador (hoy, las de canastas y alertas) no cuentan.
 */
@SpringBootTest
@AutoConfigureMockMvc
class RutasProtegidasTests {

    @Autowired
    @Qualifier("requestMappingHandlerMapping")
    private RequestMappingHandlerMapping rutas;

    @Test
    void cadaRutaPideSesionSiYSoloSiDominioYamlLaExige() throws IOException {
        List<Implementada> implementadas = implementadas();
        assertFalse(implementadas.isEmpty(), "no se encontró ninguna ruta de CanastaMX");

        List<String> encontradas =
                discrepancias(SeguridadDelContrato.leer(DOMINIO_YAML), implementadas);

        assertTrue(encontradas.isEmpty(), () -> "No cumplen lo que declara"
                + " docs/analisis/openapi/dominio.yaml:\n  " + String.join("\n  ", encontradas));
    }

    /** Si dominio.yaml cambia la security de una ruta y su controlador no, se detecta. */
    @Test
    void cambiarEnDominioYamlLaSeguridadDeUnaRutaImplementadaSeDetecta() throws IOException {
        List<Implementada> implementadas = implementadas();
        siLaComparacionRealNoFallaYa(implementadas);
        for (Implementada ruta : implementadas) {
            Map<?, ?> documento = documento(DOMINIO_YAML);   // una copia en memoria
            Map<Object, Object> operacion = operacion(documento, ruta.clave());
            boolean exigia = declaradas(documento).get(ruta.clave()).exigeSesion();
            // Lo que haría quien edita el contrato: declararla pública, o protegerla.
            operacion.put("security", exigia ? List.of() : List.of(Map.of("sesion", List.of())));

            List<String> encontradas = discrepancias(declaradas(documento), implementadas);

            assertEquals(1, encontradas.size(), ruta + ": " + encontradas);
            assertTrue(encontradas.get(0).startsWith(ruta + ": "), encontradas.get(0));
        }
    }

    /** Una operación que exige sesión, hecha o por hacer, sin la anotación se detecta. */
    @Test
    void implementarSinLaAnotacionUnaOperacionQueExigeSesionSeDetecta() throws IOException {
        Map<String, Declarada> contrato = SeguridadDelContrato.leer(DOMINIO_YAML);
        List<Implementada> reales = implementadas();
        siLaComparacionRealNoFallaYa(reales);
        contrato.forEach((clave, declarada) -> {
            if (!declarada.exigeSesion()) {
                return;
            }
            String[] metodoYRuta = clave.split(" ", 2);
            Implementada olvidada =
                    new Implementada(metodoYRuta[0], metodoYRuta[1], false, "Nuevo#metodo");
            List<Implementada> conElOlvido = new ArrayList<>(reales);
            conElOlvido.removeIf(real -> real.clave().equals(clave));
            conElOlvido.add(olvidada);

            List<String> encontradas = discrepancias(contrato, conElOlvido);

            assertEquals(1, encontradas.size(), clave + ": " + encontradas);
            assertTrue(encontradas.get(0).startsWith(olvidada + ": dominio.yaml exige sesión"),
                    encontradas.get(0));
        });
    }

    @Test
    void cuentaDeLaSesionSoloVaEnParametrosUsuario() {
        List<String> mal = new ArrayList<>();
        rutas.getHandlerMethods().forEach((info, metodo) -> Arrays.stream(metodo.getMethodParameters())
                .filter(p -> p.hasParameterAnnotation(CuentaDeLaSesion.class))
                .filter(p -> !Usuario.class.equals(p.getParameterType()))
                .forEach(p -> mal.add(metodo.getShortLogMessage())));

        assertEquals(List.of(), mal);
    }

    /** Las operaciones que atienden los controladores de CanastaMX, con o sin la anotación. */
    private List<Implementada> implementadas() {
        List<Implementada> implementadas = new ArrayList<>();
        rutas.getHandlerMethods().forEach((info, metodo) -> {
            if (!esNuestra(metodo)) {
                return;
            }
            boolean pideSesion = Arrays.stream(metodo.getMethodParameters())
                    .anyMatch(p -> p.hasParameterAnnotation(CuentaDeLaSesion.class));
            String donde = metodo.getBeanType().getSimpleName() + "#"
                    + metodo.getMethod().getName();
            Set<RequestMethod> verbos = info.getMethodsCondition().getMethods();
            for (String patron : info.getPatternValues()) {
                if (verbos.isEmpty()) {
                    implementadas.add(new Implementada("*", patron, pideSesion, donde));
                }
                for (RequestMethod verbo : verbos) {
                    implementadas.add(new Implementada(verbo.name(), patron, pideSesion, donde));
                }
            }
        });
        implementadas.sort(Comparator.comparing(Implementada::toString));
        return implementadas;
    }

    /**
     * Las dos pruebas que cambian el contrato o una ruta en memoria parten de que la
     * comparación real no tiene discrepancias. Si ya las tiene, las informa la primera
     * prueba y éstas se omiten, en vez de fallar con un conteo que confunde.
     */
    private static void siLaComparacionRealNoFallaYa(List<Implementada> implementadas)
            throws IOException {
        List<String> encontradas =
                discrepancias(SeguridadDelContrato.leer(DOMINIO_YAML), implementadas);
        assumeTrue(encontradas.isEmpty(),
                "cadaRutaPideSesionSiYSoloSiDominioYamlLaExige ya falla; se revisa cuando pase");
    }

    /** Deja fuera las rutas de Spring, como {@code /error}. */
    private static boolean esNuestra(HandlerMethod metodo) {
        return metodo.getBeanType().getName().startsWith("mx.tecnm.canastamx.");
    }

    /** El objeto de una operación dentro del documento, para cambiarlo en memoria. */
    @SuppressWarnings("unchecked")
    private static Map<Object, Object> operacion(Map<?, ?> documento, String clave) {
        for (Map.Entry<?, ?> camino : ((Map<?, ?>) documento.get("paths")).entrySet()) {
            for (Map.Entry<?, ?> campo : ((Map<?, ?>) camino.getValue()).entrySet()) {
                String esta = SeguridadDelContrato.clave(
                        String.valueOf(campo.getKey()), String.valueOf(camino.getKey()));
                if (esta.equals(clave)) {
                    return (Map<Object, Object>) campo.getValue();
                }
            }
        }
        throw new IllegalArgumentException("dominio.yaml no declara " + clave);
    }
}
