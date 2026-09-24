import { useEffect, useState } from "react";
import { Building2, CalendarDays, CheckCircle2, Clock3, DoorOpen, MapPin, Users } from "lucide-react";
import PageHeader from "../components/PageHeader";
import { Alert, Empty, Loading } from "../components/Feedback";
import { apiFetch } from "../lib/api";
import { todayISO } from "../lib/format";
import { formatTimeOption, isSlotWithinOpeningHours, START_TIME_OPTIONS, TIME_OPTIONS } from "../lib/schedule";

export default function Rooms() {
  const [rooms, setRooms] = useState([]);
  const [availableIds, setAvailableIds] = useState(null);
  const [slot, setSlot] = useState({ date: todayISO(), start: "", end: "" });
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState("");

  const updateSlot = (field, value) => {
    setSlot((current) => ({
      ...current,
      [field]: value,
      ...(field === "start" && current.end <= value ? { end: "" } : {}),
    }));
    // Dès qu'un critère change, l'ancien résultat n'est plus représentatif.
    setAvailableIds(null);
  };

  useEffect(() => {
    apiFetch("/salles/")
      .then(setRooms)
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false));
  }, []);

  const checkAvailability = async (event) => {
    event.preventDefault();
    setError("");
    if (!isSlotWithinOpeningHours(slot.start, slot.end)) {
      setError("Le créneau doit être compris entre 08h00 et 17h30.");
      return;
    }
    setChecking(true);
    try {
      const params = new URLSearchParams({
        date: slot.date,
        heure_debut: slot.start,
        heure_fin: slot.end,
      });
      const available = await apiFetch(`/salles/disponibles/?${params}`);
      setAvailableIds(new Set(available.map((room) => room.id_salle)));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setChecking(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Salles de réunion"
        description="Consultez les caractéristiques des salles et vérifiez un créneau."
      />
      {error && <Alert onClose={() => setError("")}>{error}</Alert>}

      <form onSubmit={checkAvailability} className="card mb-6 grid gap-4 p-4 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_1fr_auto] lg:items-end">
        <div>
          <label className="label" htmlFor="room-date"><CalendarDays size={15} className="mr-1 inline" />Date</label>
          <input id="room-date" className="field" type="date" min={todayISO()} required value={slot.date} onChange={(event) => updateSlot("date", event.target.value)} />
        </div>
        <div>
          <label className="label" htmlFor="room-start"><Clock3 size={15} className="mr-1 inline" />Heure de début</label>
          <select id="room-start" className="field" required value={slot.start} onChange={(event) => updateSlot("start", event.target.value)}><option value="">Choisir</option>{START_TIME_OPTIONS.map((time) => <option key={time} value={time}>{formatTimeOption(time)}</option>)}</select>
        </div>
        <div>
          <label className="label" htmlFor="room-end"><Clock3 size={15} className="mr-1 inline" />Heure de fin</label>
          <select id="room-end" className="field" required disabled={!slot.start} value={slot.end} onChange={(event) => updateSlot("end", event.target.value)}><option value="">Choisir</option>{TIME_OPTIONS.filter((time) => time > slot.start).map((time) => <option key={time} value={time}>{formatTimeOption(time)}</option>)}</select>
        </div>
        <button className="btn-primary" disabled={checking}>{checking ? "Vérification…" : "Vérifier"}</button>
      </form>

      {loading ? <Loading /> : !rooms.length ? <div className="card"><Empty>Aucune salle enregistrée.</Empty></div> : (
        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {rooms.map((room) => {
            const isAvailable = availableIds?.has(room.id_salle);
            const wasChecked = availableIds !== null;
            return (
              <article key={room.id_salle} className={`card overflow-hidden transition ${wasChecked && !isAvailable ? "opacity-65" : ""}`}>
                <div className="flex items-start justify-between bg-black p-5 text-white">
                  <span className="grid h-11 w-11 place-items-center rounded-xl bg-white/10"><DoorOpen size={23} /></span>
                  {wasChecked && <span className={`rounded-full border px-3 py-1 text-xs font-bold ${isAvailable ? "border-white bg-white text-black" : "border-white/20 bg-white/10 text-slate-300"}`}>{isAvailable ? "Disponible" : "Occupée"}</span>}
                </div>
                <div className="p-5">
                  <h2 className="font-black text-slate-900">{room.nom_salle}</h2>
                  <div className="mt-4 space-y-2.5 text-sm text-slate-500">
                    <p className="flex items-start gap-2"><MapPin size={17} className="mt-0.5 shrink-0 text-black" strokeWidth={1.8} />{room.localisation || "Localisation non renseignée"}</p>
                    <p className="flex items-center gap-2"><Building2 size={17} className="text-black" strokeWidth={1.8} />{room.etage || "Étage non renseigné"}</p>
                    <p className="flex items-center gap-2"><Users size={17} className="text-black" strokeWidth={1.8} />{room.capacite ? `${room.capacite} places indicatives` : "Capacité non renseignée"}</p>
                  </div>
                  {room.description && <p className="mt-4 border-t border-slate-100 pt-4 text-xs leading-relaxed text-slate-500">{room.description}</p>}
                  {!wasChecked && room.active && <p className="mt-4 flex items-center gap-2 text-xs font-bold text-slate-700"><CheckCircle2 size={15} /> Disponible à la réservation</p>}
                </div>
              </article>
            );
          })}
        </section>
      )}
    </>
  );
}
