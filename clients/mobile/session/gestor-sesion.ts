import { Cuenta, ErrorDeAcceso, Sesion } from "../api/sesion";

export type EstadoSesion = { estado: "cargando" | "invitado" | "conSesion" | "error"; cuenta?: Cuenta; mensaje?: string };
type Dependencias = {
  leerToken(): Promise<string | null>;
  guardarToken(token: string): Promise<void>;
  borrarToken(): Promise<void>;
  iniciar(correo: string, contrasena: string): Promise<Sesion>;
  consultar(token: string): Promise<Cuenta>;
};

// El correo sólo vive en memoria. Toda restauración obtiene la cuenta de /yo (D-10).
export class GestorSesion {
  private version = 0;
  private token: string | null = null;
  private vencimiento?: number;
  private escritura: Promise<void> = Promise.resolve();
  constructor(private deps: Dependencias, private publicar: (estado: EstadoSesion) => void) {}

  private persistir(operacion: () => Promise<void>) {
    const pendiente = this.escritura.then(operacion);
    this.escritura = pendiente.catch(() => {});
    return pendiente;
  }

  private validarRol(cuenta: Cuenta) {
    if (cuenta.rol !== "CONSUMIDOR") throw new ErrorDeAcceso("Esta cuenta es de analista u operador. Accede desde la plataforma web o explora sin cuenta.");
  }

  async restaurar() {
    const version = ++this.version;
    this.publicar({ estado: "cargando" });
    try {
      const token = this.token ?? await this.deps.leerToken();
      if (version !== this.version) return;
      if (!token) { this.publicar({ estado: "invitado" }); return; }
      if (this.vencimiento && Date.now() >= this.vencimiento) throw new ErrorDeAcceso("Tu sesión venció. Vuelve a iniciar sesión.", 401);
      const cuenta = await this.deps.consultar(token);
      if (version !== this.version) return;
      this.validarRol(cuenta);
      this.token = token;
      this.publicar({ estado: "conSesion", cuenta });
    } catch (error) {
      if (version !== this.version) return;
      if (error instanceof ErrorDeAcceso && error.status === 401) {
        try { await this.persistir(() => this.deps.borrarToken()); } catch { this.publicar({ estado: "error", mensaje: "No pudimos borrar la sesión vencida. Intenta de nuevo." }); return; }
        this.token = null;
        this.publicar({ estado: "invitado", mensaje: error.message });
      } else this.publicar({ estado: "error", mensaje: error instanceof Error ? error.message : "No pudimos recuperar tu sesión." });
    }
  }

  async entrar(correo: string, contrasena: string) {
    const version = ++this.version;
    this.publicar({ estado: "cargando" });
    try {
      const sesion = await this.deps.iniciar(correo, contrasena);
      if (version !== this.version) return false;
      const cuenta = await this.deps.consultar(sesion.token);
      if (version !== this.version) return false;
      this.validarRol(cuenta);
      if (cuenta.rol !== sesion.rol) throw new ErrorDeAcceso("El rol de la sesión no coincide con el de la cuenta.");
      await this.persistir(() => this.deps.guardarToken(sesion.token));
      if (version !== this.version) return false;
      this.token = sesion.token;
      this.vencimiento = Date.parse(sesion.expiraEn);
      this.publicar({ estado: "conSesion", cuenta });
      return true;
    } catch (error) {
      if (version === this.version) this.publicar({ estado: "invitado", mensaje: error instanceof Error ? error.message : "No pudimos iniciar sesión." });
      return false;
    }
  }

  async salir() {
    ++this.version;
    this.publicar({ estado: "cargando" });
    try {
      await this.persistir(() => this.deps.borrarToken());
      this.token = null;
      this.vencimiento = undefined;
      this.publicar({ estado: "invitado" });
      return true;
    } catch {
      this.publicar({ estado: "error", mensaje: "No pudimos borrar la sesión del teléfono. Vuelve a intentar." });
      return false;
    }
  }
  cancelar() { ++this.version; }
}
