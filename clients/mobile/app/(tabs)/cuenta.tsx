import { AccesoAlertas } from "../../components/AccesoAlertas";
import { PantallaVacia } from "../../components/PantallaVacia";

export default function Cuenta() {
  return (
    <PantallaVacia title="Cuenta" showTitle={false} withHeader>
      <AccesoAlertas />
    </PantallaVacia>
  );
}
