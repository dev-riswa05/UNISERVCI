import { useCallback, useEffect, useMemo, useState } from "react";
import { CalendarDays, Clock3, DoorOpen, LogOut, Monitor, RefreshCw } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { apiFetch } from "../lib/api";
import { formatDate, formatTime } from "../lib/format";
import { countdownLabel, meetingCountdown, meetingStatus, roomSchedule } from "../lib/display";
import BrandLogo from "../components/BrandLogo";

const REFRESH_DELAY = 60_000;
const ABIDJAN_TIME_ZONE = "Africa/Abidjan";

// Force la date et l'heure ivoiriennes, quel que soit le fuseau de la tablette.
function abidjanDateTime(date) {
  const parts = new Intl.DateTimeFormat("fr-FR", {
    timeZone: ABIDJAN_TIME_ZONE,
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date).reduce((result, part) => ({ ...result, [part.type]: part.value }), {});
  return {
    date: `${parts.year}-${parts.month}-${parts.day}`,
    time: `${parts.hour}:${parts.minute}:${parts.second}`,
  };
}

export default function AffichageSalles() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const selectedRoomId = searchParams.get("salle") || "";
  const [now, setNow] = useState(new Date());
  const [data, setData] = useState({ salles: [], reservations: [] });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const abidjanNow = useMemo(() => abidjanDateTime(now), [now]);
  const date = abidjanNow.date;
  const currentTime = abidjanNow.time;

  const loadDisplay = useCallback(async (silent = false) => {
    if (silent) setRefreshing(true);
    else setLoading(true);
    setError("");
    const params = new URLSearchParams({ date });
    if (selectedRoomId) params.set("id_salle", selectedRoomId);
    try {
      const response = await apiFetch(`/affichage/?${params}`);
      setData(response);
    } catch {
      setError("Impossible de charger les réservations. Une nouvelle tentative sera faite automatiquement.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [date, selectedRoomId]);

  // L'heure évolue sans recharger la page ; les badges changent donc de statut
  // dès qu'une réunion commence ou se termine.
  useEffect(() => {
    const clock = window.setInterval(() => setNow(new Date()), 1_000);
    return () => window.clearInterval(clock);
  }, []);

  useEffect(() => {
    const initialLoad = window.setTimeout(() => loadDisplay(), 0);
    const refresh = window.setInterval(() => loadDisplay(true), REFRESH_DELAY);
    return () => {
      window.clearTimeout(initialLoad);
      window.clearInterval(refresh);
    };
  }, [loadDisplay]);

  const selectedRoom = data.salles.find((room) => String(room.id_salle) === selectedRoomId);
  const selectedSchedule = useMemo(
    () => selectedRoom ? roomSchedule(selectedRoom, data.reservations, currentTime) : null,
    [selectedRoom, data.reservations, currentTime]
  );

  const selectRoom = (event) => {
    const value = event.target.value;
    setSearchParams(value ? { salle: value } : {}, { replace: true });
  };

  const logout = () => {
    sessionStorage.removeItem("token");
    sessionStorage.removeItem("role");
    sessionStorage.removeItem("username");
    navigate("/login", { replace: true });
  };

  return (
    <main className="display-shell min-h-screen text-slate-950">
      <header className="display-header px-5 py-5 text-white sm:px-8 lg:px-12">
        <div className="mx-auto flex max-w-[1700px] flex-col justify-between gap-5 md:flex-row md:items-center">
          <div className="flex items-center gap-4">
            <BrandLogo light />
            <div className="border-l border-white/20 pl-4"><p className="text-sm font-bold uppercase tracking-[.2em] text-sky-100/70 sm:text-base">Salles de réunion</p><p className="text-xs text-sky-100/50">Disponibilités en temps réel</p></div>
          </div>
          <div className="flex items-end justify-between gap-7 md:justify-end">
            <div className="text-left md:text-right"><p className="flex items-center gap-2 text-sm text-slate-400 md:justify-end"><CalendarDays size={16} />{formatDate(date, { weekday: "long" })}</p><p className="mt-1 flex items-center gap-2 text-3xl font-black tabular-nums md:justify-end"><Clock3 size={24} />{currentTime}</p><p className="mt-1 text-xs font-semibold uppercase tracking-wider text-slate-500">Heure de Côte d’Ivoire</p></div>
            <button aria-label="Déconnecter la tablette" title="Déconnecter la tablette" onClick={logout} className="rounded-xl border border-white/20 p-3 text-slate-300 hover:bg-white/10 hover:text-white"><LogOut size={22} /></button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-[1700px] p-5 sm:p-8 lg:p-12">
        <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div><p className="mb-2 flex items-center gap-2 text-sm font-bold text-slate-500"><Monitor size={17} />Salle affichée</p><select aria-label="Choisir une salle" className="min-w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-lg font-bold shadow-sm outline-none focus:border-black sm:min-w-96" value={selectedRoomId} onChange={selectRoom}><option value="">Toutes les salles</option>{data.salles.map((room) => <option key={room.id_salle} value={room.id_salle}>{room.nom_salle}</option>)}</select></div>
          <button className="flex items-center gap-2 self-start rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-bold hover:bg-slate-100 sm:self-auto" onClick={() => loadDisplay(true)} disabled={refreshing}><RefreshCw size={17} className={refreshing ? "animate-spin" : ""} />{refreshing ? "Actualisation…" : "Actualiser"}</button>
        </div>

        {error && <div role="alert" className="mb-7 rounded-2xl border border-slate-300 bg-white p-5 text-base font-semibold text-slate-700">{error}</div>}
        {loading ? <DisplayLoading /> : selectedRoom && selectedSchedule ? (
          <SelectedRoom room={selectedRoom} schedule={selectedSchedule} currentTime={currentTime} />
        ) : selectedRoomId && !selectedRoom ? (
          <EmptyDisplay message="Cette salle n’existe pas ou n’est plus active." />
        ) : (
          <AllRooms rooms={data.salles} reservations={data.reservations} currentTime={currentTime} onSelect={(id) => setSearchParams({ salle: String(id) })} />
        )}
      </div>
    </main>
  );
}

function AllRooms({ rooms, reservations, currentTime, onSelect }) {
  if (!rooms.length) return <EmptyDisplay message="Aucune salle n’est disponible à l’affichage." />;
  return <section className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">{rooms.map((room) => { const schedule = roomSchedule(room, reservations, currentTime); return <RoomCard key={room.id_salle} room={room} schedule={schedule} onSelect={onSelect} />; })}</section>;
}

function RoomCard({ room, schedule, onSelect }) {
  const occupied = Boolean(schedule.current);
  return <button onClick={() => onSelect(room.id_salle)} className="overflow-hidden rounded-3xl border border-slate-200 bg-white text-left shadow-[0_15px_50px_rgba(15,23,42,.08)] transition hover:-translate-y-1 hover:shadow-xl"><div className={`flex items-center justify-between px-6 py-5 text-white ${occupied ? "bg-[#e13236]" : "bg-black"}`}><DoorOpen size={28} strokeWidth={1.7} /><span className="rounded-full border border-white/25 bg-white/10 px-4 py-1.5 text-sm font-black tracking-wider">{occupied ? "OCCUPÉE" : "LIBRE"}</span></div><div className="p-6"><h2 className="min-h-14 text-2xl font-black leading-tight">{room.nom_salle}</h2>{occupied ? <MeetingHighlight label="En cours" meeting={schedule.current} currentTime={schedule.currentTime} /> : <p className="mt-5 text-lg font-black tabular-nums">{countdownLabel(schedule)}</p>}<div className="mt-6 border-t border-slate-200 pt-5"><p className="text-sm font-bold uppercase tracking-wider text-slate-400">Prochaine réunion</p>{schedule.next ? <><p className="mt-2 text-xl font-black tabular-nums">{meetingCountdown(schedule.next, schedule.currentTime)}</p><p className="mt-1 text-xs text-slate-400">{formatTime(schedule.next.heure_debut)} – {formatTime(schedule.next.heure_fin)}</p><p className="mt-1 truncate text-base text-slate-600">{schedule.next.objet}</p></> : <p className="mt-2 text-base text-slate-500">Aucune autre réservation aujourd’hui</p>}</div></div></button>;
}

function SelectedRoom({ room, schedule, currentTime }) {
  const occupied = Boolean(schedule.current);
  return <div className="space-y-7"><section className={`rounded-3xl p-7 text-white shadow-xl sm:p-10 ${occupied ? "bg-[#e13236]" : "bg-black"}`}><div className="flex flex-col justify-between gap-6 md:flex-row md:items-center"><div><p className="mb-3 text-sm font-bold uppercase tracking-[.2em] text-white/70">Salle sélectionnée</p><h1 className="text-3xl font-black sm:text-5xl">{room.nom_salle}</h1></div><span className="w-fit rounded-full border border-white/25 bg-white/10 px-6 py-3 text-2xl font-black tracking-wider">{occupied ? "OCCUPÉE" : "LIBRE"}</span></div><p className="mt-7 text-3xl font-black tabular-nums">{countdownLabel(schedule)}</p>{occupied && <div className="mt-6 border-t border-white/20 pt-6"><p className="text-sm font-bold uppercase tracking-wider text-white/70">Réunion en cours</p><p className="mt-2 text-3xl font-black">{schedule.current.objet}</p><p className="mt-2 text-sm text-white/70">{formatTime(schedule.current.heure_debut)} – {formatTime(schedule.current.heure_fin)}</p></div>}</section><section className="grid gap-6 lg:grid-cols-[.8fr_1.2fr]"><div className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm"><p className="text-sm font-bold uppercase tracking-wider text-slate-400">Prochaine réunion</p>{schedule.next ? <><p className="mt-3 text-3xl font-black tabular-nums">{meetingCountdown(schedule.next, currentTime)}</p><p className="mt-2 text-sm text-slate-400">{formatTime(schedule.next.heure_debut)} – {formatTime(schedule.next.heure_fin)}</p><p className="mt-3 text-xl text-slate-600">{schedule.next.objet}</p></> : <p className="mt-5 text-xl text-slate-500">Aucune autre réservation aujourd’hui</p>}</div><TodayList meetings={schedule.meetings} currentTime={currentTime} /></section></div>;
}

function TodayList({ meetings, currentTime }) {
  return <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm"><div className="border-b border-slate-200 px-6 py-5"><h2 className="text-xl font-black">Réservations du jour</h2></div>{meetings.length ? <div className="divide-y divide-slate-100">{meetings.map((meeting) => { const status = meetingStatus(meeting, currentTime); return <div key={meeting.id_reservation} className="grid gap-3 px-6 py-5 sm:grid-cols-[220px_1fr_auto] sm:items-center"><div><p className="text-lg font-black tabular-nums">{meetingCountdown(meeting, currentTime)}</p><p className="text-xs text-slate-400">{formatTime(meeting.heure_debut)} – {formatTime(meeting.heure_fin)}</p></div><p className="text-lg font-semibold">{meeting.objet}</p><StatusBadge status={status} /></div>; })}</div> : <EmptyDisplay message="Aucune réservation aujourd’hui." compact />}</section>;
}

function StatusBadge({ status }) {
  const classes = status === "En cours" ? "bg-[#e13236] text-white" : status === "Terminée" ? "bg-slate-200 text-slate-500" : "bg-black text-white";
  return <span className={`w-fit rounded-full px-3 py-1.5 text-xs font-black uppercase tracking-wide ${classes}`}>{status}</span>;
}

function MeetingHighlight({ label, meeting, currentTime }) {
  return <div className="mt-5"><p className="text-sm font-bold uppercase tracking-wider text-slate-400">{label}</p><p className="mt-2 text-xl font-black tabular-nums">{meetingCountdown(meeting, currentTime)}</p><p className="mt-1 text-xs text-slate-400">{formatTime(meeting.heure_debut)} – {formatTime(meeting.heure_fin)}</p><p className="mt-1 truncate text-base text-slate-600">{meeting.objet}</p></div>;
}

function DisplayLoading() {
  return <div className="grid min-h-80 place-items-center rounded-3xl border border-slate-200 bg-white"><div className="text-center"><span className="spinner mx-auto mb-4 block" /><p className="text-lg font-bold text-slate-600">Chargement des salles…</p></div></div>;
}

function EmptyDisplay({ message, compact = false }) {
  return <div className={`grid place-items-center text-center text-slate-500 ${compact ? "min-h-40" : "min-h-80 rounded-3xl border border-slate-200 bg-white"}`}><div><DoorOpen className="mx-auto mb-3" size={32} strokeWidth={1.5} /><p className="text-lg font-semibold">{message}</p></div></div>;
}
