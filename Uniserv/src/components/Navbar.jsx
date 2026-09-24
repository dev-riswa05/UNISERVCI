import { LogOut, Menu, UserRound } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../lib/api";
import LiveClock from "./LiveClock";

export default function Navbar({ onMenu }) {
  const navigate = useNavigate();
  const profile = JSON.parse(sessionStorage.getItem("user") || "null");
  const role = sessionStorage.getItem("role");
  const roleLabel = role === "SUPER_ADMIN" ? "Super Admin" : role === "RH" ? "Équipe RH" : "Affichage";
  const logout = async () => {
    try { await apiFetch("/logout/", { method: "POST" }); } catch { /* Le nettoyage local reste prioritaire hors connexion. */ }
    sessionStorage.clear(); navigate("/login", { replace: true });
  };
  return <header className="brand-navbar sticky top-0 z-30 flex h-20 items-center justify-between px-4 backdrop-blur sm:px-6 lg:px-8">
    <div className="flex items-center gap-3"><button onClick={onMenu} className="rounded-lg border border-slate-200 p-2 lg:hidden" aria-label="Ouvrir le menu"><Menu size={21} /></button><div><div className="flex items-center gap-2"><p className="font-bold text-slate-800">Espace Ressources Humaines</p><span className="role-badge hidden sm:inline-flex">{roleLabel}</span></div><p className="hidden text-xs text-slate-500 sm:block">Salles de réunion · Siège UNISERV BTP</p></div></div>
    <div className="flex items-center gap-2"><LiveClock /><div className="hidden items-center gap-2 rounded-full bg-slate-100 py-1.5 pl-2 pr-3 text-sm font-semibold text-slate-700 md:flex"><span className="grid h-7 w-7 place-items-center rounded-full bg-black text-white"><UserRound size={15} /></span>{profile?.name || profile?.username || profile?.nom || "Service RH"}</div><button onClick={logout} title="Se déconnecter" className="rounded-lg p-2.5 text-slate-500 hover:bg-slate-100 hover:text-black"><LogOut size={20} /></button></div>
  </header>;
}
