import { useEffect, useState } from "react";
import { Camera, Trash2, UserRound } from "lucide-react";
import PageHeader from "../components/PageHeader";
import { Alert, Loading } from "../components/Feedback";
import { apiFetch } from "../lib/api";

export default function MyProfile() {
  const cached = JSON.parse(sessionStorage.getItem("user") || "null");
  const [user, setUser] = useState(cached);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [password, setPassword] = useState({ current_password: "", new_password: "", confirmation: "" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const remember = (data) => {
    setUser(data);
    sessionStorage.setItem("user", JSON.stringify({ ...cached, ...data, name: `${data.first_name || ""} ${data.last_name || ""}`.trim() || data.username }));
  };

  useEffect(() => {
    apiFetch("/me/").then(remember).catch((requestError) => setError(requestError.message)).finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const uploadPhoto = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true); setError("");
    const body = new FormData(); body.append("photo", file);
    try { remember(await apiFetch("/me/photo/", { method: "PATCH", body })); setMessage("Photo de profil enregistrée."); }
    catch (requestError) { setError(requestError.message); }
    finally { setUploading(false); event.target.value = ""; }
  };

  const removePhoto = async () => {
    try { remember(await apiFetch("/me/photo/", { method: "DELETE" })); setMessage("Photo supprimée."); }
    catch (requestError) { setError(requestError.message); }
  };

  const save = async (event) => {
    event.preventDefault(); setError("");
    try { const data = await apiFetch("/me/", { method: "PATCH", body: JSON.stringify({ username: user.username, email: user.email }) }); remember(data); sessionStorage.setItem("username", data.username); setMessage("Profil mis à jour."); }
    catch (requestError) { setError(requestError.message); }
  };

  const changePassword = async (event) => {
    event.preventDefault(); setError("");
    try { const data = await apiFetch("/me/password/", { method: "POST", body: JSON.stringify(password) }); sessionStorage.clear(); window.alert(data.message); window.location.replace("/login"); }
    catch (requestError) { setError(requestError.message); }
  };

  if (loading && !user) return <Loading label="Chargement de votre profil…" />;
  const isSuperAdmin = user?.role === "SUPER_ADMIN";

  return <><PageHeader title="Mon profil" description="Informations du compte actuellement connecté." />{error && <Alert onClose={() => setError("")}>{error}</Alert>}{message && <Alert onClose={() => setMessage("")}>{message}</Alert>}{user && <div className="space-y-6">
    <section className="card flex flex-col items-center gap-5 p-6 sm:flex-row"><div className="grid size-28 shrink-0 place-items-center overflow-hidden rounded-full bg-black text-white">{user.photo_url ? <img className="size-full object-cover" src={user.photo_url} alt="Photo de profil" /> : <UserRound size={48} />}</div><div className="text-center sm:text-left"><h2 className="text-2xl font-black">{user.first_name || user.last_name ? `${user.first_name} ${user.last_name}` : user.username}</h2><p className="text-sm text-slate-500">{user.role}</p><div className="mt-4 flex flex-wrap justify-center gap-2 sm:justify-start"><label className="btn-primary cursor-pointer"><Camera size={17} />{uploading ? "Envoi…" : "Ajouter une photo"}<input className="hidden" type="file" accept="image/jpeg,image/png,image/webp" disabled={uploading} onChange={uploadPhoto} /></label>{user.photo_url && <button className="btn-secondary" onClick={removePhoto}><Trash2 size={16} />Supprimer</button>}</div><p className="mt-2 text-xs text-slate-400">Facultatif · JPG, PNG ou WEBP · 2 Mo maximum</p></div></section>
    <div className={`grid gap-6 ${isSuperAdmin ? "lg:grid-cols-2" : "max-w-2xl"}`}><form className="card space-y-4 p-6" onSubmit={save}><h2 className="font-black">Informations du compte</h2><label className="label">Nom d’utilisateur</label><input className="field" readOnly={!isSuperAdmin} value={user.username || ""} onChange={(e) => setUser({ ...user, username: e.target.value })} /><label className="label">Email professionnel</label><input className="field" type="email" readOnly={!isSuperAdmin} value={user.email || ""} onChange={(e) => setUser({ ...user, email: e.target.value })} /><label className="label">Rôle</label><input className="field bg-slate-50" readOnly value={user.role || ""} />{isSuperAdmin ? <button className="btn-primary">Enregistrer</button> : <p className="rounded-lg bg-slate-50 p-3 text-xs text-slate-500">Ces informations sont gérées par le Super Administrateur et sont disponibles en lecture seule.</p>}</form>{isSuperAdmin && <form className="card space-y-4 p-6" onSubmit={changePassword}><h2 className="font-black">Changer le mot de passe</h2>{[["current_password", "Mot de passe actuel"], ["new_password", "Nouveau mot de passe"], ["confirmation", "Confirmation"]].map(([key, label]) => <div key={key}><label className="label">{label}</label><input className="field" type="password" required value={password[key]} onChange={(e) => setPassword({ ...password, [key]: e.target.value })} /></div>)}<button className="btn-primary">Changer le mot de passe</button></form>}</div>
  </div>}</>;
}
