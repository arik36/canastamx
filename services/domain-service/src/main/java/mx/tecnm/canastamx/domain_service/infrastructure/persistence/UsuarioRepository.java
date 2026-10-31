
package mx.tecnm.canastamx.domain_service.infrastructure.persistence;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.Optional;

import mx.tecnm.canastamx.domain_service.domain.usuario.CorreoElectronico;
import mx.tecnm.canastamx.domain_service.domain.usuario.Rol;
import mx.tecnm.canastamx.domain_service.domain.usuario.Usuario;

import org.springframework.dao.DuplicateKeyException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class UsuarioRepository {

    private final JdbcTemplate jdbcTemplate;

    public UsuarioRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public Usuario guardar(Usuario usuario) {
        String sql = """
                INSERT INTO usuario
                    (id, correo_electronico, contrasena_hash, rol, fecha_de_registro)
                VALUES (?, ?, ?, ?, ?)
                """;

        jdbcTemplate.update(
                sql,
                usuario.id(),
                usuario.correo().valor(),
                usuario.contrasenaCifrada(),
                usuario.rol().name(),
                Timestamp.from(usuario.fechaDeRegistro())
        );

        return usuario;
    }

    public Optional<Usuario> buscarPorCorreo(CorreoElectronico correo) {
        String sql = """
                SELECT id, correo_electronico, contrasena_hash,
                       rol, fecha_de_registro
                FROM usuario
                WHERE correo_electronico = ?
                """;

        return jdbcTemplate.query(
                sql,
                (rs, rowNum) -> mapearUsuario(rs),
                correo.valor()
        ).stream().findFirst();
    }

    public Optional<Usuario> buscarPorId(String id) {
        String sql = """
                SELECT id, correo_electronico, contrasena_hash,
                       rol, fecha_de_registro
                FROM usuario
                WHERE id = ?
                """;

        return jdbcTemplate.query(
                sql,
                (rs, rowNum) -> mapearUsuario(rs),
                id
        ).stream().findFirst();
    }

    private Usuario mapearUsuario(ResultSet rs) throws SQLException {
        Timestamp fecha = rs.getTimestamp("fecha_de_registro");
        Instant fechaRegistro = fecha.toInstant();

        return new Usuario(
                rs.getString("id"),
                new CorreoElectronico(rs.getString("correo_electronico")),
                rs.getString("contrasena_hash"),
                Rol.valueOf(rs.getString("rol")),
                fechaRegistro
        );
    }
}
