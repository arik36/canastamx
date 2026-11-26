import { createContext, ReactNode, useCallback, useContext, useEffect, useRef, useState } from "react";
import * as api from "../api/canastas";
import { ErrorServicio } from "../api/solicitud";
import { ErrorDeAcceso } from "../api/sesion";
import { useSesion } from "../session/SesionProvider";

type Contexto = {
  canastas: api.Canasta[]; actual?: api.Canasta; ocupada: boolean; error: string; listaCargada: boolean; requiereRecarga: boolean;
  seleccionar(id: string): void; recargar(): Promise<boolean>;
  crear(nombre: string): Promise<boolean>;
  renombrar(nombre: string): Promise<boolean>; borrar(): Promise<boolean>;
  agregar(articulo: api.Articulo, cantidad: number): Promise<boolean>;
  agregarEn(id: string, articulo: api.Articulo, cantidad: number): Promise<boolean>;
  fijar(linea: api.Linea): Promise<boolean>; quitar(articulo: api.Articulo): Promise<boolean>;
};
const Context = createContext<Contexto | null>(null);

export function CanastaProvider({ children }: { children: ReactNode }) {
  const sesion = useSesion();
  const cuenta = sesion.estado === "conSesion" ? sesion.cuenta?.id : undefined;
  const [canastas, setCanastas] = useState<api.Canasta[]>([]);
  const [id, setId] = useState<string>();
  const [ocupada, setOcupada] = useState(false);
  const [error, setError] = useState("");
  const [listaCargada, setListaCargada] = useState(false);
  const [duenoDatos, setDuenoDatos] = useState<string>();
  const [requiereRecarga, setRequiereRecarga] = useState(false);
  const recargaNecesaria = useRef(false);
  const peticion = useRef<{ version: number; controller?: AbortController; ocupada: boolean }>({ version: 0, ocupada: false });
  // El propietario cambia durante el render: una respuesta anterior nunca publica datos de otra cuenta.
  const propietario = useRef(cuenta);
  if (propietario.current !== cuenta) { propietario.current = cuenta; peticion.current.version++; peticion.current.controller?.abort(); peticion.current.ocupada = false; }
  const token = sesion.tokenDeSesion;
  const restaurar = useRef(sesion.reintentar);
  restaurar.current = sesion.reintentar;

  const ejecutar = useCallback(async (accion: (token: string, signal: AbortSignal) => Promise<api.Canasta[] | api.Canasta>, esLista = false) => {
    if (!cuenta || peticion.current.ocupada || (!esLista && recargaNecesaria.current)) return false;
    const version = ++peticion.current.version;
    const controller = new AbortController();
    peticion.current.controller?.abort();
    peticion.current.controller = controller; peticion.current.ocupada = true;
    setOcupada(true); setError("");
    try {
      const resultado = await accion(token(), controller.signal);
      if (version !== peticion.current.version || controller.signal.aborted) return false;
      setDuenoDatos(cuenta);
      if (Array.isArray(resultado)) {
        recargaNecesaria.current = false; setRequiereRecarga(false);
        setCanastas(resultado); setListaCargada(true);
        setId(prev => resultado.some(c => c.id === prev) ? prev : resultado[0]?.id);
      } else {
        setCanastas(prev => prev.some(c => c.id === resultado.id) ? prev.map(c => c.id === resultado.id ? resultado : c) : [...prev, resultado]);
        setId(resultado.id);
      }
      return true;
    } catch (e) {
      if (version !== peticion.current.version || controller.signal.aborted) return false;
      if ((e instanceof ErrorServicio || e instanceof ErrorDeAcceso) && e.status === 401) {
        setCanastas([]); setId(undefined); setListaCargada(false);
        void restaurar.current();
      }
      const incierto = !esLista && (!(e instanceof ErrorServicio) || e.status === undefined || e.status >= 500);
      if (incierto) { recargaNecesaria.current = true; setRequiereRecarga(true); }
      setError((e instanceof Error ? e.message : "No pudimos consultar la canasta.")
        + (incierto ? " Actualiza la canasta antes de volver a enviar el cambio; puede haberse guardado." : ""));
      return false;
    } finally {
      if (version === peticion.current.version) { peticion.current.ocupada = false; setOcupada(false); }
    }
  }, [cuenta, token]);
  const recargar = useCallback(() => ejecutar((t, s) => api.listarCanastas(t, s), true), [ejecutar]);
  useEffect(() => {
    setCanastas([]); setId(undefined); setError(""); setListaCargada(false); setOcupada(false);
    recargaNecesaria.current = false; setRequiereRecarga(false);
    if (cuenta) void recargar();
    return () => { peticion.current.version++; peticion.current.controller?.abort(); peticion.current.ocupada = false; };
  }, [cuenta, recargar]);
  const visibles = cuenta && duenoDatos === cuenta ? canastas : [];
  const actual = visibles.find(c => c.id === id);
  const modificar = (accion: (t: string, id: string, s: AbortSignal) => Promise<api.Canasta>) => actual
    ? ejecutar((t, s) => accion(t, actual.id, s)) : Promise.resolve(false);
  return <Context.Provider value={{ canastas: visibles, actual, ocupada, error, listaCargada, requiereRecarga,
    seleccionar: id => { if (!peticion.current.ocupada) { setId(id); setError(""); } }, recargar,
    crear: nombre => ejecutar((t, s) => api.crearCanasta(t, nombre, s)),
    renombrar: nombre => modificar((t, id, s) => api.renombrarCanasta(t, id, nombre, s)),
    borrar: () => actual ? ejecutar(async (t, s) => {
      await api.borrarCanasta(t, actual.id, s);
      return visibles.filter(c => c.id !== actual.id);
    }) : Promise.resolve(false),
    agregar: (articulo, cantidad) => modificar((t, id, s) => api.guardarLinea(t, id, { articulo, cantidad }, false, s)),
    agregarEn: (id, articulo, cantidad) => visibles.some(c => c.id === id)
      ? ejecutar((t, s) => api.guardarLinea(t, id, { articulo, cantidad }, false, s)) : Promise.resolve(false),
    fijar: linea => modificar((t, id, s) => api.guardarLinea(t, id, linea, true, s)),
    quitar: articulo => modificar((t, id, s) => api.quitarArticulo(t, id, articulo, s)),
  }}>{children}</Context.Provider>;
}
export function useCanasta() {
  const value = useContext(Context);
  if (!value) throw new Error("Falta CanastaProvider.");
  return value;
}
