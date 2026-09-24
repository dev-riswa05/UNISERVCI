import { AlertCircle, CheckCircle2, X } from "lucide-react";

export function Loading({ label = "Chargement…" }) { return <div className="flex items-center justify-center gap-3 py-16 text-sm text-slate-500"><span className="spinner" />{label}</div>; }
export function Empty({ children }) { return <div className="py-16 text-center text-sm text-slate-500">{children}</div>; }
export function Alert({ type = "error", children, onClose }) { const ok = type === "success"; return <div className={`mb-5 flex items-start gap-3 rounded-xl border p-3.5 text-sm ${ok ? "border-[#003764] bg-[#00263e] text-white" : "border-[#cbdde6] bg-white text-[#00263e]"}`}>{ok ? <CheckCircle2 size={19} /> : <AlertCircle size={19} />}<span className="flex-1">{children}</span>{onClose && <button aria-label="Fermer le message" onClick={onClose}><X size={17} /></button>}</div>; }
