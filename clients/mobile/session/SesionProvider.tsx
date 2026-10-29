import { createContext, ReactNode, useContext, useEffect, useRef, useState } from "react";
import { AppState } from "react-native";
import * as SecureStore from "expo-secure-store";
import { consultarMiCuenta, iniciarSesion } from "../api/sesion";
import { EstadoSesion, GestorSesion } from "./gestor-sesion";

const CLAVE = "canastamx.sesion.token";
type Contexto = EstadoSesion & { entrar(correo: string, contrasena: string): Promise<boolean>; salir(): Promise<boolean>; reintentar(): Promise<void> };
const SesionContext = createContext<Contexto | null>(null);

export function SesionProvider({ children }: { children: ReactNode }) {
  const [estado, setEstado] = useState<EstadoSesion>({ estado: "cargando" });
  const gestor = useRef<GestorSesion | null>(null);
  if (!gestor.current) gestor.current = new GestorSesion({
    leerToken: () => SecureStore.getItemAsync(CLAVE),
    guardarToken: token => SecureStore.setItemAsync(CLAVE, token),
    borrarToken: () => SecureStore.deleteItemAsync(CLAVE),
    iniciar: iniciarSesion, consultar: consultarMiCuenta,
  }, setEstado);
  const sesion = gestor.current;
  useEffect(() => {
    void sesion.restaurar();
    const subscription = AppState.addEventListener("change", state => { if (state === "active") void sesion.restaurar(); });
    return () => { subscription.remove(); sesion.cancelar(); };
  }, [sesion]);
  return <SesionContext.Provider value={{ ...estado, entrar: (correo, contrasena) => sesion.entrar(correo, contrasena), salir: () => sesion.salir(), reintentar: () => sesion.restaurar() }}>{children}</SesionContext.Provider>;
}
export function useSesion() {
  const sesion = useContext(SesionContext);
  if (!sesion) throw new Error("Falta SesionProvider.");
  return sesion;
}
