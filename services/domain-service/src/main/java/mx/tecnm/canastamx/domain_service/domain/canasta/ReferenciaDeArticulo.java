package mx.tecnm.canastamx.domain_service.domain.canasta;

import java.text.Normalizer;
import java.util.Locale;

/**
 * Identidad de un artículo: producto y presentación (ADR 002).
 * La marca pertenece al registro de precio. Se normalizan ambos campos según
 * {@code contracts/qqp-v1.yaml}, regla {@code normalizacion.canonica}, antes de
 * comprobar que no estén vacíos.
 */
public record ReferenciaDeArticulo(String producto, String presentacion) {
    public ReferenciaDeArticulo {
        producto = exigir(canonica(producto), "producto");
        presentacion = exigir(canonica(presentacion), "presentacion");
    }

    private static String exigir(String valor, String campo) {
        if (valor.isBlank()) {
            throw new IllegalArgumentException(campo + " no puede ir vacío");
        }
        return valor;
    }

    /** Quita acentos y signos, convierte a minúsculas y compacta los espacios. */
    static String canonica(String texto) {
        if (texto == null) {
            return "";
        }
        return Normalizer.normalize(texto, Normalizer.Form.NFD)
                .replaceAll("\\p{M}+", "")
                .toLowerCase(Locale.ROOT)
                .replaceAll("[^a-z0-9 ]", " ")
                .replaceAll("\\s+", " ")
                .trim();
    }
}
