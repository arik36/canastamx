
package mx.tecnm.canastamx.domain_service.domain.usuario;

import static org.junit.jupiter.api.Assertions.*;

import java.lang.reflect.Field;

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
                Rol.CONSUMIDOR,
                null);

        assertThrows(
                IllegalArgumentException.class,
                () -> u.cambiarContrasena("hola123"));
    }

    @Test
    void el_usuario_tiene_rol() {
        var u = new Usuario(
                "u1",
                new CorreoElectronico("liseth@tecnm.mx"),
                HASH,
                Rol.CONSUMIDOR,
                null);

        assertEquals(Rol.CONSUMIDOR, u.rol());
    }

    @Test
    void el_usuario_no_tiene_atributo_nombre() {
        for (Field campo : Usuario.class.getDeclaredFields()) {
            assertNotEquals(
                    "nombre",
                    campo.getName(),
                    "Usuario no debe volver a tener el atributo nombre");
        }
    }
}
