import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

export default function DashboardInsights() {
  const [stats, setStats] = useState(null);
  useEffect(() => { apiFetch("/dashboard/stats/").then(setStats).catch(() => {}); }, []);
  if (!stats) return null;
  const max = Math.max(1, ...stats.by_room.map((room) => room.total));
  return <section className="mb-7 grid gap-5 lg:grid-cols-[1fr_1.2fr]"><div className="card p-5"><h2 className="font-black">Occupation par salle</h2><p className="mb-5 text-xs text-slate-500">Réservations enregistrées</p><div className="space-y-4">{stats.by_room.map((room) => <div key={room.id_salle}><div className="mb-1 flex justify-between text-xs"><b>{room.id_salle__nom_salle}</b><span>{room.total}</span></div><div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-black" style={{ width: `${(room.total / max) * 100}%` }} /></div></div>)}</div></div><div className="card p-5"><h2 className="font-black">Activité RH récente</h2><p className="mb-4 text-xs text-slate-500">Créations, modifications et annulations</p><div className="space-y-3">{stats.recent_activity.slice(0, 5).map((item) => <div key={item.id_reservation} className="flex justify-between gap-4 border-b border-slate-100 pb-3"><div className="min-w-0"><p className="truncate text-sm font-bold">{item.objet}</p><p className="text-xs text-slate-500">Créée par {item.created_by_name || "profil historique"}</p></div><span className="shrink-0 text-xs font-semibold">{item.statut}</span></div>)}</div></div></section>;
}
