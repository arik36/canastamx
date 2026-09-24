package mx.tecnm.canastamx.domain_service.domain.usuario;

import java.util.Locale;
import java.util.regex.Pattern;

public record CorreoElectronico(String valor) {

    private static final Pattern FORMATO =
            Pattern.compile("^[^@\\s]+@[^@\\s]+\\.[^@\\s]{2,}$");

    public CorreoElectronico {
        if (valor == null || valor.isBlank()) {
            throw new IllegalArgumentException("el correo no puede ir vacío");
        }

        valor = valor.trim().toLowerCase(Locale.ROOT);

        if (!FORMATO.matcher(valor).matches()) {
            throw new IllegalArgumentException("correo inválido: " + valor);
        }
    }
}
