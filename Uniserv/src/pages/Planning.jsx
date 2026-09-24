import { useEffect, useState } from "react";
import { CalendarDays, Filter } from "lucide-react";
import PageHeader from "../components/PageHeader";
import { Alert, Empty, Loading } from "../components/Feedback";
import { apiFetch } from "../lib/api";
import { formatDate, formatTime, todayISO } from "../lib/format";

export default function Planning() {
  const [date, setDate] = useState(todayISO()); const [room, setRoom] = useState("");
  const [rooms, setRooms] = useState([]); const [items, setItems] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  useEffect(() => { apiFetch("/salles/").then(setRooms).catch((e) => setError(e.message)); }, []);
  useEffect(() => { const params = new URLSearchParams(); if (date) params.set("date", date); if (room) params.set("id_salle", room); const timer = setTimeout(() => { setLoading(true); setError(""); apiFetch(`/planning/?${params}`).then(setItems).catch((e) => setError(e.message)).finally(() => setLoading(false)); }, 0); return () => clearTimeout(timer); }, [date, room]);
  const groups = items.reduce((acc, item) => ((acc[item.date_reservation] ||= []).push(item), acc), {});
  return <><PageHeader title="Planning des salles" description="Visualisez les réservations confirmées et les créneaux occupés." />{error && <Alert>{error}</Alert>}
    <div className="card mb-6 flex flex-col gap-4 p-4 sm:flex-row sm:items-end"><div className="flex-1"><label className="label" htmlFor="date"><CalendarDays size={15} className="mr-1 inline" />Date</label><input className="field" id="date" type="date" value={date} onChange={(e) => setDate(e.target.value)} /></div><div className="flex-1"><label className="label" htmlFor="room"><Filter size={15} className="mr-1 inline" />Salle</label><select className="field" id="room" value={room} onChange={(e) => setRoom(e.target.value)}><option value="">Toutes les salles</option>{rooms.map((r) => <option key={r.id_salle} value={r.id_salle}>{r.nom_salle}</option>)}</select></div><button className="btn-secondary" onClick={() => { setDate(todayISO()); setRoom(""); }}>Aujourd’hui</button></div>
    {loading ? <Loading /> : !items.length ? <div className="card"><Empty>Aucune réservation sur cette période.</Empty></div> : <div className="space-y-6">{Object.entries(groups).map(([day, reservations]) => <section key={day} className="card overflow-hidden"><div className="border-b border-slate-100 bg-slate-50/70 px-5 py-3"><h2 className="font-bold capitalize text-slate-800">{formatDate(day, { weekday: "long" })}</h2><p className="text-xs text-slate-500">{reservations.length} réservation{reservations.length > 1 ? "s" : ""}</p></div><div className="divide-y divide-slate-100">{reservations.map((r) => <div key={r.id_reservation} className="grid gap-3 p-5 sm:grid-cols-[130px_1fr_220px] sm:items-center"><div><p className="font-black text-slate-800">{formatTime(r.heure_debut)} – {formatTime(r.heure_fin)}</p></div><div className="border-l-4 border-black pl-4"><p className="font-bold text-slate-900">{r.objet}</p><p className="mt-1 text-xs text-slate-500">Demandé par {r.nom_demandeur} · {r.nombre_participants || 0} participant(s)</p></div><div className="rounded-lg bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">{r.salle_nom}</div></div>)}</div></section>)}</div>}
  </>;
}
