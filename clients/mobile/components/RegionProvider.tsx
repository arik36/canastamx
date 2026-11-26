import { createContext, ReactNode, useContext, useState } from "react";
import { FlatList, Pressable, StyleSheet, Text } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { PanelInferior } from "./PanelInferior";
import { BotonAcceso } from "./ControlesAcceso";
import { colors, fonts } from "../theme/design-system";

const Context = createContext<{ entidad: string; quincena: string; setQuincena(v: string): void; elegir(): void }>({ entidad: "Guanajuato", quincena: "", setQuincena() {}, elegir() {} });
const entidades = [
  "Aguascalientes", "Baja California", "Baja California Sur", "Campeche",
  "Chiapas", "Chihuahua", "Ciudad de México", "Coahuila", "Colima", "Durango",
  "Estado de México", "Guanajuato", "Guerrero", "Hidalgo", "Jalisco", "Michoacán",
  "Morelos", "Nayarit", "Nuevo León", "Oaxaca", "Puebla", "Querétaro",
  "Quintana Roo", "San Luis Potosí", "Sinaloa", "Sonora", "Tabasco", "Tamaulipas",
  "Tlaxcala", "Veracruz", "Yucatán", "Zacatecas",
];
export const useRegion = () => useContext(Context);
export function RegionProvider({ children }: { children: ReactNode }) {
  const [entidad, setEntidad] = useState("Guanajuato");
  const [quincena, setQuincena] = useState("");
  const [abierto, setAbierto] = useState(false);
  function seleccionar(nombre: string) {
    if (nombre !== entidad) setQuincena("");
    setEntidad(nombre);
    setAbierto(false);
  }
  return <Context.Provider value={{ entidad, quincena, setQuincena, elegir() { setAbierto(true); } }}>
    {children}
    <PanelInferior visible={abierto} titulo="¿Dónde vas a comprar?" cerrar={() => setAbierto(false)} alto desplazable={false}>
          <Text style={s.texto}>Selecciona tu estado. Si todavía no hay cobertura, te lo indicaremos.</Text>
          <Text style={s.actual}>Estado actual: {entidad}</Text>
          <FlatList style={s.lista} data={entidades} keyExtractor={nombre => nombre}
            extraData={entidad} accessibilityLabel="Entidades federativas"
            renderItem={({ item }) => <Pressable accessibilityRole="radio"
              accessibilityLabel={item} accessibilityState={{ checked: item === entidad }}
              onPress={() => seleccionar(item)} style={({ pressed }) => [s.opcion, item === entidad && s.seleccionada, pressed && s.pulsada]}>
              <Text style={[s.nombre, item === entidad && s.nombreSeleccionado]}>{item}</Text>
              <Ionicons name={item === entidad ? "radio-button-on" : "radio-button-off"} size={22} color={item === entidad ? colors.button : colors.muted} />
            </Pressable>} />
          <BotonAcceso titulo="Cancelar" secundario onPress={() => setAbierto(false)} />
    </PanelInferior>
  </Context.Provider>;
}
const s = StyleSheet.create({
  texto: { fontFamily: fonts.regular, color: colors.muted, lineHeight: 22 },
  actual: { fontFamily: fonts.semibold, color: colors.button }, lista: { flex: 1 },
  opcion: { minHeight: 52, paddingVertical: 14, paddingHorizontal: 12, flexDirection: "row", alignItems: "center", gap: 12, borderBottomWidth: 1, borderBottomColor: colors.border },
  seleccionada: { backgroundColor: colors.background, borderRadius: 12 }, pulsada: { opacity: 0.6 },
  nombre: { flex: 1, fontFamily: fonts.regular, fontSize: 16, color: colors.text },
  nombreSeleccionado: { fontFamily: fonts.semibold, color: colors.button },
});
