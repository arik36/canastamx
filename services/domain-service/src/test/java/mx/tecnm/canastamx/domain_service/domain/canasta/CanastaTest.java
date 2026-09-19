package mx.tecnm.canastamx.domain_service.domain.canasta;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

class CanastaTest {

    private final ReferenciaDeArticulo leche =
            new ReferenciaDeArticulo("Leche Ultrapasteurizada", "1 L");

    @Test
    void dos_escrituras_del_mismo_articulo_son_el_mismo_articulo() {
        var otra = new ReferenciaDeArticulo(
                "LECHE ULTRAPASTEURIZADA", "1 l.");

        assertEquals(leche, otra);
        assertEquals(leche.hashCode(), otra.hashCode());
    }

    @Test
    void agregar_dos_veces_el_mismo_articulo_suma_cantidades() {
        var c = new Canasta("c1", "u1", "Despensa");

        c.agregar(leche, new Cantidad(2));
        c.agregar(
                new ReferenciaDeArticulo(
                        "LECHE ULTRAPASTEURIZADA", "1 l."),
                new Cantidad(3));

        assertEquals(1, c.lineas().size());
        assertEquals(5, c.lineas().get(0).cantidad().unidades());
    }

    @Test
    void desde_afuera_no_se_modifican_las_lineas() {
        var c = new Canasta("c1", "u1", "Despensa");

        c.agregar(leche, new Cantidad(1));

        assertThrows(
                UnsupportedOperationException.class,
                () -> c.lineas().clear());
    }

    @Test
    void la_cantidad_tiene_que_ser_mayor_que_cero() {
        assertThrows(
                IllegalArgumentException.class,
                () -> new Cantidad(0));
    }
}
