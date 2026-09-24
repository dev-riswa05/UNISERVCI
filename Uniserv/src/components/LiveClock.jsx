import { useEffect, useMemo, useState } from "react";
import { Clock3 } from "lucide-react";

const TIME_ZONE = "Africa/Abidjan";

function clockParts(date) {
  return new Intl.DateTimeFormat("fr-FR", {
    timeZone: TIME_ZONE,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date).reduce((parts, item) => {
    if (item.type !== "literal") parts[item.type] = item.value;
    return parts;
  }, {});
}

export default function LiveClock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const interval = window.setInterval(() => setNow(new Date()), 1_000);
    return () => window.clearInterval(interval);
  }, []);
  const time = useMemo(() => clockParts(now), [now]);
  return <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-2.5 py-1.5 tabular-nums" title="Heure de Côte d’Ivoire">
    <Clock3 className="hidden text-slate-500 sm:block" size={18} />
    <TimeUnit value={time.hour} label="h" />
    <span className="font-black text-slate-400">:</span>
    <TimeUnit value={time.minute} label="min" />
    <span className="font-black text-slate-400">:</span>
    <TimeUnit value={time.second} label="s" highlight />
  </div>;
}

function TimeUnit({ value, label, highlight = false }) {
  return <span className={`flex items-baseline gap-0.5 font-black ${highlight ? "text-red-600" : "text-slate-900"}`}><span className="text-base sm:text-lg">{value}</span><small className="text-[8px] font-bold uppercase text-slate-400">{label}</small></span>;
}
