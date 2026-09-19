package mx.tecnm.canastamx.domain_service.domain.canasta;

import java.text.Normalizer;
import java.util.Locale;

/**
 * Identidad de un artículo: producto + presentación (ADR 002).
 * La marca NO va aquí — va en el registro de precio.
 *
 * Se guarda YA normalizado, con la misma regla que declara
 * contracts/qqp-v1.yaml -> normalizacion.canonica.
 */
public record ReferenciaDeArticulo(String producto, String presentacion) {
  //La marca NO va aquí: ADR 002. Va en el registro de precio
    public ReferenciaDeArticulo {
        producto = canonica(exigir(producto, "producto"));
        presentacion = canonica(exigir(presentacion, "presentacion"));
    }

    private static String exigir(String v, String campo) {
        if (v == null || v.isBlank()) {
            throw new IllegalArgumentException(campo + " no puede ir vacío");
        }

        return v;
    }

    /**
     * Equivale a:
     * trim(regexp_replace(regexp_replace(
     * lower(strip_accents(col)), '[^a-z0-9 ]', ' ', 'g'),
     * '\\s+', ' ', 'g'))
     */
    static String canonica(String s) {
        return Normalizer.normalize(s, Normalizer.Form.NFD)
                .replaceAll("\\p{M}+", "")
                .toLowerCase(Locale.ROOT)
                .replaceAll("[^a-z0-9 ]", " ")
                .replaceAll("\\s+", " ")
                .trim();
    }
}