import { useNavigate } from "react-router-dom";
import { formatTime } from "../lib/format";

const START = 480;
const END = 1050;
const HEIGHT = 950;
const toMinutes = (value) => {
  const [hours, minutes] = value.slice(0, 5).split(":").map(Number);
  return hours * 60 + minutes;
};
const toTime = (value) => `${String(Math.floor(value / 60)).padStart(2, "0")}:${String(value % 60).padStart(2, "0")}`;

export default function GoogleCalendar({ days, items, onSelect }) {
  const navigate = useNavigate();
  const today = new Date().toISOString().slice(0, 10);
  const slots = Array.from({ length: 20 }, (_, index) => START + index * 30);

  const createFromSlot = (event, date) => {
    if (event.target !== event.currentTarget) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    const clicked = START + ((event.clientY - bounds.top) / HEIGHT) * (END - START);
    const start = Math.min(END - 30, Math.max(START, Math.round(clicked / 30) * 30));
    navigate(`/reservations/nouvelle?date=${date}&debut=${toTime(start)}&fin=${toTime(start + 30)}`);
  };

  return <div className="card overflow-hidden">
    <div className="overflow-auto" style={{ maxHeight: 760 }}>
      <div className="grid min-w-[1050px]" style={{ gridTemplateColumns: "74px repeat(7, minmax(135px, 1fr))" }}>
        <div className="sticky left-0 top-0 z-30 border-b border-r bg-white" />
        {days.map(({ iso, date }) => <div key={iso} className="sticky top-0 z-20 border-b border-r bg-white px-2 py-3 text-center">
          <p className="text-xs font-bold uppercase text-slate-500">{date.toLocaleDateString("fr-FR", { weekday: "short" })}</p>
          <span className={`mx-auto mt-1 grid h-9 w-9 place-items-center rounded-full text-lg font-black ${iso === today ? "bg-black text-white" : "text-slate-800"}`}>{date.getDate()}</span>
        </div>)}
        <div className="sticky left-0 z-10 relative border-r bg-white" style={{ height: HEIGHT }}>
          {slots.map((slot) => <span key={slot} className="absolute right-3 -translate-y-2 text-[11px] text-slate-400" style={{ top: ((slot - START) / (END - START)) * HEIGHT }}>{toTime(slot)}</span>)}
        </div>
        {days.map(({ iso }) => <div
          key={iso}
          title="Double-cliquez pour réserver"
          onDoubleClick={(event) => createFromSlot(event, iso)}
          className={`relative cursor-crosshair border-r ${iso === today ? "bg-slate-50/80" : "bg-white"}`}
          style={{ height: HEIGHT, backgroundImage: "repeating-linear-gradient(to bottom, transparent 0, transparent 49px, #e2e8f0 50px)" }}
        >
          {items.filter((item) => item.date_reservation === iso).map((item, index) => {
            const top = ((toMinutes(item.heure_debut) - START) / (END - START)) * HEIGHT;
            const eventHeight = Math.max(42, ((toMinutes(item.heure_fin) - toMinutes(item.heure_debut)) / (END - START)) * HEIGHT);
            return <button
              key={item.id_reservation}
              onClick={() => onSelect(item)}
              className={`absolute z-10 overflow-hidden rounded-md border-l-4 px-2 py-1.5 text-left text-xs shadow-sm transition hover:z-20 hover:shadow-lg ${item.statut === "ANNULEE" ? "border-slate-400 bg-slate-100 text-slate-500 opacity-70" : "border-black bg-slate-800 text-white"}`}
              style={{ top, height: eventHeight, left: `${4 + (index % 2) * 2}%`, right: "4%" }}
            ><b className="block truncate">{item.objet}</b><span className="block truncate">{formatTime(item.heure_debut)} – {formatTime(item.heure_fin)}</span><span className="block truncate opacity-75">{item.salle_nom}</span></button>;
          })}
        </div>)}
      </div>
    </div>
    <div className="flex flex-wrap justify-between gap-2 border-t bg-slate-50 px-4 py-2 text-xs text-slate-500"><span>Semaine du {days[0].date.toLocaleDateString("fr-FR", { day: "numeric", month: "long" })} au {days[6].date.toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" })}</span><span>Double-cliquez sur un créneau vide pour réserver</span></div>
  </div>;
}
