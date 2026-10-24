package mx.tecnm.canastamx.domain_service.application.service;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.security.SecureRandom;
import java.time.Instant;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

import mx.tecnm.canastamx.domain_service.domain.usuario.CorreoElectronico;
import mx.tecnm.canastamx.domain_service.domain.usuario.Rol;
import mx.tecnm.canastamx.domain_service.domain.usuario.Usuario;
import mx.tecnm.canastamx.domain_service.infrastructure.persistence.UsuarioRepository;
import mx.tecnm.canastamx.domain_service.infrastructure.security.JwtService;

import org.junit.jupiter.api.Test;

/**
 * La regla de la sesión sin Spring ni base: primero se verifica el token y sólo
 * después se busca la cuenta de su {@code sub}. Un token que no pasa la
 * verificación no llega al repositorio.
 */
class CuentaDeLaSesionServiceTest {

    private static final Usuario USUARIO = new Usuario(
            "u1",
            new CorreoElectronico("prueba@canastamx.mx"),
            "$2a$10$abcdefghijklmnopqrstuv",
            Rol.CONSUMIDOR,
            Instant.parse("2026-10-23T12:00:00Z"));

    // Clave aleatoria creada en cada corrida: el repositorio no guarda ninguna.
    private final JwtService jwt = new JwtService(claveDePrueba(), 15);

    @Test
    void unTokenValidoDeUnaCuentaQueExisteDevuelveEsaCuenta() {
        CuentaDeLaSesionService servicio =
                new CuentaDeLaSesionService(new Repositorio(USUARIO), jwt);

        assertSame(USUARIO, servicio.obtener(jwt.generarToken(USUARIO).token()));
    }

    @Test
    void unTokenValidoDeUnaCuentaQueYaNoExisteNoEsSesion() {
        Repositorio sinCuentas = new Repositorio();
        CuentaDeLaSesionService servicio = new CuentaDeLaSesionService(sinCuentas, jwt);

        CuentaDeLaSesionService.SinSesionException error = assertThrows(
                CuentaDeLaSesionService.SinSesionException.class,
                () -> servicio.obtener(jwt.generarToken(USUARIO).token()));

        assertTrue(error.llegoUnToken());
        assertTrue(sinCuentas.consultado, "con un token válido sí se busca la cuenta");
    }

    @Test
    void unTokenQueNoPasaLaVerificacionNoLlegaAlRepositorio() {
        Repositorio repositorio = new Repositorio(USUARIO);
        CuentaDeLaSesionService servicio = new CuentaDeLaSesionService(repositorio, jwt);
        String deOtraClave = new JwtService(claveDePrueba(), 15).generarToken(USUARIO).token();

        for (String token : new String[] {deOtraClave, "no-es-un-token"}) {
            CuentaDeLaSesionService.SinSesionException error = assertThrows(
                    CuentaDeLaSesionService.SinSesionException.class,
                    () -> servicio.obtener(token));
            assertTrue(error.llegoUnToken());
        }
        assertFalse(repositorio.consultado, "se buscó una cuenta con un sub sin verificar");
    }

    @Test
    void sinTokenNoHaySesionYAsiLoDice() {
        Repositorio repositorio = new Repositorio(USUARIO);
        CuentaDeLaSesionService servicio = new CuentaDeLaSesionService(repositorio, jwt);

        for (String token : new String[] {null, "", "   "}) {
            CuentaDeLaSesionService.SinSesionException error = assertThrows(
                    CuentaDeLaSesionService.SinSesionException.class,
                    () -> servicio.obtener(token));
            assertFalse(error.llegoUnToken());
        }
        assertFalse(repositorio.consultado);
    }

    /** Un repositorio sin base: conoce sólo las cuentas que se le dan y anota si lo usaron. */
    private static final class Repositorio extends UsuarioRepository {

        private final Map<String, Usuario> cuentas = new HashMap<>();
        private boolean consultado;

        Repositorio(Usuario... cuentas) {
            super(null);
            for (Usuario cuenta : cuentas) {
                this.cuentas.put(cuenta.id(), cuenta);
            }
        }

        @Override
        public Optional<Usuario> buscarPorId(String id) {
            consultado = true;
            return Optional.ofNullable(cuentas.get(id));
        }
    }

    private static String claveDePrueba() {
        byte[] bytes = new byte[32];
        new SecureRandom().nextBytes(bytes);
        return Base64.getEncoder().encodeToString(bytes);
    }
}
