import { useEffect, useState } from "react";
import { Edit3, Mail, Plus, Save, Trash2, X } from "lucide-react";
import PageHeader from "../components/PageHeader";
import { Alert, Loading } from "../components/Feedback";
import { apiFetch } from "../lib/api";

// Valeurs initiales des deux formulaires de création.
// Les réutiliser permet aussi de vider facilement un formulaire après succès.
const emptyMember = {
  nom: "",
  prenom: "",
  username: "",
  email: "",
  password: "",
  actif: true,
};
const emptyRoom = {
  nom_salle: "",
  localisation: "",
  etage: "",
  capacite: "",
  description: "",
  active: true,
};

export default function Administration() {
  // Données chargées depuis l'API.
  const [users, setUsers] = useState([]);
  const [rooms, setRooms] = useState([]);

  // Valeurs en cours de saisie dans les formulaires.
  const [member, setMember] = useState(emptyMember);
  const [room, setRoom] = useState(emptyRoom);
  const [editingRoom, setEditingRoom] = useState(null);

  // États de l'interface : chargement, enregistrement et messages utilisateur.
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  // Charge les utilisateurs RH et les salles en parallèle pour réduire l'attente.
  const load = () =>
    Promise.all([
      apiFetch("/administration/utilisateurs-rh/"),
      apiFetch("/salles/"),
    ])
      .then(([members, roomList]) => {
        setUsers(members);
        setRooms(roomList);
      })
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false));

  // Le tableau est chargé une seule fois à l'ouverture de la page.
  useEffect(() => {
    load();
  }, []);

  // Crée un nouveau compte RH à partir du premier formulaire.
  const addMember = async (event) => {
    event.preventDefault();
    try {
      const data = await apiFetch("/administration/utilisateurs-rh/", {
        method: "POST",
        body: JSON.stringify(member),
      });
      setMessage(data.message);
      setMember(emptyMember);
      load();
    } catch (requestError) {
      setError(requestError.message);
    }
  };

  // Active ou désactive un compte sans le supprimer.
  const toggleMember = async (user) => {
    try {
      await apiFetch(`/administration/utilisateurs-rh/${user.id}/`, {
        method: "PATCH",
        body: JSON.stringify({ actif: !user.actif }),
      });
      load();
    } catch (requestError) {
      setError(requestError.message);
    }
  };

  // Demande au backend de renvoyer les informations d'accès par e-mail.
  const resend = async (user) => {
    try {
      const data = await apiFetch(
        `/administration/utilisateurs-rh/${user.id}/renvoyer-acces/`,
        { method: "POST" },
      );
      setMessage(data.message);
    } catch (requestError) {
      setError(requestError.message);
    }
  };

  // La suppression est irréversible : une confirmation est donc demandée.
  const deleteMember = async (user) => {
    const displayName =
      `${user.prenom || ""} ${user.nom || ""}`.trim() || user.username;
    if (
      !window.confirm(
        `Supprimer définitivement le compte RH de ${displayName} ?\n\nCette personne ne pourra plus se connecter.`,
      )
    )
      return;
    setError("");
    try {
      await apiFetch(`/administration/utilisateurs-rh/${user.id}/`, {
        method: "DELETE",
      });
      setMessage(`Le compte RH de ${displayName} a été supprimé.`);
      await load();
    } catch (requestError) {
      setError(requestError.message);
    }
  };

  // Ajoute une salle et convertit la capacité saisie en nombre.
  const addRoom = async (event) => {
    event.preventDefault();
    try {
      await apiFetch("/salles/", {
        method: "POST",
        body: JSON.stringify({
          ...room,
          capacite: Number(room.capacite) || null,
        }),
      });
      setRoom(emptyRoom);
      setMessage("Salle ajoutée avec succès.");
      load();
    } catch (requestError) {
      setError(requestError.message);
    }
  };

  // Copie la salle sélectionnée dans un état séparé pour alimenter la modale.
  const openRoomEditor = (selectedRoom) =>
    setEditingRoom({
      ...selectedRoom,
      capacite: selectedRoom.capacite ?? "",
      localisation: selectedRoom.localisation || "",
      etage: selectedRoom.etage || "",
      description: selectedRoom.description || "",
    });

  // Envoie uniquement les champs modifiables de la salle au backend.
  const saveRoom = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = {
        ...editingRoom,
        capacite: Number(editingRoom.capacite) || null,
      };
      delete payload.id_salle;
      delete payload.date_creation;
      await apiFetch(`/salles/${editingRoom.id_salle}/`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      setEditingRoom(null);
      setMessage("Les informations de la salle ont été enregistrées.");
      await load();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSaving(false);
    }
  };

  // Une salle inactive reste dans l'historique mais n'est plus réservable.
  const toggleRoom = async (selectedRoom) => {
    try {
      await apiFetch(`/salles/${selectedRoom.id_salle}/`, {
        method: "PATCH",
        body: JSON.stringify({ active: !selectedRoom.active }),
      });
      setMessage(selectedRoom.active ? "Salle désactivée." : "Salle activée.");
      load();
    } catch (requestError) {
      setError(requestError.message);
    }
  };

  // Protection supplémentaire côté interface. Le backend vérifie aussi ce rôle.
  if (sessionStorage.getItem("role") !== "SUPER_ADMIN")
    return <Alert>Accès réservé au Super Administrateur.</Alert>;

  return (
    <>
      <PageHeader
        title="Administration"
        description="Gestion autonome des membres RH et des salles."
      />
      {error && <Alert onClose={() => setError("")}>{error}</Alert>}
      {message && <Alert onClose={() => setMessage("")}>{message}</Alert>}
      {loading ? (
        <Loading />
      ) : (
        <div className="space-y-6">
          <MembersSection
            users={users}
            member={member}
            setMember={setMember}
            addMember={addMember}
            toggleMember={toggleMember}
            resend={resend}
            deleteMember={deleteMember}
          />
          <RoomsSection
            rooms={rooms}
            room={room}
            setRoom={setRoom}
            addRoom={addRoom}
            editRoom={openRoomEditor}
            toggleRoom={toggleRoom}
          />
        </div>
      )}
      {editingRoom && (
        <RoomEditor
          room={editingRoom}
          setRoom={setEditingRoom}
          onClose={() => setEditingRoom(null)}
          onSave={saveRoom}
          saving={saving}
        />
      )}
    </>
  );
}

