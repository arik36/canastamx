package mx.tecnm.canastamx.domain_service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.lang.reflect.RecordComponent;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;
import mx.tecnm.canastamx.domain_service.application.service.InicioSesionService;
import mx.tecnm.canastamx.domain_service.domain.usuario.Rol;
import mx.tecnm.canastamx.domain_service.infrastructure.web.CuentaController;
import mx.tecnm.canastamx.domain_service.infrastructure.web.SesionController;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.yaml.snakeyaml.LoaderOptions;
import org.yaml.snakeyaml.Yaml;
import org.yaml.snakeyaml.constructor.SafeConstructor;

/**
 * Comprueba que los cuatro cuerpos JSON de CU-08 coincidan con dominio.yaml.
 * Se ejecuta sin levantar Spring ni escribir en PostgreSQL.
 */
class ContratoOpenApiEsquemasTest {

    private static final Path CONTRATO = Path.of(
            "..", "..", "docs", "analisis", "openapi", "dominio.yaml");

    private static final JsonMapper JSON = JsonMapper.builder().build();

    private static Map<String, Object> esquemas;

    @BeforeAll
    static void cargarContratoOpenApi() throws IOException {
        assertTrue(Files.isRegularFile(CONTRATO),
                "No se encontró el contrato OpenAPI en " + CONTRATO.toAbsolutePath());

        Object documento;
        try (var lector = Files.newBufferedReader(CONTRATO)) {
            documento = new Yaml(new SafeConstructor(new LoaderOptions())).load(lector);
        }

        Map<String, Object> raiz = mapa(documento, "documento OpenAPI");
        Map<String, Object> componentes = mapa(raiz.get("components"), "components");
        esquemas = mapa(componentes.get("schemas"), "components.schemas");
    }

    @Test
    void registroCoincideConDominioYaml() throws Exception {
        comprobar("Registro",
                CuentaController.RegistroSolicitud.class,
                new CuentaController.RegistroSolicitud(
                        "persona@tecnm.mx", "Prueba123"));
    }

    @Test
    void credencialesCoincideConDominioYaml() throws Exception {
        comprobar("Credenciales",
                SesionController.InicioSolicitud.class,
                new SesionController.InicioSolicitud(
                        "persona@tecnm.mx", "Prueba123"));
    }

    @Test
    void cuentaCoincideConDominioYamlYNoTieneCamposAdicionales() throws Exception {
        comprobar("Cuenta",
                CuentaController.CuentaRespuesta.class,
                new CuentaController.CuentaRespuesta(
                        "usuario-prueba",
                        "persona@tecnm.mx",
                        Rol.CONSUMIDOR.name(),
                        Instant.parse("2026-10-23T12:00:00Z")));
    }

    @Test
    void sesionCoincideConDominioYamlYNoTieneCamposAdicionales() throws Exception {
        comprobar("Sesion",
                InicioSesionService.ResultadoInicioSesion.class,
                new InicioSesionService.ResultadoInicioSesion(
                        "token-de-prueba",
                        Instant.parse("2026-10-23T12:15:00Z"),
                        Rol.CONSUMIDOR.name()));
    }

    @Test
    void enumRolDelDominioCoincideConOpenApi() {
        Map<String, Object> esquema = esquema("Rol");
        List<?> valoresOpenApi = lista(esquema.get("enum"), "Rol.enum");
        Set<String> esperados = Arrays.stream(Rol.values())
                .map(Enum::name)
                .collect(Collectors.toCollection(TreeSet::new));
        Set<String> declarados = valoresOpenApi.stream()
                .map(String::valueOf)
                .collect(Collectors.toCollection(TreeSet::new));

        assertEquals(esperados, declarados,
                "Rol.java y components.schemas.Rol deben declarar los mismos valores");
    }

    private static void comprobar(String nombreEsquema, Class<?> tipoRecord,
                                  Object ejemplo) throws Exception {
        Map<String, Object> esquema = esquema(nombreEsquema);
        Map<String, Object> propiedades = mapa(
                esquema.get("properties"), nombreEsquema + ".properties");

        assertTrue(tipoRecord.isRecord(),
                tipoRecord.getSimpleName() + " debe seguir siendo un record DTO");
        Set<String> componentesJava = Arrays.stream(tipoRecord.getRecordComponents())
                .map(RecordComponent::getName)
                .collect(Collectors.toCollection(TreeSet::new));
        Set<String> propiedadesOpenApi = new TreeSet<>(propiedades.keySet());

        assertEquals(propiedadesOpenApi, componentesJava,
                "Los campos de " + tipoRecord.getSimpleName()
                        + " deben coincidir exactamente con " + nombreEsquema);

        JsonNode json = JSON.valueToTree(ejemplo);
        comprobarJson(json, nombreEsquema);
    }

