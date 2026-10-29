import { useEffect } from "react";
import { DoorOpen, LayoutDashboard, ListChecks, Plus, Settings, UserCog, CalendarDays, LogOut, X } from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";
import BrandLogo from "./BrandLogo";
import { homeForRole, logout as endSession } from "../lib/session";

// Chaque lien : [chemin, libellé, icône]. Chaque profil ne voit que ce dont il se sert.
const adminLinks = [
  ["/dashboard", "Tableau de bord", LayoutDashboard],
  ["/reservations", "Réservations", ListChecks],
  ["/administration", "Comptes et salles", Settings],
  ["/mon-profil", "Mon profil", UserCog],
];
const rhLinks = [
  ["/dashboard", "Tableau de bord", LayoutDashboard],
  ["/reservations", "Réservations", ListChecks],
  ["/reservations/nouvelle", "Nouvelle réservation", Plus],
  ["/salles", "Salles", DoorOpen],
  ["/mon-profil", "Mon profil", UserCog],
];
const managerLinks = [
  ["/planning", "Planning", CalendarDays],
  ["/reservations", "Mes réservations", ListChecks],
  ["/reservations/nouvelle", "Nouvelle réservation", Plus],
  ["/mon-profil", "Mon profil", UserCog],
];
const LINKS_BY_ROLE = { SUPER_ADMIN: adminLinks, RH: rhLinks, MANAGER: managerLinks };

export default function Sidebar({ open, onClose }) {
  const role = sessionStorage.getItem("role");
  const links = LINKS_BY_ROLE[role] || rhLinks;
  const navigate = useNavigate();
  const logout = async () => {
    await endSession();
    navigate("/", { replace: true });
  };

  // Échap ferme le tiroir sur téléphone et tablette.
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (event) => { if (event.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  return <>
    {open && <button aria-label="Fermer le menu" className="fixed inset-0 z-40 bg-slate-950/45 lg:hidden" onClick={onClose} />}
    <aside id="app-sidebar" aria-label="Menu principal" className={`brand-sidebar fixed inset-y-0 left-0 z-50 flex w-[min(16rem,88vw)] flex-col overflow-y-auto text-white transition-[transform,visibility] lg:visible lg:w-64 lg:translate-x-0 ${open ? "visible translate-x-0" : "invisible -translate-x-full"}`}>
      <div className="flex h-24 items-center justify-between border-b border-white/10 px-5">
        <BrandLogo light to={homeForRole(role)} onClick={onClose} nameClassName="text-xl" />
        <button className="grid h-10 w-10 place-items-center rounded-lg text-slate-300 hover:bg-white/10 lg:hidden" onClick={onClose} aria-label="Fermer le menu"><X size={20} /></button>
      </div>
      <nav className="flex-1 space-y-1 p-3 pt-6">
        {links.map(([to, label, Icon]) => <NavLink key={to} to={to} end={to === "/reservations"} onClick={onClose} className={({ isActive }) => `flex min-h-11 items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${isActive ? "bg-white/15 text-white" : "text-slate-300 hover:bg-white/10 hover:text-white"}`}><Icon size={19} strokeWidth={1.8} />{label}</NavLink>)}
      </nav>
      <div className="border-t border-white/10 p-3">
        <button type="button" onClick={logout} className="flex min-h-11 w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-300 transition hover:bg-white/10 hover:text-white"><LogOut size={19} strokeWidth={1.8} />Se déconnecter</button>
      </div>
    </aside>
  </>;
}
