
-- Esquema versionado de la tabla usuario.
-- Referencia: docs/analisis/modelo-er.md

CREATE TABLE IF NOT EXISTS usuario (
    id VARCHAR(36) PRIMARY KEY,
    correo_electronico VARCHAR(255) NOT NULL UNIQUE,
    contrasena_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL DEFAULT 'CONSUMIDOR',
    fecha_de_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_usuario_rol
        CHECK (rol IN ('CONSUMIDOR', 'ANALISTA', 'OPERADOR'))
);
