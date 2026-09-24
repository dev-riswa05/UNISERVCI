import { DoorOpen, LayoutDashboard, ListChecks, Monitor, Plus, Settings, UserCog, X } from "lucide-react";
import { NavLink } from "react-router-dom";
import BrandLogo from "./BrandLogo";

const links = [
  ["/dashboard", "Tableau de bord", LayoutDashboard],
  ["/salles", "Salles", DoorOpen],
  ["/reservations", "Réservations", ListChecks],
  ["/reservations/nouvelle", "Nouvelle réservation", Plus],
  ["/salles-vue", "Salles Vue", Monitor],
  ["/mon-profil", "Mon profil", UserCog],
];

export default function Sidebar({ open, onClose }) {
  const superAdmin = sessionStorage.getItem("role") === "SUPER_ADMIN";
  return <>
    {open && <button aria-label="Fermer le menu" className="fixed inset-0 z-40 bg-slate-950/45 lg:hidden" onClick={onClose} />}
    <aside className={`brand-sidebar fixed inset-y-0 left-0 z-50 flex w-[min(16rem,88vw)] flex-col overflow-y-auto text-white transition-transform lg:w-64 lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}>
      <div className="flex h-24 items-center justify-between border-b border-white/10 px-5">
        <div><BrandLogo light /><p className="mt-1 text-[10px] font-semibold uppercase tracking-[.22em] text-sky-100/70">Gestion des salles</p></div>
        <button className="rounded-lg p-2 text-slate-300 hover:bg-white/10 lg:hidden" onClick={onClose}><X size={20} /></button>
      </div>
      <nav className="flex-1 space-y-1 p-3 pt-6">
        {links.map(([to, label, Icon]) => <NavLink key={to} to={to} onClick={onClose} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold transition ${isActive ? "bg-white text-[#00263e] shadow-lg" : "text-sky-50/75 hover:bg-white/10 hover:text-white"}`}><Icon size={19} strokeWidth={1.8} />{label}</NavLink>)}
      </nav>
      {superAdmin && <nav className="space-y-1 border-t border-white/10 p-3"><p className="px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-slate-500">Administration</p><NavLink to="/administration" onClick={onClose} className="flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold text-slate-300 hover:bg-white/10"><Settings size={19}/>Gestion salles & RH</NavLink></nav>}
      <div className="m-4 rounded-xl bg-white/6 p-4 text-xs leading-relaxed text-slate-400"><span className="font-bold text-slate-200">Espace RH</span><br />Réservations et planning commun</div>
    </aside>
  </>;
}
