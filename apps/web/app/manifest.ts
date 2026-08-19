import type { MetadataRoute } from "next";

/**
 * PWA manifest (docs section 34). Installable, own STACKUP identity.
 * Icons are generated at /icon and /apple-icon by app/icon.tsx.
 */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "STACKUP",
    short_name: "STACKUP",
    description: "Sabé cuánto te cuesta realmente tu software.",
    start_url: "/",
    display: "standalone",
    background_color: "#0b0c10",
    theme_color: "#0b0c10",
    icons: [
      {
        src: "/icon",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
    ],
  };
}