// Section responsable de la création et de la liste des comptes RH.
function MembersSection({
  users,
  member,
  setMember,
  addMember,
  toggleMember,
  resend,
  deleteMember,
}) {
  return (
    <section className="card p-5">
      <h2 className="mb-4 text-xl font-black">Gestion équipe RH</h2>
      <form
        onSubmit={addMember}
        className="mb-6 grid gap-3 md:grid-cols-2 xl:grid-cols-6"
      >
        <input
          className="field"
          placeholder="Nom"
          required
          value={member.nom}
          onChange={(e) => setMember({ ...member, nom: e.target.value })}
        />
        <input
          className="field"
          placeholder="Prénom"
          value={member.prenom}
          onChange={(e) => setMember({ ...member, prenom: e.target.value })}
        />
        <input
          className="field"
          placeholder="Utilisateur"
          required
          value={member.username}
          onChange={(e) => setMember({ ...member, username: e.target.value })}
        />
        <input
          className="field"
          type="email"
          placeholder="Email professionnel"
          required
          value={member.email}
          onChange={(e) => setMember({ ...member, email: e.target.value })}
        />
        <input
          className="field"
          type="password"
          autoComplete="new-password"
          minLength="8"
          placeholder="Mot de passe"
          required
          value={member.password}
          onChange={(e) => setMember({ ...member, password: e.target.value })}
        />
        <button className="btn-primary">
          <Plus size={16} />
          Ajouter
        </button>
      </form>
      <p className="mb-5 text-xs text-slate-500">
        Le mot de passe est défini par le Super Admin, chiffré par Django et
        n’est jamais retourné par l’API.
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Utilisateur</th>
              <th>Email</th>
              <th>Rôle</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr className="border-t" key={user.id}>
                <td className="py-3">
                  {user.prenom} {user.nom}
                </td>
                <td>{user.username}</td>
                <td>{user.email}</td>
                <td>{user.role}</td>
                <td>{user.actif ? "ACTIF" : "INACTIF"}</td>
                <td className="flex flex-wrap gap-2 py-2">
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => toggleMember(user)}
                  >
                    {user.actif ? "Désactiver" : "Activer"}
                  </button>
                  <button
                    type="button"
                    className="btn-secondary"
                    title="Renvoyer l’email"
                    onClick={() => resend(user)}
                  >
                    <Mail size={16} />
                  </button>
                  <button
                    type="button"
                    className="inline-flex items-center gap-2 rounded-xl border border-red-200 px-3 py-2 font-bold text-red-600 transition hover:bg-red-50"
                    onClick={() => deleteMember(user)}
                  >
                    <Trash2 size={16} />
                    Supprimer
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

// Section responsable de la création et de la liste des salles.
function RoomsSection({ rooms, room, setRoom, addRoom, editRoom, toggleRoom }) {
  return (
    <section className="card p-5">
      <h2 className="mb-4 text-xl font-black">Gestion des salles</h2>
      <form onSubmit={addRoom} className="mb-6 grid gap-3 md:grid-cols-5">
        <input
          className="field"
          placeholder="Nom"
          required
          value={room.nom_salle}
          onChange={(e) => setRoom({ ...room, nom_salle: e.target.value })}
        />
        <input
          className="field"
          placeholder="Localisation"
          value={room.localisation}
          onChange={(e) => setRoom({ ...room, localisation: e.target.value })}
        />
        <input
          className="field"
          placeholder="Étage"
          value={room.etage}
          onChange={(e) => setRoom({ ...room, etage: e.target.value })}
        />
        <input
          className="field"
          type="number"
          min="1"
          placeholder="Capacité"
          value={room.capacite}
          onChange={(e) => setRoom({ ...room, capacite: e.target.value })}
        />
        <button className="btn-primary">
          <Plus size={16} />
          Ajouter
        </button>
      </form>
      <div className="divide-y">
        {rooms.map((item) => (
          <div
            key={item.id_salle}
            className="flex flex-col justify-between gap-3 py-4 sm:flex-row sm:items-center"
          >
            <div>
              <b>{item.nom_salle}</b>
              <p className="text-xs text-slate-500">
                {item.localisation || "Localisation non renseignée"} ·{" "}
                {item.etage || "Étage non renseigné"} · {item.capacite || 0}{" "}
                places
              </p>
            </div>
            <div className="flex gap-2">
              <button className="btn-secondary" onClick={() => editRoom(item)}>
                <Edit3 size={16} />
                Modifier
              </button>
              <button
                className="btn-secondary"
                onClick={() => toggleRoom(item)}
              >
                {item.active ? "Désactiver" : "Activer"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// Fenêtre modale utilisée pour modifier une salle existante.
function RoomEditor({ room, setRoom, onClose, onSave, saving }) {
  const set = (field, value) => setRoom({ ...room, [field]: value });
  return (
    <div
      className="fixed inset-0 z-70 grid place-items-center bg-black/50 p-4"
      onMouseDown={onClose}
    >
      <form
        onSubmit={onSave}
        onMouseDown={(e) => e.stopPropagation()}
        className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-2xl"
      >
        <div className="mb-6 flex items-start justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Gestion des salles
            </p>
            <h2 className="mt-1 text-2xl font-black">Modifier la salle</h2>
          </div>
          <button
            type="button"
            className="rounded-lg p-2 hover:bg-slate-100"
            onClick={onClose}
          >
            <X />
          </button>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Nom de la salle *">
            <input
              className="field"
              required
              value={room.nom_salle}
              onChange={(e) => set("nom_salle", e.target.value)}
            />
          </Field>
          <Field label="Localisation">
            <input
              className="field"
              value={room.localisation}
              onChange={(e) => set("localisation", e.target.value)}
            />
          </Field>
          <Field label="Étage">
            <input
              className="field"
              value={room.etage}
              onChange={(e) => set("etage", e.target.value)}
            />
          </Field>
          <Field label="Capacité">
            <input
              className="field"
              type="number"
              min="1"
              value={room.capacite}
              onChange={(e) => set("capacite", e.target.value)}
            />
          </Field>
          <div className="sm:col-span-2">
            <Field label="Description et équipements">
              <textarea
                className="field min-h-28"
                value={room.description}
                onChange={(e) => set("description", e.target.value)}
              />
            </Field>
          </div>
          <label className="flex items-center gap-3 sm:col-span-2">
            <input
              type="checkbox"
              checked={room.active}
              onChange={(e) => set("active", e.target.checked)}
            />
            <span className="font-semibold">
              Salle active et disponible à la réservation
            </span>
          </label>
        </div>
        <div className="mt-7 flex justify-end gap-3">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Annuler
          </button>
          <button className="btn-primary" disabled={saving}>
            <Save size={17} />
            {saving ? "Enregistrement…" : "Enregistrer"}
          </button>
        </div>
      </form>
    </div>
  );
}

// Petit composant réutilisable pour garder les libellés de formulaire uniformes.
function Field({ label, children }) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      {children}
    </label>
  );
}
