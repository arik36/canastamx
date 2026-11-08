
CREATE TABLE canasta (
    id VARCHAR(36) PRIMARY KEY,
    usuario_id VARCHAR(36) NOT NULL,
    nombre VARCHAR(255) NOT NULL,

    CONSTRAINT fk_canasta_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuario(id),

    CONSTRAINT chk_canasta_nombre
        CHECK (LENGTH(TRIM(nombre)) > 0)
);

CREATE TABLE linea_canasta (
    canasta_id VARCHAR(36) NOT NULL,
    producto VARCHAR(255) NOT NULL,
    presentacion VARCHAR(255) NOT NULL,
    cantidad INTEGER NOT NULL,

    CONSTRAINT pk_linea_canasta
        PRIMARY KEY (canasta_id, producto, presentacion),

    CONSTRAINT fk_linea_canasta_canasta
        FOREIGN KEY (canasta_id)
        REFERENCES canasta(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_linea_canasta_cantidad
        CHECK (cantidad > 0),

    CONSTRAINT chk_linea_canasta_producto
        CHECK (LENGTH(TRIM(producto)) > 0),

    CONSTRAINT chk_linea_canasta_presentacion
        CHECK (LENGTH(TRIM(presentacion)) > 0)
);