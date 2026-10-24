package mx.tecnm.canastamx.domain_service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assumptions.assumeTrue;

import java.io.IOException;
import java.io.InputStream;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.Set;
import java.util.TreeSet;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.junit.jupiter.api.Test;

/**
 * Las pruebas toman su configuración del {@code .env} de la raíz
 * (application.properties), pero una variable del entorno le gana al archivo. Si
 * una quedó exportada en una terminal —o, en Windows, en las variables de
 * usuario— con otro valor, las pruebas correrían con otra base u otra clave sin
 * avisar. Aquí eso es una falla con nombre. Nunca se muestran valores.
 *
 * <p>Sin {@code .env} (la CI, que pasa todo por variables) no aplica.
 */
class ConfiguracionLocalTest {

    /** El mismo archivo que importa application.properties, desde services/domain-service. */
    private static final Path ENV = Path.of("..", "..", ".env");

    private static final Pattern MARCADOR = Pattern.compile("\\$\\{([A-Z][A-Z0-9_]*)");

    @Test
    void ningunaVariableDelEntornoTapaAlEnvConOtroValor() throws IOException {
        assumeTrue(Files.isRegularFile(ENV), "no hay .env en la raíz: no aplica");

        Properties archivo = new Properties();
        // Como lo lee Spring con [.properties]: ISO-8859-1.
        try (Reader lector = Files.newBufferedReader(ENV, StandardCharsets.ISO_8859_1)) {
            archivo.load(lector);
        }

        List<String> tapadas = variablesTapadas(
                archivo, System.getenv(), variablesQueLeeLaConfiguracion());

        assertEquals(List.of(), tapadas,
                "estas variables del entorno ganan sobre el .env con otro valor. Ciérralas"
                        + " (unset en Linux/WSL, Remove-Item Env: en PowerShell) o corre las"
                        + " pruebas sin heredar variables: services/domain-service/README.md");
    }

    @Test
    void soloCuentanLasDistintasYNuncaUnaVaciaDelArchivo() {
        Properties archivo = new Properties();
        archivo.setProperty("OLTP_DB", "canastamx_oltp");
        archivo.setProperty("OLTP_PORT", "5432");
        archivo.setProperty("JWT_SECRET", "");

        Map<String, String> entorno = Map.of(
                "OLTP_DB", "otra_base",
                "OLTP_PORT", "5432",
                "JWT_SECRET", "la-de-la-terminal");

        // JWT_SECRET vacía en el archivo: la del entorno es la única, no tapa nada.
        assertEquals(List.of("OLTP_DB"), variablesTapadas(archivo, entorno,
                List.of("JWT_SECRET", "OLTP_DB", "OLTP_PORT", "OLTP_USER")));
    }

    @Test
    void lasVariablesRevisadasSonLasDeApplicationProperties() throws IOException {
        assertTrue(variablesQueLeeLaConfiguracion().containsAll(List.of(
                "OLTP_DB", "OLTP_USER", "OLTP_PASSWORD", "OLTP_PORT",
                "JWT_SECRET", "JWT_EXPIRATION_MINUTES")));
    }

    static List<String> variablesTapadas(Properties archivo, Map<String, String> entorno,
                                         Collection<String> claves) {
        return claves.stream()
                .sorted()
                .filter(clave -> !archivo.getProperty(clave, "").isEmpty())
                .filter(clave -> entorno.containsKey(clave)
                        && !entorno.get(clave).equals(archivo.getProperty(clave)))
                .toList();
    }

    static Set<String> variablesQueLeeLaConfiguracion() throws IOException {
        try (InputStream propiedades =
                     ConfiguracionLocalTest.class.getResourceAsStream("/application.properties")) {
            String texto = new String(propiedades.readAllBytes(), StandardCharsets.ISO_8859_1);
            Set<String> claves = new TreeSet<>();
            Matcher marcador = MARCADOR.matcher(texto);
            while (marcador.find()) {
                claves.add(marcador.group(1));
            }
            return claves;
        }
    }
}
