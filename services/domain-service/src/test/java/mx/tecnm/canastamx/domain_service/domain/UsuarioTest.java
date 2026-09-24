package mx.tecnm.canastamx.domain_service.domain.usuario;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

class UsuarioTest {

    private static final String HASH =
            "$2a$10$abcdefghijklmnopqrstuv";

    @Test
    void el_correo_se_guarda_normalizado() {
        assertEquals(
                "liseth@tecnm.mx",
                new CorreoElectronico("  Liseth@Tecnm.MX ").valor());
    }

    @Test
    void no_acepta_correos_con_formato_invalido() {
        assertThrows(
                IllegalArgumentException.class,
                () -> new CorreoElectronico("no-es-correo"));
    }

    @Test
    void no_acepta_contrasena_en_texto_plano() {
        var u = new Usuario(
                "u1",
                new CorreoElectronico("liseth@tecnm.mx"),
                HASH,
                "Liseth",
                null);

        assertThrows(
                IllegalArgumentException.class,
                () -> u.cambiarContrasena("hola123"));
    }
}