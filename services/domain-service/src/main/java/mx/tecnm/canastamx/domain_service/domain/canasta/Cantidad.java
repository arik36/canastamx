package mx.tecnm.canastamx.domain_service.domain.canasta;

public record Cantidad(int unidades) {

    public Cantidad {
        if (unidades <= 0) {
            throw new IllegalArgumentException(
                    "la cantidad debe ser mayor que cero");
        }
    }

    public Cantidad mas(Cantidad otra) {
        return new Cantidad(unidades + otra.unidades);
    }
}
