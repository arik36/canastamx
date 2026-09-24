package mx.tecnm.canastamx.domain_service.domain.usuario;

import java.time.Instant;

public class Usuario {

    private final String id;
    private final CorreoElectronico correo;
    private final Instant fechaDeRegistro;
    private String contrasenaCifrada;
    private String nombre;

    public Usuario(String id, CorreoElectronico correo, String contrasenaCifrada,
                   String nombre, Instant fechaDeRegistro) {

        if (id == null || id.isBlank()) {
            throw new IllegalArgumentException("el usuario necesita id");
        }

        if (correo == null) {
            throw new IllegalArgumentException("el usuario necesita correo");
        }

        this.id = id;
        this.correo = correo;
        this.fechaDeRegistro =
                fechaDeRegistro == null ? Instant.now() : fechaDeRegistro;

        cambiarContrasena(contrasenaCifrada);
        renombrar(nombre);
    }

    public final void cambiarContrasena(String yaCifrada) {
        if (yaCifrada == null || yaCifrada.isBlank()) {
            throw new IllegalArgumentException(
                    "la contraseña cifrada no puede ir vacía");
        }

        if (!yaCifrada.startsWith("$2")) {
            throw new IllegalArgumentException(
                    "esto no parece un hash BCrypt: ¿te llegó en texto plano?");
        }

        this.contrasenaCifrada = yaCifrada;
    }

    public final void renombrar(String nuevo) {
        if (nuevo == null || nuevo.isBlank()) {
            throw new IllegalArgumentException(
                    "el nombre no puede ir vacío");
        }

        this.nombre = nuevo.trim();
    }

    public String id() {
        return id;
    }

    public CorreoElectronico correo() {
        return correo;
    }

    public String nombre() {
        return nombre;
    }

    public Instant fechaDeRegistro() {
        return fechaDeRegistro;
    }

    public String contrasenaCifrada() {
        return contrasenaCifrada;
    }
}