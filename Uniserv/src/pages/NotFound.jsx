import { ArrowLeft, SearchX } from "lucide-react";
import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="card mx-auto mt-10 max-w-xl p-8 text-center sm:p-12">
      <span className="mx-auto mb-5 grid h-16 w-16 place-items-center rounded-2xl bg-black text-white">
        <SearchX size={30} />
      </span>
      <p className="text-sm font-black uppercase tracking-[.2em] text-slate-500">Erreur 404</p>
      <h1 className="mt-2 text-3xl font-black text-slate-900">Page introuvable</h1>
      <p className="mx-auto mt-3 max-w-md text-sm leading-relaxed text-slate-500">
        L’adresse demandée n’existe pas ou la page a été déplacée.
      </p>
      <Link className="btn-primary mt-7" to="/dashboard">
        <ArrowLeft size={18} /> Retour au tableau de bord
      </Link>
    </div>
  );
}
