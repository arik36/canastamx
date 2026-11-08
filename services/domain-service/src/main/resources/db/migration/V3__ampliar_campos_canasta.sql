-- El contrato no limita la longitud de nombre, producto ni presentación.
ALTER TABLE canasta ALTER COLUMN nombre TYPE TEXT;
ALTER TABLE linea_canasta ALTER COLUMN producto TYPE TEXT;
ALTER TABLE linea_canasta ALTER COLUMN presentacion TYPE TEXT;
CREATE INDEX idx_canasta_usuario_id ON canasta (usuario_id, id);
