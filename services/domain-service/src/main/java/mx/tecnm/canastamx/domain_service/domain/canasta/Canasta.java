package mx.tecnm.canastamx.domain_service.domain.canasta;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class Canasta {

    private final String id;
    private final String usuarioId;
    private final List<LineaDeCanasta> lineas = new ArrayList<>();
    private String nombre;

    public Canasta(String id, String usuarioId, String nombre) {
        if (id == null || id.isBlank()) {
            throw new IllegalArgumentException("la canasta necesita id");
        }

        if (usuarioId == null || usuarioId.isBlank()) {
            throw new IllegalArgumentException("la canasta pertenece a un usuario");
        }

        this.id = id;
        this.usuarioId = usuarioId;
        renombrar(nombre);
    }

    public final void renombrar(String nuevo) {
        if (nuevo == null || nuevo.isBlank()) {
            throw new IllegalArgumentException("el nombre no puede ir vacío");
        }

        this.nombre = nuevo.trim();
    }

    public void agregar(ReferenciaDeArticulo articulo, Cantidad cantidad) {
        for (int i = 0; i < lineas.size(); i++) {
            if (lineas.get(i).articulo().equals(articulo)) {
                lineas.set(i, lineas.get(i).sumar(cantidad));
                return;
            }
        }

        lineas.add(new LineaDeCanasta(articulo, cantidad));
    }

    public void quitar(ReferenciaDeArticulo articulo) {
        lineas.removeIf(l -> l.articulo().equals(articulo));
    }

    public List<LineaDeCanasta> lineas() {
        return Collections.unmodifiableList(lineas);
    }

    public String id() {
        return id;
    }

    public String usuarioId() {
        return usuarioId;
    }

    public String nombre() {
        return nombre;
    }
}