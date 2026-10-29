import { useState } from "react";
import { ArrowRight, CalendarCheck, ChevronDown, Eye, EyeOff, LogIn, MailCheck, Monitor, ShieldCheck } from "lucide-react";
import { Link, Navigate, useLocation } from "react-router-dom";
import { resolveApiUrl } from "../lib/api";
import { homeForRole } from "../lib/session";
import BrandLogo from "../components/BrandLogo";

// Trois fonctions essentielles, affichées dans le panneau de marque.
const FEATURES = [
  [CalendarCheck, "Réservation en quelques clics", "Choisissez la salle, l'horaire et les participants."],
  [Monitor, "Planning en direct", "Les disponibilités de toutes les salles, sur écran ou depuis votre poste."],
  [MailCheck, "Participants prévenus", "Chaque réservation est confirmée par email aux personnes invitées."],
];

export default function Home() {
  const location = useLocation();

  // Le formulaire reste replié tant que l'utilisateur n'a pas choisi « Se connecter ».
  const [open, setOpen] = useState(Boolean(location.state?.from));
  const [form, setForm] = useState({ email: "", password: "" });

  // Ces états contrôlent les retours visuels du formulaire.
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [show, setShow] = useState(false);

  // Un utilisateur déjà authentifié est envoyé directement vers son espace.
  if (sessionStorage.getItem("token"))
    return <Navigate to={homeForRole(sessionStorage.getItem("role"))} replace />;

  // Envoie les identifiants au backend puis mémorise la session dans l'onglet.
  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const response = await fetch(`${resolveApiUrl()}/login/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ email: form.email.trim(), password: form.password }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data.token)
        throw new Error(
          response.status === 429
            ? "Trop de tentatives. Réessayez dans quelques instants."
            : data.detail || data.erreur || "Identifiants incorrects.",
        );
      // sessionStorage est propre à chaque onglet : plusieurs comptes peuvent
      // ainsi être ouverts simultanément dans le même navigateur.
      sessionStorage.setItem("token", data.token);
      sessionStorage.setItem("role", data.role);
      sessionStorage.setItem("username", data.username || "");
      sessionStorage.setItem("user", JSON.stringify(data));
      window.location.replace(location.state?.from || homeForRole(data.role));
    } catch (e) {
      setError(
        e.message === "Failed to fetch"
          ? "Le serveur est injoignable."
          : e.message,
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-shell grid min-h-screen bg-white lg:grid-cols-[1.08fr_.92fr]">
      {/* Panneau institutionnel visible sur les grands écrans. */}
      <section className="login-brand-panel hidden p-14 text-white lg:flex lg:flex-col">
        <div className="flex flex-1 flex-col">
          {/* Bloc 1 : le logo UNISERV et le nom MaSalle, ensemble. */}
          <h1>
            <BrandLogo light className="brand-lockup--hero" nameClassName="text-5xl xl:text-6xl" />
          </h1>

          {/* Bloc 2 : les textes qui suivent le nom. */}
          <div className="mt-12">
            <span className="block text-xs font-bold uppercase tracking-[.34em] text-(--uniserv-sky)">
              Espace collaboratif UNISERV BTP
            </span>
            <p className="mt-4 max-w-xl text-3xl font-black leading-[1.15]">
              Bâtir ensemble.
              <br />
              <span className="text-(--uniserv-sky)">Réunir efficacement.</span>
            </p>
            <p className="mt-5 max-w-lg text-sky-50/70">
              La plateforme interne de réservation et de gestion des salles de
              réunion.
            </p>
          </div>

          {/* Bloc 3 : les trois fonctions essentielles. */}
          <ul className="mt-12 grid max-w-xl gap-6">
            {FEATURES.map(([Icon, title, text]) => (
              <li key={title} className="flex items-start gap-4">
                <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl border border-white/15 bg-white/10">
                  <Icon size={21} strokeWidth={1.8} />
                </span>
                <span>
                  <strong className="block text-base font-bold">{title}</strong>
                  <span className="text-sm text-sky-50/65">{text}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
        <small className="text-sky-100/50">
          © {new Date().getFullYear()} UNISERV BTP · Bâtir durablement
        </small>
      </section>
      {/* Choix d'accès, toujours visible y compris sur mobile. */}
      <section className="login-form-panel flex items-center justify-center p-4 sm:p-8">
        <div className="brand-login-card w-full min-w-0 max-w-lg rounded-3xl bg-white p-6 shadow-xl sm:p-9">
          {/* Sur téléphone et tablette le panneau de marque est masqué : on le résume ici. */}
          <h1 className="mb-6 lg:hidden">
            <BrandLogo nameClassName="text-3xl" />
          </h1>
          <h2 className="text-3xl font-black sm:text-4xl">Bienvenue</h2>
          <p className="mb-7 mt-2 text-sm text-slate-500 sm:text-base">
            Choisissez comment accéder à la plateforme.
          </p>
          <button
            type="button"
            aria-expanded={open}
            aria-controls="login-panel"
            onClick={() => setOpen(!open)}
            className="access-option access-option--primary"
          >
            <span className="access-option__icon"><LogIn size={22} /></span>
            <span className="access-option__text">
              <strong>Se connecter</strong>
              <small>Réservations, planning et administration</small>
            </span>
            <ChevronDown size={20} className={`transition-transform ${open ? "rotate-180" : ""}`} aria-hidden="true" />
          </button>
          {/* Accordéon : la grille passe de 0fr à 1fr pour un déploiement fluide. */}
          <div
            id="login-panel"
            className={`grid transition-[grid-template-rows,opacity] duration-300 ${open ? "grid-rows-[1fr] opacity-100" : "invisible grid-rows-[0fr] opacity-0"}`}
          >
            <div className="min-h-0 overflow-hidden">
              <form onSubmit={submit} className="pt-5">
                {error && (
                  <div
                    role="alert"
                    className="mb-5 rounded-lg border bg-slate-50 p-3 text-sm"
                  >
                    {error}
                  </div>
                )}
                <label className="label" htmlFor="login-email">Email</label>
                <input
                  id="login-email"
                  className="field mb-4"
                  type="email"
                  autoComplete="username"
                  required
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                />
                <label className="label" htmlFor="login-password">Mot de passe</label>
                <div className="relative mb-6">
                  <input
                    id="login-password"
                    className="field pr-12"
                    type={show ? "text" : "password"}
                    autoComplete="current-password"
                    required
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                  />
                  <button
                    type="button"
                    onClick={() => setShow(!show)}
                    aria-label={show ? "Masquer le mot de passe" : "Afficher le mot de passe"}
                    className="absolute right-1 top-1/2 grid h-10 w-10 -translate-y-1/2 place-items-center"
                  >
                    {show ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
                <button className="btn-primary w-full py-3" disabled={loading}>
                  {loading ? "Connexion…" : "Se connecter"}
                </button>
              </form>
            </div>
          </div>
          <Link to="/affichage" className="access-option mt-4">
            <span className="access-option__icon"><Monitor size={22} /></span>
            <span className="access-option__text">
              <strong>Écran</strong>
              <small>Disponibilité des salles en direct, sans connexion</small>
            </span>
            <ArrowRight size={20} aria-hidden="true" />
          </Link>
          <p className="mt-7 flex items-start gap-2 border-t border-slate-200 pt-5 text-xs leading-relaxed text-slate-500">
            <ShieldCheck size={16} className="mt-px shrink-0" aria-hidden="true" />
            Accès réservé au personnel UNISERV BTP. Besoin d’un accès ? Contactez le service informatique.
          </p>
        </div>
      </section>
    </main>
  );
}
