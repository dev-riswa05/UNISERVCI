import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss()],

  // Écoute sur toutes les interfaces réseau de l'ordinateur.
  // Le site reste accessible en local et devient aussi accessible via l'IP Wi-Fi.
  server: {
    host: "0.0.0.0",
    port: 5173,
  },
})
