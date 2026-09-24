export const todayISO = () => new Date().toLocaleDateString("en-CA");
export const formatDate = (value, options = {}) => value ? new Intl.DateTimeFormat("fr-FR", { day: "2-digit", month: "short", year: "numeric", ...options }).format(new Date(`${value}T12:00:00`)) : "—";
export const formatTime = (value) => value ? value.slice(0, 5).replace(":", "h") : "—";
export const statusLabel = (status) => ({ CONFIRMEE: "Confirmée", ANNULEE: "Annulée", EN_ATTENTE: "En attente" }[status] || status || "Confirmée");
export const statusClass = (status) => status === "ANNULEE" ? "border border-slate-200 bg-slate-100 text-slate-500" : status === "EN_ATTENTE" ? "border border-slate-300 bg-white text-slate-700" : "bg-slate-900 text-white";
