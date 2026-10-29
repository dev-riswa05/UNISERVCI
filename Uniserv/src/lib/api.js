// En développement, sans VITE_API_URL, l'API utilise le même ordinateur que le
// frontend (port 8000). En production, VITE_API_URL est obligatoire.
export function resolveApiUrl() {
  const configured = import.meta.env.VITE_API_URL;
  if (configured) return configured.replace(/\/$/, "");
  if (import.meta.env.DEV) return `${window.location.protocol}//${window.location.hostname}:8000/api`;
  throw new Error("Configuration manquante : VITE_API_URL n'est pas définie.");
}

function messageFrom(data, fallback, status = 0) {
  if (status >= 500) return "Le serveur a rencontré une erreur. Réessayez dans un instant.";
  if (!data) return fallback;
  if (typeof data === "string") return data;
  if (Array.isArray(data)) return data.join(" ");
  if (data.erreur || data.error || data.detail || data.message) return data.erreur || data.error || data.detail || data.message;
  return Object.values(data).flat().filter(Boolean).join(" ") || fallback;
}

export async function apiFetch(path, options = {}) {
  // Toutes les pages utilisent ce point d'entrée afin de ne jamais oublier
  // l'en-tête Token et de traiter l'expiration de session au même endroit.
  // `public: true` : endpoint sans authentification (écran d'affichage).
  const { public: isPublic = false, ...fetchOptions } = options;
  const token = isPublic ? null : sessionStorage.getItem("token");
  const headers = { Accept: "application/json", ...fetchOptions.headers };
  if (fetchOptions.body && !(fetchOptions.body instanceof FormData)) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Token ${token}`;
  let response;
  try {
    response = await fetch(`${resolveApiUrl()}${path}`, { ...fetchOptions, headers });
  } catch {
    throw new Error("Impossible de joindre le serveur. Réessayez dans un instant.");
  }
  const text = await response.text();
  const data = (() => { try { return text ? JSON.parse(text) : null; } catch { return text; } })();
  if (response.status === 401 && token) {
    // Un token refusé ne doit pas rester dans le navigateur : sinon chaque
    // nouvelle page bouclerait sur une requête 401.
    sessionStorage.removeItem("token");
    sessionStorage.removeItem("role");
    sessionStorage.removeItem("username");
    sessionStorage.removeItem("profil_rh");
    sessionStorage.removeItem("user");
    if (window.location.pathname !== "/") window.location.assign("/");
    throw new Error("Votre session a expiré. Veuillez vous reconnecter.");
  }
  if (!response.ok) throw new Error(messageFrom(data, "Une erreur est survenue.", response.status));
  return data;
}

