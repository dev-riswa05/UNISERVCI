import { Menu, UserRound } from "lucide-react";
import LiveClock from "./LiveClock";
import AppName from "./AppName";

const ROLE_TITLES = { SUPER_ADMIN: "Administration", RH: "Espace RH", MANAGER: "Espace Manager" };

export default function Navbar({ onMenu, menuOpen = false }) {
  const profile = JSON.parse(sessionStorage.getItem("user") || "null");
  const role = sessionStorage.getItem("role");
  return <header className="brand-navbar sticky top-0 z-30 flex h-20 items-center justify-between gap-2 px-3 backdrop-blur sm:px-6 lg:px-8">
    <div className="flex min-w-0 items-center gap-3"><button onClick={onMenu} className="grid h-11 w-11 shrink-0 place-items-center rounded-lg border border-slate-200 lg:hidden" aria-label="Ouvrir le menu" aria-expanded={menuOpen} aria-controls="app-sidebar"><Menu size={21} /></button><span className="lg:hidden"><AppName className="text-lg" /></span><div className="hidden min-w-0 lg:block"><div className="flex items-center gap-2"><p className="truncate font-bold text-slate-800">{ROLE_TITLES[role] || "MaSalle"}</p></div></div></div>
    <div className="flex shrink-0 items-center gap-2"><div className="hidden sm:block"><LiveClock /></div><div className="hidden items-center gap-2 rounded-full bg-slate-100 py-1.5 pl-2 pr-3 text-sm font-semibold text-slate-700 md:flex"><span className="grid h-7 w-7 place-items-center rounded-full bg-black text-white"><UserRound size={15} /></span>{profile?.name || profile?.username || "Utilisateur"}</div></div>
  </header>;
}
