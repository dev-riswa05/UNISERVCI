import { useEffect, useState } from "react";
import { ArrowLeft, CalendarDays, CalendarX2, Clock3, Edit3, Mail, MapPin, MessageSquareText, UserRound, Users } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import { Alert, Empty, Loading } from "../components/Feedback";
import { apiFetch } from "../lib/api";
import { formatDate, formatTime, statusClass, statusLabel } from "../lib/format";

export default function ReservationDetails() {
  const { id } = useParams();
  const [reservation, setReservation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    apiFetch(`/reservations/${id}/`)
      .then(setReservation)
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false));
  }, [id]);

  const cancelReservation = async () => {
    if (!window.confirm("Annuler cette réservation confirmée ?\n\nLe créneau sera libéré et les participants seront informés.")) return;
    setCancelling(true); setError(""); setMessage("");
    try {
      await apiFetch(`/reservations/${id}/annuler/`, { method: "POST" });
      setReservation((current) => ({ ...current, statut: "ANNULEE" }));
      setMessage("La réservation a été annulée avec succès.");
    } catch (requestError) { setError(requestError.message); }
    finally { setCancelling(false); }
  };

  if (loading) return <Loading label="Chargement de la réservation…" />;

  return (
    <>
      <PageHeader title="Détail de la réservation" description={`Référence #${id}`}>
        <Link to="/reservations" className="btn-secondary"><ArrowLeft size={17} /> Retour</Link>
        {reservation?.statut !== "ANNULEE" && (
          <Link to={`/reservations/${id}/modifier`} className="btn-primary"><Edit3 size={17} /> Modifier</Link>
        )}
        {reservation?.statut === "CONFIRMEE" && (
          <button type="button" onClick={cancelReservation} disabled={cancelling} className="inline-flex items-center gap-2 rounded-xl bg-red-600 px-4 py-3 font-bold text-white transition hover:bg-red-700 disabled:opacity-50"><CalendarX2 size={17} />{cancelling ? "Annulation…" : "Annuler la réservation"}</button>
        )}
      </PageHeader>
      {error && <Alert>{error}</Alert>}
      {message && <Alert onClose={() => setMessage("")}>{message}</Alert>}
      {!reservation ? <div className="card"><Empty>Cette réservation est introuvable.</Empty></div> : (
        <div className="grid gap-6 xl:grid-cols-[1.25fr_.75fr]">
          <div className="space-y-6">
            <section className="card p-5 sm:p-6">
              <div className="flex flex-col justify-between gap-3 border-b border-slate-100 pb-5 sm:flex-row sm:items-start">
                <div><p className="text-xs font-bold uppercase tracking-wider text-slate-400">Objet de la réunion</p><h2 className="mt-1 text-xl font-black text-slate-900">{reservation.objet}</h2></div>
                <span className={`w-fit rounded-full px-3 py-1.5 text-xs font-bold ${statusClass(reservation.statut)}`}>{statusLabel(reservation.statut)}</span>
              </div>
              <div className="mt-5 grid gap-5 sm:grid-cols-2">
                <Info icon={CalendarDays} label="Date" value={formatDate(reservation.date_reservation, { weekday: "long" })} />
                <Info icon={Clock3} label="Horaire" value={`${formatTime(reservation.heure_debut)} – ${formatTime(reservation.heure_fin)}`} />
                <Info icon={MapPin} label="Salle" value={reservation.salle_nom} />
                <Info icon={Users} label="Nombre déclaré" value={`${reservation.nombre_participants || 0} participant(s)`} />
              </div>
              {reservation.notes && <div className="mt-6 rounded-xl bg-slate-50 p-4"><p className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500"><MessageSquareText size={15} /> Notes</p><p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">{reservation.notes}</p></div>}
            </section>

            <section className="card p-5 sm:p-6">
              <div className="mb-4 flex items-center justify-between"><div><h2 className="font-bold text-slate-900">Participants</h2><p className="text-xs text-slate-500">Destinataires des invitations et rappels</p></div><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-600">{reservation.participants?.length || 0}</span></div>
              {reservation.participants?.length ? <div className="divide-y divide-slate-100">{reservation.participants.map((participant, index) => <div key={`${participant.email}-${index}`} className="flex items-center gap-3 py-3"><span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-black text-white"><UserRound size={17} strokeWidth={1.8} /></span><div className="min-w-0"><p className="truncate text-sm font-bold text-slate-800">{participant.nom || "Participant"}</p><p className="truncate text-xs text-slate-500">{participant.email}</p></div></div>)}</div> : <p className="rounded-xl border border-dashed border-slate-200 py-8 text-center text-sm text-slate-500">Aucun participant prévu pour cette réunion.</p>}
            </section>
          </div>

          <aside className="space-y-5">
            <section className="card p-5"><h2 className="font-bold text-slate-900">Demandeur</h2><div className="mt-4 flex items-center gap-3"><span className="grid h-11 w-11 place-items-center rounded-xl bg-black text-white"><UserRound size={20} strokeWidth={1.8} /></span><div className="min-w-0"><p className="truncate font-bold text-slate-800">{reservation.nom_demandeur}</p><a href={`mailto:${reservation.email_demandeur}`} className="flex items-center gap-1.5 truncate text-xs text-black underline-offset-2 hover:underline"><Mail size={13} />{reservation.email_demandeur}</a></div></div></section>
            <section className="rounded-2xl border border-slate-300 bg-slate-100 p-5"><h3 className="text-sm font-bold text-slate-900">À propos des notifications</h3><p className="mt-2 text-xs leading-relaxed text-slate-600">Le demandeur et les participants sont prévenus après chaque changement. Un rappel est aussi prévu deux heures avant la réunion.</p></section>
          </aside>
        </div>
      )}
    </>
  );
}

function Info({ icon: Icon, label, value }) {
  return <div className="flex items-start gap-3"><span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-black text-white"><Icon size={17} strokeWidth={1.8} /></span><div><p className="text-xs font-medium text-slate-400">{label}</p><p className="mt-0.5 text-sm font-bold capitalize text-slate-800">{value}</p></div></div>;
}
