package mx.tecnm.canastamx.domain_service.infrastructure.persistence;

import java.util.Optional;

import mx.tecnm.canastamx.domain_service.domain.canasta.Canasta;
import mx.tecnm.canastamx.domain_service.domain.canasta.Cantidad;
import mx.tecnm.canastamx.domain_service.domain.canasta.LineaDeCanasta;
import mx.tecnm.canastamx.domain_service.domain.canasta.ReferenciaDeArticulo;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

@Repository
public class CanastaRepository {

    private final JdbcTemplate jdbcTemplate;

    public CanastaRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Transactional
    public Canasta crear(Canasta canasta) {
        jdbcTemplate.update("""
                INSERT INTO canasta (id, usuario_id, nombre)
                VALUES (?, ?, ?)
                """,
                canasta.id(),
                canasta.usuarioId(),
                canasta.nombre());

        for (LineaDeCanasta linea : canasta.lineas()) {
            jdbcTemplate.update("""
                    INSERT INTO linea_canasta
                        (canasta_id, producto, presentacion, cantidad)
                    VALUES (?, ?, ?, ?)
                    """,
                    canasta.id(),
                    linea.articulo().producto(),
                    linea.articulo().presentacion(),
                    linea.cantidad().unidades());
        }

        return canasta;
    }

    @Transactional(readOnly = true)
    public Optional<Canasta> buscarPorIdYUsuario(
            String canastaId, String usuarioId) {

        Optional<Canasta> encontrada = jdbcTemplate.query("""
                SELECT id, usuario_id, nombre
                FROM canasta
                WHERE id = ? AND usuario_id = ?
                """,
                (rs, rowNum) -> new Canasta(
                        rs.getString("id"),
                        rs.getString("usuario_id"),
                        rs.getString("nombre")),
                canastaId,
                usuarioId
        ).stream().findFirst();

        if (encontrada.isEmpty()) {
            return Optional.empty();
        }

        Canasta canasta = encontrada.get();

        var lineas = jdbcTemplate.query("""
                SELECT producto, presentacion, cantidad
                FROM linea_canasta
                WHERE canasta_id = ?
                ORDER BY producto, presentacion
                """,
                (rs, rowNum) -> new LineaDeCanasta(
                        new ReferenciaDeArticulo(
                                rs.getString("producto"),
                                rs.getString("presentacion")),
                        new Cantidad(rs.getInt("cantidad"))),
                canasta.id());

        for (LineaDeCanasta linea : lineas) {
            canasta.agregar(linea.articulo(), linea.cantidad());
        }

        return Optional.of(canasta);
    }

    /** Serializa los cambios de una misma canasta para no perder sumas concurrentes. */
    public void bloquear(String id, String usuarioId) {
        jdbcTemplate.query("SELECT id FROM canasta WHERE id = ? AND usuario_id = ? FOR UPDATE",
                (rs, n) -> rs.getString("id"), id, usuarioId);
    }

    public java.util.List<Canasta> listar(String usuarioId, int limit, int offset) {
        return jdbcTemplate.query("""
                SELECT id FROM canasta WHERE usuario_id = ? ORDER BY id LIMIT ? OFFSET ?
                """, (rs, n) -> rs.getString("id"), usuarioId, limit, offset).stream()
                .map(id -> buscarPorIdYUsuario(id, usuarioId).orElseThrow()).toList();
    }

    public long contar(String usuarioId) {
        return jdbcTemplate.queryForObject("SELECT count(*) FROM canasta WHERE usuario_id = ?",
                Long.class, usuarioId);
    }

    public void guardar(Canasta canasta) {
        jdbcTemplate.update("UPDATE canasta SET nombre = ? WHERE id = ? AND usuario_id = ?",
                canasta.nombre(), canasta.id(), canasta.usuarioId());
        jdbcTemplate.update("DELETE FROM linea_canasta WHERE canasta_id = ?", canasta.id());
        for (LineaDeCanasta linea : canasta.lineas()) {
            jdbcTemplate.update("""
                    INSERT INTO linea_canasta (canasta_id, producto, presentacion, cantidad)
                    VALUES (?, ?, ?, ?)
                    """, canasta.id(), linea.articulo().producto(),
                    linea.articulo().presentacion(), linea.cantidad().unidades());
        }
    }

    public boolean borrar(String id, String usuarioId) {
        return jdbcTemplate.update("DELETE FROM canasta WHERE id = ? AND usuario_id = ?",
                id, usuarioId) == 1;
    }
}
