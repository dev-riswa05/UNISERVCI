import { apiFetch } from "./api";

// Déconnexion unique : invalide le token côté serveur (sans bloquer en cas
// d'échec) puis vide la session locale.
export async function logout() {
  try {
    await Promise.race([
      apiFetch("/logout/", { method: "POST" }),
      new Promise((resolve) => setTimeout(resolve, 3000)),
    ]);
  } catch { /* Le nettoyage local reste prioritaire. */ }
  sessionStorage.clear();
}

// Page d'accueil de chaque rôle une fois connecté.
export function homeForRole(role) {
  return role === "MANAGER" ? "/planning" : "/dashboard";
}