    private static void comprobarJson(JsonNode json, String nombreEsquema) {
        assertTrue(json.isObject(), nombreEsquema + " debe serializarse como objeto JSON");
        Map<String, Object> esquema = esquema(nombreEsquema);
        Map<String, Object> propiedades = mapa(
                esquema.get("properties"), nombreEsquema + ".properties");

        Set<String> camposJson = new TreeSet<>();
        camposJson.addAll(json.propertyNames());
        Set<String> camposOpenApi = new TreeSet<>(propiedades.keySet());
        assertEquals(camposOpenApi, camposJson,
                "El JSON de " + nombreEsquema
                        + " debe contener todos y solo los campos declarados en OpenAPI");

        Set<String> requeridos = new LinkedHashSet<>();
        Object listaRequeridos = esquema.get("required");
        if (listaRequeridos != null) {
            lista(listaRequeridos, nombreEsquema + ".required")
                    .forEach(valor -> requeridos.add(String.valueOf(valor)));
        }
        assertEquals(camposOpenApi, requeridos,
                nombreEsquema + " debe exigir todos los campos que declara");
        assertTrue(camposJson.containsAll(requeridos),
                nombreEsquema + " no contiene todos sus campos obligatorios: " + requeridos);

        for (String campo : camposJson) {
            comprobarValor(json.get(campo), campo,
                    mapa(propiedades.get(campo), nombreEsquema + "." + campo));
        }
    }

    private static void comprobarValor(JsonNode valor, String nombreCampo,
                                       Map<String, Object> definicion) {
        Map<String, Object> efectiva = definicion;
        Object referencia = definicion.get("$ref");
        if (referencia != null) {
            String ref = String.valueOf(referencia);
            String prefijo = "#/components/schemas/";
            assertTrue(ref.startsWith(prefijo),
                    "Referencia no soportada para " + nombreCampo + ": " + ref);
            efectiva = esquema(ref.substring(prefijo.length()));
        }

        Object tipo = efectiva.get("type");
        assertEquals("string", tipo,
                "Esta prueba de CU-08 espera un campo string en " + nombreCampo);
        if ("string".equals(tipo)) {
            assertTrue(valor.isTextual(), nombreCampo + " debe ser una cadena");
            String texto = valor.asText();

            Object longitudMinima = efectiva.get("minLength");
            if (longitudMinima instanceof Number minimo) {
                assertTrue(texto.length() >= minimo.intValue(),
                        nombreCampo + " no alcanza minLength=" + minimo);
            }

            Object patron = efectiva.get("pattern");
            if (patron != null) {
                assertTrue(Pattern.matches(String.valueOf(patron), texto),
                        nombreCampo + " no cumple pattern=" + patron);
            }

            Object formato = efectiva.get("format");
            if ("email".equals(formato)) {
                assertTrue(texto.matches("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"),
                        nombreCampo + " no tiene formato de correo");
            } else if ("date-time".equals(formato)) {
                try {
                    OffsetDateTime.parse(texto);
                } catch (RuntimeException ex) {
                    throw new AssertionError(nombreCampo
                            + " debe tener formato date-time ISO-8601", ex);
                }
            }
        }

        Object enumeracion = efectiva.get("enum");
        if (enumeracion != null) {
            List<?> valores = lista(enumeracion, nombreCampo + ".enum");
            assertTrue(valores.contains(valor.asText()),
                    nombreCampo + " debe ser uno de " + valores);
        }
    }

    private static Map<String, Object> esquema(String nombre) {
        Object valor = esquemas.get(nombre);
        assertTrue(valor != null, "No existe components.schemas." + nombre);
        return mapa(valor, "components.schemas." + nombre);
    }

    private static Map<String, Object> mapa(Object valor, String contexto) {
        assertInstanceOf(Map.class, valor, contexto + " debe ser un mapa YAML");
        Map<?, ?> origen = (Map<?, ?>) valor;
        Map<String, Object> resultado = new LinkedHashMap<>();
        origen.forEach((clave, elemento) -> resultado.put(String.valueOf(clave), elemento));
        return resultado;
    }

    private static List<?> lista(Object valor, String contexto) {
        assertInstanceOf(List.class, valor, contexto + " debe ser una lista YAML");
        return (List<?>) valor;
    }
}
