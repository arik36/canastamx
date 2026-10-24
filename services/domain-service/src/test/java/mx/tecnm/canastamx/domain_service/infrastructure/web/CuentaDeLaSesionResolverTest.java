package mx.tecnm.canastamx.domain_service.infrastructure.web;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.LinkedHashMap;
import java.util.Map;

import org.junit.jupiter.api.Test;

/** Cómo se lee {@code Authorization}, sin Spring. */
class CuentaDeLaSesionResolverTest {

    @Test
    void sacaElTokenSoloDelEsquemaBearer() {
        Map<String, String> casos = new LinkedHashMap<>();
        casos.put("Bearer abc.def.ghi", "abc.def.ghi");
        casos.put("bearer abc.def.ghi", "abc.def.ghi");      // el esquema no distingue mayúsculas
        casos.put("BEARER   abc.def.ghi  ", "abc.def.ghi");
        casos.put("Bearer ", "");                             // un Bearer vacío es «sin token»
        casos.put("Bearer", null);
        casos.put("Token abc.def.ghi", null);
        casos.put("Basic dXN1YXJpbw==", null);
        casos.put("abc.def.ghi", null);
        casos.put(null, null);

        casos.forEach((autorizacion, token) -> assertEquals(token,
                CuentaDeLaSesionResolver.tokenBearer(autorizacion), String.valueOf(autorizacion)));
    }
}
