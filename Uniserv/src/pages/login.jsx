import { useState } from "react";
import { Eye, EyeOff, LockKeyhole, Monitor, ShieldCheck } from "lucide-react";
import { Navigate, useLocation } from "react-router-dom";
import { API_URL } from "../lib/api";
import BrandLogo from "../components/BrandLogo";

export default function Login() {
  const location = useLocation();

  // `mode` représente le profil choisi : Super Admin, RH ou écran d'affichage.
  const [mode, setMode] = useState("RH");
  const [form, setForm] = useState({ email: "", username: "", password: "" });

  // Ces états contrôlent les retours visuels du formulaire.
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [show, setShow] = useState(false);

  // Un utilisateur déjà authentifié ne doit pas revoir la page de connexion.
  if (sessionStorage.getItem("token"))
    return (
      <Navigate
        to={
          sessionStorage.getItem("role") === "AFFICHAGE"
            ? "/affichage"
            : "/dashboard"
        }
        replace
      />
    );
  // Envoie les identifiants au backend puis mémorise la session dans l'onglet.
  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/login/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ ...form, role: mode }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data.token)
        throw new Error(
          data.detail || data.erreur || "Identifiants incorrects.",
        );
      // sessionStorage est propre à chaque onglet : plusieurs comptes peuvent
      // ainsi être ouverts simultanément dans le même navigateur.
      sessionStorage.setItem("token", data.token);
      sessionStorage.setItem("role", data.role);
      sessionStorage.setItem("username", data.username || "");
      sessionStorage.setItem("user", JSON.stringify(data));
      // Les tablettes ont une interface dédiée, les autres profils utilisent
      // le tableau de bord ou la page demandée avant la connexion.
      window.location.replace(
        data.role === "AFFICHAGE"
          ? "/affichage"
          : location.state?.from || "/dashboard",
      );
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
  // Une ligne contient : [valeur envoyée à l'API, libellé, icône].
  const modes = [
    ["SUPER_ADMIN", "Super Admin", ShieldCheck],
    ["RH", "Équipe RH", LockKeyhole],
    ["AFFICHAGE", "Écran", Monitor],
  ];
  return (
    <main className="login-shell grid min-h-screen bg-white lg:grid-cols-[1.08fr_.92fr]">
      {/* Panneau institutionnel visible sur les grands écrans. */}
      <section className="login-brand-panel hidden p-14 text-white lg:flex lg:flex-col lg:justify-between">
        <BrandLogo light />
        <div>
          <span className="mb-5 block text-xs font-bold uppercase tracking-[.34em] text-sky-200">
            Espace collaboratif
          </span>
          <h1 className="max-w-xl text-5xl font-black leading-[1.08]">
            Bâtir ensemble.
            <br />
            <span className="text-sky-200">Réunir efficacement.</span>
          </h1>
          <p className="mt-5 max-w-lg text-sky-50/70">
            La plateforme interne de réservation et de gestion des espaces
            UNISERV BTP.
          </p>
        </div>
        <small className="text-sky-100/50">
          © {new Date().getFullYear()} UNISERV BTP · Bâtir durablement
        </small>
      </section>
      {/* Formulaire principal, toujours visible y compris sur mobile. */}
      <section className="login-form-panel flex items-center justify-center p-5">
        <form
          onSubmit={submit}
          className="brand-login-card w-full max-w-md rounded-2xl bg-white p-7 shadow-xl"
        >
          <BrandLogo className="mb-8 lg:hidden" />
          <h1 className="text-3xl font-black">Connexion</h1>
          <p className="mb-6 mt-2 text-sm text-slate-500">
            Choisissez votre espace.
          </p>
          <div className="mb-6 grid grid-cols-3 rounded-xl bg-[#edf3f6] p-1">
            {modes.map(([value, label, Icon]) => (
              <button
                key={value}
                type="button"
                onClick={() => {
                  setMode(value);
                  setError("");
                }}
                className={`flex items-center justify-center gap-1 rounded-lg py-2 text-xs font-bold ${mode === value ? "bg-[#00263e] text-white shadow" : "text-slate-500"}`}
              >
                <Icon size={15} />
                {label}
              </button>
            ))}
          </div>
          {error && (
            <div className="mb-5 rounded-lg border bg-slate-50 p-3 text-sm">
              {error}
            </div>
          )}
          {/* L'adresse e-mail supplémentaire est exigée uniquement pour le Super Admin. */}
          {mode === "SUPER_ADMIN" && (
            <>
              <label className="label">Adresse email</label>
              <input
                className="field mb-4"
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </>
          )}
          <label className="label">Nom d'utilisateur</label>
          <input
            className="field mb-4"
            required
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            placeholder={mode === "AFFICHAGE" ? "TABLETTE" : "KARELL"}
          />
          <label className="label">Mot de passe</label>
          <div className="relative mb-7">
            <input
              className="field pr-12"
              type={show ? "text" : "password"}
              required
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
            <button
              type="button"
              onClick={() => setShow(!show)}
              className="absolute right-3 top-1/2 -translate-y-1/2"
            >
              {show ? <EyeOff /> : <Eye />}
            </button>
          </div>
          <button className="btn-primary w-full py-3" disabled={loading}>
            {loading ? "Connexion…" : "Se connecter"}
          </button>
        </form>
      </section>
    </main>
  );
}
