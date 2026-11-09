import { redirect } from "next/navigation";

// La raíz no es una vista. El proxy ya manda al acceso sin sesión, y a la vista del
// rol con ella (lib/rutas.mjs); esto cubre el caso en que el proxy no corra.
export default function Inicio() {
  redirect("/acceso");
}
