import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss()],

  // Accessible uniquement depuis cet ordinateur (localhost).
  server: {
    host: "localhost",
    port: 5173,
  },
})
