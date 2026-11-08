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
    @Test
    void fijar_cantidad_reemplaza_y_no_agrega_articulos_inexistentes() {
        var c = new Canasta("c1", "u1", "Despensa");
        c.agregar(leche, new Cantidad(3));
        c.fijarCantidad(leche, new Cantidad(2));
        assertEquals(1, c.lineas().size());
        assertEquals(2, c.lineas().get(0).cantidad().unidades());
        var arroz = new ReferenciaDeArticulo("Arroz", "1 kg");
        assertThrows(Canasta.ArticuloNoExisteException.class,
                () -> c.fijarCantidad(arroz, new Cantidad(4)));
        assertEquals(1, c.lineas().size());
        assertEquals(2, c.lineas().get(0).cantidad().unidades());
    }

    @Test
    void quitar_articulo_inexistente_no_modifica_la_canasta() {
        var c = new Canasta("c1", "u1", "Despensa");
        c.agregar(leche, new Cantidad(3));
        assertThrows(Canasta.ArticuloNoExisteException.class,
                () -> c.quitar(new ReferenciaDeArticulo("Arroz", "1 kg")));
        assertEquals(1, c.lineas().size());
        assertEquals(leche, c.lineas().get(0).articulo());
        assertEquals(3, c.lineas().get(0).cantidad().unidades());
    }

    @Test
    void referencia_rechaza_texto_que_queda_vacio_al_normalizar() {
        assertThrows(IllegalArgumentException.class,
                () -> new ReferenciaDeArticulo("...", "1 L"));
        assertThrows(IllegalArgumentException.class,
                () -> new ReferenciaDeArticulo("Leche", "!!!"));
    }

    @Test
    void agregar_rechaza_cantidad_nula_con_y_sin_linea_previa() {
        var c = new Canasta("c1", "u1", "Despensa");
        assertThrows(IllegalArgumentException.class, () -> c.agregar(leche, null));
        assertTrue(c.lineas().isEmpty());
        c.agregar(leche, new Cantidad(3));
        assertThrows(IllegalArgumentException.class, () -> c.agregar(leche, null));
        assertEquals(1, c.lineas().size());
        assertEquals(3, c.lineas().get(0).cantidad().unidades());
    }

    @Test
    void suma_no_desborda_la_cantidad_ni_modifica_la_linea() {
        var c = new Canasta("c1", "u1", "Despensa");
        c.agregar(leche, new Cantidad(Integer.MAX_VALUE));
        assertThrows(ArithmeticException.class, () -> c.agregar(leche, new Cantidad(1)));
        assertEquals(Integer.MAX_VALUE, c.lineas().get(0).cantidad().unidades());
    }
}
