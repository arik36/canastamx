package mx.tecnm.canastamx.domain_service.application.service;

import java.util.List;
import java.util.UUID;
import java.util.function.Consumer;

import mx.tecnm.canastamx.domain_service.domain.canasta.*;
import mx.tecnm.canastamx.domain_service.infrastructure.persistence.CanastaRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class CanastaService {
    private final CanastaRepository repositorio;

    public CanastaService(CanastaRepository repositorio) {
        this.repositorio = repositorio;
    }

    public Canasta crear(String usuarioId, String nombre) {
        return repositorio.crear(new Canasta(UUID.randomUUID().toString(), usuarioId, nombre));
    }

    @Transactional(readOnly = true, isolation = org.springframework.transaction.annotation.Isolation.REPEATABLE_READ)
    public Pagina listar(String usuarioId, int limit, int offset) {
        if (limit < 1 || limit > 100 || offset < 0) {
            throw new IllegalArgumentException("Paginación inválida");
        }
        return new Pagina(repositorio.listar(usuarioId, limit, offset), repositorio.contar(usuarioId));
    }

    @Transactional(readOnly = true)
    public Canasta obtener(String id, String usuarioId) {
        return repositorio.buscarPorIdYUsuario(id, usuarioId).orElseThrow(NoExisteException::new);
    }

    public Canasta modificar(String id, String usuarioId, Consumer<Canasta> cambio) {
        repositorio.bloquear(id, usuarioId);
        Canasta canasta = obtener(id, usuarioId);
        cambio.accept(canasta);
        repositorio.guardar(canasta);
        return canasta;
    }

    public void borrar(String id, String usuarioId) {
        if (!repositorio.borrar(id, usuarioId)) {
            throw new NoExisteException();
        }
    }

    public record Pagina(List<Canasta> canastas, long total) {}
    public static class NoExisteException extends RuntimeException {}
}
