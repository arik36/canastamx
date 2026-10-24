package mx.tecnm.canastamx.domain_service.infrastructure.web;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.stream.Collectors;

import org.yaml.snakeyaml.LoaderOptions;
import org.yaml.snakeyaml.Yaml;
import org.yaml.snakeyaml.constructor.SafeConstructor;

/**
 * Qué exige {@code dominio.yaml} de cada operación, leído como lo define OpenAPI 3.1,
 * y en qué se aparta de eso lo que implementan los controladores.
 *
 * <ul>
 *   <li>Si la operación tiene la propiedad {@code security}, rige ésa y la global no
 *       cuenta. Si no la tiene, hereda la {@code security} global del documento:
 *       omitirla no equivale a {@code security: []}.</li>
 *   <li>{@code security: []} declara pública la operación.</li>
 *   <li>Una lista con requisitos la protege, salvo que uno sea {@code {}}: con él la
 *       sesión es opcional, así que no se exige.</li>
 * </ul>
 *
 * Una operación se identifica por su método, en mayúsculas, y su ruta, con cada
 * variable como {@code {}}: {@code /canastas/{canastaId}} y {@code /canastas/{id}}
 * son la misma.
 */
final class SeguridadDelContrato {

    /** Relativa al directorio de trabajo de las pruebas, {@code services/domain-service}. */
    static final Path DOMINIO_YAML =
            Path.of("..", "..", "docs", "analisis", "openapi", "dominio.yaml");

    /** Los campos de un Path Item que son operaciones (OpenAPI 3.1). */
    private static final List<String> METODOS =
            List.of("get", "put", "post", "delete", "options", "head", "patch", "trace");

    private SeguridadDelContrato() {
    }

    /** Lo que el contrato dice de una operación: si exige sesión y de dónde sale. */
    record Declarada(boolean exigeSesion, String porque) {
    }

    /** Una operación que atiende un controlador; {@code metodo} es "*" si atiende cualquiera. */
    record Implementada(String metodo, String ruta, boolean pideSesion, String donde) {

        String clave() {
            return SeguridadDelContrato.clave(metodo, ruta);
        }

        @Override
        public String toString() {
            return metodo + " " + ruta + " (" + donde + ")";
        }
    }

    /** Las operaciones que declara el archivo, por {@link #clave}. */
    static Map<String, Declarada> leer(Path archivo) throws IOException {
        return declaradas(documento(archivo));
    }

    /** El archivo tal como lo lee SnakeYAML: mapas, listas y valores. */
    static Map<?, ?> documento(Path archivo) throws IOException {
        if (!Files.isRegularFile(archivo)) {
            throw new IllegalStateException("No está " + archivo.toAbsolutePath().normalize()
                    + ": las pruebas se corren desde services/domain-service");
        }
        return documento(Files.readString(archivo, StandardCharsets.UTF_8));
    }

    static Map<?, ?> documento(String yaml) {
        LoaderOptions opciones = new LoaderOptions();
        opciones.setAllowDuplicateKeys(false);   // una clave repetida no se resuelve en silencio
        return mapa(new Yaml(new SafeConstructor(opciones)).load(yaml), "el documento");
    }

    static Map<String, Declarada> declaradas(Map<?, ?> documento) {
        boolean hayGlobal = documento.containsKey("security");
        List<Map<?, ?>> global = hayGlobal
                ? requisitos(documento.get("security"), "la security global")
                : List.of();

        Map<String, Declarada> operaciones = new LinkedHashMap<>();
        mapa(documento.get("paths"), "paths").forEach((ruta, item) -> {
            Map<?, ?> camino = mapa(item, String.valueOf(ruta));
            if (camino.containsKey("$ref")) {
                throw new IllegalArgumentException(
                        "dominio.yaml: " + ruta + " usa $ref, y esta prueba no lo sigue");
            }
            for (String metodo : METODOS) {
                if (!camino.containsKey(metodo)) {
                    continue;
                }
                String operacion = metodo.toUpperCase(Locale.ROOT) + " " + ruta;
                Map<?, ?> objeto = mapa(camino.get(metodo), operacion);
                Declarada declarada;
                if (objeto.containsKey("security")) {
                    declarada = declarada(requisitos(objeto.get("security"), operacion),
                            "en la operación");
                } else if (hayGlobal) {
                    declarada = declarada(global, "heredada de la global");
                } else {
                    declarada = new Declarada(false, "sin security en la operación ni global");
                }
                if (operaciones.put(clave(metodo, String.valueOf(ruta)), declarada) != null) {
                    throw new IllegalArgumentException("dominio.yaml: " + operacion
                            + " repite una ruta que sólo cambia el nombre de una variable");
                }
            }
        });
        return operaciones;
    }

    /**
     * Cada operación implementada que no cumple lo que el contrato declara, con su
     * método, su ruta, el método del controlador y el motivo. Las operaciones del
     * contrato que nadie implementa todavía no cuentan.
     */
    static List<String> discrepancias(Map<String, Declarada> contrato,
                                      List<Implementada> implementadas) {
        List<String> encontradas = new ArrayList<>();
        for (Implementada ruta : implementadas) {
            Declarada declarada = contrato.get(ruta.clave());
            if ("*".equals(ruta.metodo())) {
                encontradas.add(ruta + ": atiende cualquier método HTTP;"
                        + " dominio.yaml declara cada operación con el suyo");
            } else if (declarada == null) {
                encontradas.add(ruta + ": está implementada, pero dominio.yaml no la declara");
            } else if (declarada.exigeSesion() && !ruta.pideSesion()) {
                encontradas.add(ruta + ": dominio.yaml exige sesión (" + declarada.porque()
                        + ") y el método no recibe @CuentaDeLaSesion");
            } else if (!declarada.exigeSesion() && ruta.pideSesion()) {
                encontradas.add(ruta + ": dominio.yaml no exige sesión (" + declarada.porque()
                        + ") y el método recibe @CuentaDeLaSesion");
            }
        }
        return encontradas;
    }

    /** El método en mayúsculas y la ruta con cada variable como {@code {}}. */
    static String clave(String metodo, String ruta) {
        return metodo.toUpperCase(Locale.ROOT) + " "
                + ruta.replaceAll("\\{[^/]*?\\}(?=/|$)", "{}");
    }

    private static Declarada declarada(List<Map<?, ?>> requisitos, String origen) {
        boolean opcional = requisitos.stream().anyMatch(Map::isEmpty);
        String lista = requisitos.stream()
                .map(r -> r.isEmpty() ? "{}" : r.keySet().stream()
                        .map(String::valueOf).collect(Collectors.joining(" + ")))
                .collect(Collectors.joining(", ", "[", "]"));
        String porque = "security: " + lista + " " + origen
                + (opcional ? "; con {} la sesión es opcional" : "");
        return new Declarada(!requisitos.isEmpty() && !opcional, porque);
    }

    private static List<Map<?, ?>> requisitos(Object valor, String donde) {
        if (!(valor instanceof List<?> lista)) {
            throw new IllegalArgumentException("dominio.yaml: " + donde
                    + ": security tiene que ser una lista; para declararla pública, security: []");
        }
        List<Map<?, ?>> requisitos = new ArrayList<>();
        for (Object requisito : lista) {
            requisitos.add(mapa(requisito, donde + ", en security"));
        }
        return requisitos;
    }

    private static Map<?, ?> mapa(Object valor, String donde) {
        if (!(valor instanceof Map<?, ?> mapa)) {
            throw new IllegalArgumentException(
                    "dominio.yaml: " + donde + " tendría que ser un objeto");
        }
        return mapa;
    }
}
