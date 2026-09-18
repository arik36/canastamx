package mx.tecnm.canastamx.domain_service.domain.usuario;

public class Usuario {

    private final String id;
    private final String correoElectronico;
    private final String contrasenaCifrada;

    public Usuario(String id, String correoElectronico, String contrasenaCifrada) {
        this.id = id;
        this.correoElectronico = correoElectronico;
        this.contrasenaCifrada = contrasenaCifrada;
    }
}
