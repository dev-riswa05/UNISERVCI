// Rôle courant lu dans la session. Les droits réels restent contrôlés par l'API.
export const getRole = () => sessionStorage.getItem("role");
export const isManager = () => getRole() === "MANAGER";
export const canManageAll = () => ["SUPER_ADMIN", "RH"].includes(getRole());
export const getSessionUser = () => { try { return JSON.parse(sessionStorage.getItem("user") || "null") || {}; } catch { return {}; } };
