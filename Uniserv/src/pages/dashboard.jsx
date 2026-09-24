import { useEffect, useState } from "react";
import { ArrowRight, CalendarCheck, CalendarDays, Clock3, DoorOpen, Plus, Users } from "lucide-react";
import { Link } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import { Alert, Loading } from "../components/Feedback";
import { apiFetch } from "../lib/api";
import { formatDate, formatTime, todayISO } from "../lib/format";
import DashboardInsights from "../components/DashboardInsights";

export default function Dashboard() {
  const [data, setData] = useState({ reservations: [], rooms: [] });
  const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  useEffect(() => { Promise.all([apiFetch("/reservations/"), apiFetch("/salles/")]).then(([reservations, rooms]) => setData({ reservations, rooms })).catch((e) => setError(e.message)).finally(() => setLoading(false)); }, []);
  const today = todayISO();
  const currentTime = new Date().toTimeString().slice(0, 5);
  const active = data.reservations.filter((r) => r.statut !== "ANNULEE");
  const todays = active.filter((r) => r.date_reservation === today).sort((a, b) => a.heure_debut.localeCompare(b.heure_debut));
  const upcoming = active.filter((r) => r.date_reservation > today || (r.date_reservation === today && r.heure_fin.slice(0, 5) >= currentTime)).sort((a, b) => `${a.date_reservation}${a.heure_debut}`.localeCompare(`${b.date_reservation}${b.heure_debut}`));
  const cards = [["Réunions aujourd’hui", todays.length, CalendarCheck], ["À venir", upcoming.length, CalendarDays], ["Salles actives", data.rooms.filter((r) => r.active).length, DoorOpen], ["Participants aujourd’hui", todays.reduce((n, r) => n + (r.nombre_participants || 0), 0), Users]];
  return <><PageHeader title="Tableau de bord" description={`Vue d’ensemble · ${formatDate(today, { weekday: "long" })}`}><Link className="btn-primary" to="/reservations/nouvelle"><Plus size={18} /> Nouvelle réservation</Link></PageHeader>{error && <Alert>{error}</Alert>}{loading ? <Loading /> : <>
    <section className="mb-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{cards.map(([label, value, Icon]) => <div key={label} className="card flex items-center gap-4 p-5"><span className="grid h-12 w-12 place-items-center rounded-xl bg-black text-white"><Icon size={22} strokeWidth={1.8} /></span><div><p className="text-2xl font-black text-slate-900">{value}</p><p className="text-xs font-medium text-slate-500">{label}</p></div></div>)}</section>
    <DashboardInsights />
    <section className="grid gap-6 xl:grid-cols-[1.5fr_1fr]"><div className="card overflow-hidden"><div className="flex items-center justify-between border-b border-slate-100 p-5"><div><h2 className="font-bold text-slate-900">Planning du jour</h2><p className="text-xs text-slate-500">{todays.length ? `${todays.length} réunion${todays.length > 1 ? "s" : ""} programmée${todays.length > 1 ? "s" : ""}` : "Aucune réunion programmée"}</p></div><Link to="/planning" className="flex items-center gap-1 text-sm font-bold text-black">Voir le planning <ArrowRight size={16} /></Link></div><div className="divide-y divide-slate-100">{todays.length ? todays.slice(0, 6).map((r) => <div key={r.id_reservation} className="flex gap-4 p-5"><div className="w-20 shrink-0 text-sm font-black text-slate-800">{formatTime(r.heure_debut)}</div><span className="w-1 rounded-full bg-black" /><div className="min-w-0 flex-1"><p className="truncate font-bold text-slate-800">{r.objet}</p><p className="mt-1 truncate text-xs text-slate-500">{r.salle_nom} · {r.nom_demandeur}</p></div><p className="hidden items-center gap-1 text-xs text-slate-500 sm:flex"><Clock3 size={14} />{formatTime(r.heure_fin)}</p></div>) : <p className="p-12 text-center text-sm text-slate-500">La journée est libre.</p>}</div></div>
    <div className="card p-5"><h2 className="font-bold text-slate-900">Prochaines réunions</h2><p className="mb-5 text-xs text-slate-500">Les prochains rendez-vous confirmés</p><div className="space-y-3">{upcoming.slice(0, 5).map((r) => <Link to={`/reservations/${r.id_reservation}`} key={r.id_reservation} className="block rounded-xl border border-slate-100 p-3.5 transition hover:border-slate-400 hover:bg-slate-50"><div className="flex justify-between gap-3"><p className="truncate text-sm font-bold text-slate-800">{r.objet}</p><span className="shrink-0 text-xs font-bold text-black">{formatTime(r.heure_debut)}</span></div><p className="mt-1 text-xs text-slate-500">{formatDate(r.date_reservation)} · {r.salle_nom}</p></Link>)}{!upcoming.length && <p className="py-10 text-center text-sm text-slate-500">Aucune réunion à venir.</p>}</div></div></section>
  </>}</>;
}
