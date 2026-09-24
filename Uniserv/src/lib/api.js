// Sans variable VITE_API_URL, l'API utilise le même ordinateur que le frontend.
// Exemple : si le site est ouvert sur 10.0.0.99:5173, Django sera contacté sur
// 10.0.0.99:8000. Cela fonctionne donc en local comme sur le réseau Wi-Fi.
const DEFAULT_API_URL = `${window.location.protocol}//${window.location.hostname}:8000/api`;
const API_URL = (import.meta.env.VITE_API_URL || DEFAULT_API_URL).replace(
  /\/$/,
  "",
);

function messageFrom(data, fallback) {
  if (!data) return fallback;
  if (typeof data === "string") return data;
  if (Array.isArray(data)) return data.join(" ");
  if (data.erreur || data.error || data.detail || data.message) return data.erreur || data.error || data.detail || data.message;
  return Object.values(data).flat().filter(Boolean).join(" ") || fallback;
}

export async function apiFetch(path, options = {}) {
  // Toutes les pages utilisent ce point d'entrée afin de ne jamais oublier
  // l'en-tête Token et de traiter l'expiration de session au même endroit.
  const token = sessionStorage.getItem("token");
  const headers = { Accept: "application/json", ...options.headers };
  if (options.body && !(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Token ${token}`;
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...options, headers });
  } catch {
    throw new Error("Le serveur est injoignable. Vérifiez que Django est démarré.");
  }
  const text = await response.text();
  const data = (() => { try { return text ? JSON.parse(text) : null; } catch { return text; } })();
  if (response.status === 401) {
    // Un token refusé ne doit pas rester dans le navigateur : sinon chaque
    // nouvelle page bouclerait sur une requête 401.
    sessionStorage.removeItem("token");
    sessionStorage.removeItem("role");
    sessionStorage.removeItem("username");
    sessionStorage.removeItem("profil_rh");
    sessionStorage.removeItem("user");
    if (window.location.pathname !== "/login") window.location.assign("/login");
    throw new Error("Votre session a expiré. Veuillez vous reconnecter.");
  }
  if (!response.ok) throw new Error(messageFrom(data, "Une erreur est survenue."));
  return data;
}

export { API_URL };
