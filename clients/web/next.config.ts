import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // En `npm run dev`, Next dibuja su indicador abajo a la izquierda, encima del pie de
  // la barra lateral, y tapa el enlace «Salir». El indicador sólo existe en desarrollo.
  devIndicators: { position: "bottom-right" },
  async redirects() {
    return [
      {
        source: "/",
        destination: "/acceso",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;