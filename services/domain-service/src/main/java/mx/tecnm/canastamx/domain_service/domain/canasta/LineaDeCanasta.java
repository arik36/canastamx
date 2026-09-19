package mx.tecnm.canastamx.domain_service.domain.canasta;

public record LineaDeCanasta(ReferenciaDeArticulo articulo, Cantidad cantidad) {

    public LineaDeCanasta {
        if (articulo == null) {
            throw new IllegalArgumentException("la línea necesita artículo");
        }

        if (cantidad == null) {
            throw new IllegalArgumentException("la línea necesita cantidad");
        }
    }

    LineaDeCanasta sumar(Cantidad extra) {
        return new LineaDeCanasta(articulo, cantidad.mas(extra));
    }
}