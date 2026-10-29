import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CalendarDays, Clock3, DoorOpen, MapPin, RefreshCw } from "lucide-react";
import { apiFetch } from "../lib/api";
import { formatTime } from "../lib/format";
import { FERMETURE_MIN, OUVERTURE_MIN, countdownLabel, meetingCountdown, meetingStatus, roomSchedule, timeToMinutes } from "../lib/display";
import BrandLogo from "../components/BrandLogo";
import { homeForRole } from "../lib/session";

const REFRESH_DELAY = 60_000;
const ABIDJAN_TIME_ZONE = "Africa/Abidjan";

// Force la date et l'heure ivoiriennes, quel que soit le fuseau de l'écran.
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

// Page publique : aucune authentification, jamais de redirection vers la connexion.
export default function AffichageSalles() {
  const [now, setNow] = useState(new Date());
  const [data, setData] = useState({ salles: [], reservations: [] });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [lastRefresh, setLastRefresh] = useState(null);
  const abidjanNow = useMemo(() => abidjanDateTime(now), [now]);
  const date = abidjanNow.date;
  const currentTime = abidjanNow.time;
  const [hh, mm, ss] = currentTime.split(":");
  const dateLongue = new Intl.DateTimeFormat("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: ABIDJAN_TIME_ZONE }).format(now);
  const totalSalles = data.salles.length;
  const sallesLibres = data.salles.filter((room) => !roomSchedule(room, data.reservations, currentTime).current).length;

  const loadDisplay = useCallback(async (silent = false) => {
    if (silent) setRefreshing(true);
    else setLoading(true);
    try {
      // Endpoint public : aucun en-tête Authorization n'est envoyé.
      const response = await apiFetch(`/affichage/?${new URLSearchParams({ date })}`, { public: true });
      setData(response);
      setError("");
      setLastRefresh(new Date());
    } catch {
      setError("Impossible de charger les réservations. Une nouvelle tentative sera faite automatiquement.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [date]);

  // L'heure évolue sans recharger la page ; les badges changent donc de statut
  // dès qu'une réunion commence ou se termine.
  useEffect(() => {
    const clock = window.setInterval(() => setNow(new Date()), 1_000);
    return () => window.clearInterval(clock);
  }, []);

  const loadRef = useRef(loadDisplay);
  useEffect(() => { loadRef.current = loadDisplay; }, [loadDisplay]);

  // Rechargement immédiat quand la date change.
  useEffect(() => {
    const initialLoad = window.setTimeout(() => loadDisplay(), 0);
    return () => window.clearTimeout(initialLoad);
  }, [loadDisplay]);

  // L'intervalle de rafraîchissement n'est créé qu'une seule fois.
  useEffect(() => {
    const refresh = window.setInterval(() => loadRef.current(true), REFRESH_DELAY);
    return () => window.clearInterval(refresh);
  }, []);

  return (
    <main className="display-shell min-h-screen overflow-x-clip text-slate-950">
      <header className="display-header px-4 py-5 text-white sm:px-8 lg:px-12">
        <div className="mx-auto flex max-w-[1900px] flex-col justify-between gap-5 md:flex-row md:items-center">
          <div className="flex min-w-0 items-center gap-4">
            <BrandLogo light to={sessionStorage.getItem("token") ? homeForRole(sessionStorage.getItem("role")) : "/"} nameClassName="text-xl sm:text-2xl 2xl:text-4xl" />
            <div className="min-w-0 border-l-2 border-white/30 pl-4 sm:pl-6">
              <p role="heading" aria-level={1} className="text-lg font-black uppercase leading-tight tracking-[.12em] text-white sm:text-3xl 2xl:text-5xl">Salles de réunion</p>
              <p className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs font-semibold text-sky-100 sm:text-base 2xl:text-2xl">
                <span className="inline-flex items-center gap-2"><span className="live-dot" aria-hidden="true" />En direct</span>
                {totalSalles > 0 && <span className="text-sky-100/75">{sallesLibres} salle{sallesLibres > 1 ? "s" : ""} libre{sallesLibres > 1 ? "s" : ""} sur {totalSalles}</span>}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4 rounded-2xl border border-white/15 bg-white/[.06] px-4 py-3 sm:px-6 2xl:gap-6 2xl:px-9 2xl:py-5">
            <span className="grid h-12 w-12 shrink-0 place-items-center rounded-full bg-white/10 2xl:h-16 2xl:w-16"><Clock3 className="size-6 2xl:size-8" strokeWidth={1.8} /></span>
            <div className="text-left md:text-right">
              <p className="flex items-center gap-2 text-sm font-semibold capitalize text-sky-100 md:justify-end 2xl:text-2xl"><CalendarDays size={17} />{dateLongue}</p>
              <p className="mt-1 flex items-baseline gap-1 text-4xl font-black leading-none tabular-nums sm:text-5xl md:justify-end 2xl:text-7xl" aria-label={`Il est ${hh} heures ${mm}`}>{hh}<span className="opacity-60">:</span>{mm}<span className="ml-1.5 text-xl font-bold text-(--uniserv-sky) sm:text-2xl 2xl:text-4xl">{ss}</span></p>
              <p className="mt-1.5 text-[11px] font-semibold uppercase tracking-[.16em] text-sky-100/70 2xl:text-base">Heure d’Abidjan<span className="hidden xl:inline"> · Côte d’Ivoire</span></p>
            </div>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-[1900px] p-4 sm:p-8 lg:p-12">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          {sharedPlace(data.salles) ? <p className="flex min-w-0 items-start gap-2 text-sm text-slate-500 2xl:text-lg"><MapPin size={18} className="mt-0.5 shrink-0" />{sharedPlace(data.salles)}</p> : <span />}
          <button className="flex min-h-11 items-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-bold hover:bg-slate-100" onClick={() => loadDisplay(true)} disabled={refreshing}><RefreshCw size={17} className={refreshing ? "animate-spin" : ""} />{refreshing ? "Actualisation…" : "Actualiser"}</button>
        </div>

        {error && <div role="alert" className="mb-7 rounded-2xl border border-slate-300 bg-white p-5 text-base font-semibold text-slate-700">{error}{lastRefresh && ` Dernière actualisation réussie à ${abidjanDateTime(lastRefresh).time.slice(0, 5).replace(":", "h")}.`}</div>}
        {loading ? <DisplayLoading /> : <AllRooms rooms={data.salles} reservations={data.reservations} currentTime={currentTime} />}
      </div>
    </main>
  );
}

// Adresse commune à toutes les salles : affichée une seule fois en haut de page.
function sharedPlace(rooms) {
  const places = [...new Set(rooms.map((room) => room.localisation).filter(Boolean))];
  return places.length === 1 && rooms.every((room) => room.localisation) ? places[0] : "";
}

// Toutes les salles du jour en même temps, sans filtre d'étage. Les colonnes
// s'adaptent au nombre de salles : les cartes remplissent toute la largeur.
function AllRooms({ rooms, reservations, currentTime }) {
  if (!rooms.length) return <EmptyDisplay message="Aucune salle n’est disponible à l’affichage." />;
  const placeShared = Boolean(sharedPlace(rooms));
  return <section className="grid grid-cols-[repeat(auto-fit,minmax(min(100%,22rem),1fr))] gap-5 lg:gap-6">{rooms.map((room) => <RoomCard key={room.id_salle} room={room} showPlace={!placeShared} schedule={roomSchedule(room, reservations, currentTime)} />)}</section>;
}

function RoomCard({ room, schedule, showPlace }) {
  const occupied = Boolean(schedule.current);
  return <article className="flex min-w-0 flex-col overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-[0_15px_50px_rgba(15,23,42,.08)]">
    <div className={`flex items-center justify-between gap-3 px-5 py-4 text-white sm:px-6 sm:py-5 ${occupied ? "bg-[#e13236]" : "bg-black"}`}><DoorOpen size={28} strokeWidth={1.7} /><span className="rounded-full border border-white/25 bg-white/10 px-4 py-1.5 text-sm font-black tracking-wider 2xl:text-base">{occupied ? "OCCUPÉE" : "LIBRE"}</span></div>
    <div className="flex flex-1 flex-col p-5 sm:p-6">
      <h2 className="text-balance wrap-break-word text-2xl font-black leading-tight 2xl:text-3xl">{room.nom_salle}</h2>
      {room.etage && <span className="mt-2 inline-flex w-fit rounded-full bg-slate-100 px-3 py-1 text-xs font-bold uppercase tracking-wider text-slate-600 2xl:text-sm">{room.etage}</span>}
      {showPlace && room.localisation && <p className="mt-2 text-sm text-slate-500 2xl:text-base">{room.localisation}</p>}
      <p className="mt-5 text-lg font-black tabular-nums 2xl:text-xl">{countdownLabel(schedule)}</p>
      <DayBar meetings={schedule.meetings} currentTime={schedule.currentTime} />
      {schedule.meetings.length > 0 && <div className="mt-5 border-t border-slate-200 pt-4">
        <p className="text-sm font-bold uppercase tracking-wider text-slate-400">Réservations du jour</p>
        <ul className="mt-3 space-y-3">{schedule.meetings.map((meeting) => <Slot key={meeting.id_reservation} meeting={meeting} currentTime={schedule.currentTime} />)}</ul>
      </div>}
    </div>
  </article>;
}

// Repères horaires de la frise, placés à leur position exacte.
const DAY_TICKS = [[480, "8h"], [600, "10h"], [720, "12h"], [840, "14h"], [960, "16h"], [1050, "17h30"]];

// Frise de la journée (08h – 17h30) : créneaux occupés et heure actuelle.
function DayBar({ meetings, currentTime }) {
  const span = FERMETURE_MIN - OUVERTURE_MIN;
  const percent = (value) => Math.min(100, Math.max(0, ((timeToMinutes(value) - OUVERTURE_MIN) / span) * 100));
  const now = timeToMinutes(currentTime);
  const nowVisible = now >= OUVERTURE_MIN && now <= FERMETURE_MIN;
  return <div className="mt-4" role="img" aria-label="Occupation de la salle sur la journée">
    <div className="relative h-3.5 rounded-full bg-slate-100">
      {meetings.map((meeting) => <span key={meeting.id_reservation} className={`absolute inset-y-0 rounded-full ${meetingStatus(meeting, currentTime) === "En cours" ? "bg-[#e13236]" : "bg-[#00263e]"}`} style={{ left: `${percent(meeting.heure_debut)}%`, width: `${Math.max(1.5, percent(meeting.heure_fin) - percent(meeting.heure_debut))}%` }} />)}
      {nowVisible && <span className="absolute -inset-y-1 w-0.5 rounded bg-[#e13236]" style={{ left: `${percent(currentTime)}%` }} />}
    </div>
    <div className="relative mt-1.5 h-5 text-xs font-semibold tabular-nums text-slate-400 2xl:text-sm">{DAY_TICKS.map(([minutes, label], index) => <span key={label} className="absolute whitespace-nowrap" style={{ left: `${((minutes - OUVERTURE_MIN) / span) * 100}%`, transform: index === 0 ? "none" : index === DAY_TICKS.length - 1 ? "translateX(-100%)" : "translateX(-50%)" }}>{label}</span>)}</div>
  </div>;
}

function Slot({ meeting, currentTime }) {
  const status = meetingStatus(meeting, currentTime);
  const classes = status === "En cours" ? "bg-[#e13236] text-white" : status === "Terminée" ? "bg-slate-200 text-slate-500" : "bg-black text-white";
  return <li className={`rounded-2xl border border-slate-200 p-3 ${status === "Terminée" ? "opacity-60" : ""}`}>
    <div className="flex items-center justify-between gap-3"><p className="text-lg font-black tabular-nums 2xl:text-xl">{formatTime(meeting.heure_debut)} – {formatTime(meeting.heure_fin)}</p><span className={`shrink-0 rounded-full px-3 py-1 text-xs font-black uppercase tracking-wide ${classes}`}>{status}</span></div>
    <p className="mt-1 wrap-break-word text-base text-slate-600 2xl:text-lg">{meeting.objet}</p>
    {status === "En cours" && <p className="mt-1 text-sm font-semibold tabular-nums text-slate-500">{meetingCountdown(meeting, currentTime)}</p>}
  </li>;
}

function DisplayLoading() {
  return <div className="grid min-h-80 place-items-center rounded-3xl border border-slate-200 bg-white"><div className="text-center"><span className="spinner mx-auto mb-4 block" /><p className="text-lg font-bold text-slate-600">Chargement des salles…</p></div></div>;
}

function EmptyDisplay({ message }) {
  return <div className="grid min-h-80 place-items-center rounded-3xl border border-slate-200 bg-white text-center text-slate-500"><div><DoorOpen className="mx-auto mb-3" size={32} strokeWidth={1.5} /><p className="text-lg font-semibold">{message}</p></div></div>;
}
