package mx.tecnm.canastamx.domain_service.infrastructure.web;

import java.util.List;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import mx.tecnm.canastamx.domain_service.application.service.CanastaService;
import mx.tecnm.canastamx.domain_service.domain.canasta.*;
import mx.tecnm.canastamx.domain_service.domain.usuario.Usuario;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/canastas")
public class CanastaController {
    private final CanastaService servicio;

    public CanastaController(CanastaService servicio) {
        this.servicio = servicio;
    }

    @GetMapping
    public PaginaRespuesta listar(@CuentaDeLaSesion Usuario cuenta,
            @RequestParam(defaultValue = "20") int limit,
            @RequestParam(defaultValue = "0") int offset) {
        var pagina = servicio.listar(cuenta.id(), limit, offset);
        return new PaginaRespuesta(pagina.canastas().stream().map(CanastaRespuesta::de).toList(),
                pagina.total());
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public CanastaRespuesta crear(@CuentaDeLaSesion Usuario cuenta,
            @Valid @RequestBody NombreSolicitud solicitud) {
        return CanastaRespuesta.de(servicio.crear(cuenta.id(), solicitud.nombre()));
    }

    @GetMapping("/{canastaId}")
    public CanastaRespuesta obtener(@CuentaDeLaSesion Usuario cuenta, @PathVariable String canastaId) {
        return CanastaRespuesta.de(servicio.obtener(canastaId, cuenta.id()));
    }

    @PatchMapping("/{canastaId}")
    public CanastaRespuesta renombrar(@CuentaDeLaSesion Usuario cuenta, @PathVariable String canastaId,
            @Valid @RequestBody NombreSolicitud solicitud) {
        return CanastaRespuesta.de(servicio.modificar(canastaId, cuenta.id(),
                c -> c.renombrar(solicitud.nombre())));
    }

    @DeleteMapping("/{canastaId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void borrar(@CuentaDeLaSesion Usuario cuenta, @PathVariable String canastaId) {
        servicio.borrar(canastaId, cuenta.id());
    }

    @PostMapping("/{canastaId}/lineas")
    public CanastaRespuesta agregar(@CuentaDeLaSesion Usuario cuenta, @PathVariable String canastaId,
            @Valid @RequestBody LineaSolicitud solicitud) {
        return CanastaRespuesta.de(servicio.modificar(canastaId, cuenta.id(),
                c -> c.agregar(solicitud.articulo().referencia(), new Cantidad(solicitud.cantidad().intValueExact()))));
    }

    @PutMapping("/{canastaId}/lineas")
    public CanastaRespuesta fijar(@CuentaDeLaSesion Usuario cuenta, @PathVariable String canastaId,
            @Valid @RequestBody LineaSolicitud solicitud) {
        return CanastaRespuesta.de(servicio.modificar(canastaId, cuenta.id(),
                c -> c.fijarCantidad(solicitud.articulo().referencia(), new Cantidad(solicitud.cantidad().intValueExact()))));
    }

    @DeleteMapping("/{canastaId}/lineas")
    public CanastaRespuesta quitar(@CuentaDeLaSesion Usuario cuenta, @PathVariable String canastaId,
            @RequestParam String producto, @RequestParam String presentacion) {
        return CanastaRespuesta.de(servicio.modificar(canastaId, cuenta.id(),
                c -> c.quitar(new ReferenciaDeArticulo(producto, presentacion))));
    }

    public record NombreSolicitud(@NotBlank String nombre) {}
    public record ArticuloSolicitud(@NotBlank String producto, @NotBlank String presentacion) {
        ReferenciaDeArticulo referencia() {
            return new ReferenciaDeArticulo(producto, presentacion);
        }
    }
    public record LineaSolicitud(@NotNull @Valid ArticuloSolicitud articulo,
                                @NotNull @Positive java.math.BigDecimal cantidad) {}
    public record LineaRespuesta(ReferenciaDeArticulo articulo, int cantidad) {}
    public record CanastaRespuesta(String id, String nombre, List<LineaRespuesta> lineas) {
        static CanastaRespuesta de(Canasta canasta) {
            return new CanastaRespuesta(canasta.id(), canasta.nombre(), canasta.lineas().stream()
                    .map(l -> new LineaRespuesta(l.articulo(), l.cantidad().unidades())).toList());
        }
    }
    public record PaginaRespuesta(List<CanastaRespuesta> canastas, long total) {}
}
