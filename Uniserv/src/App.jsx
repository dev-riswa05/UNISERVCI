import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import AppLayout from "./components/AppLayout";
import Home from "./pages/Home";
import Dashboard from "./pages/dashboard";
import Planning from "./pages/Planning";
import Reservations from "./pages/Reservations";
import ReservationForm from "./pages/ReservationForm";
import ReservationDetails from "./pages/ReservationDetails";
import Rooms from "./pages/Rooms";
import NotFound from "./pages/NotFound";
import AffichageSalles from "./pages/AffichageSalles";
import Administration from "./pages/Administration";
import MyProfile from "./pages/MyProfile";
import { homeForRole } from "./lib/session";

const STAFF = ["SUPER_ADMIN", "RH"];

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Navigate to="/" replace />} />
        {/* Écran d'affichage public : aucun token requis. */}
        <Route path="/affichage" element={<AffichageSalles />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            {/* Routes communes aux trois rôles. */}
            <Route path="/planning" element={<Planning />} />
            <Route path="/salles-vue" element={<AffichageSalles />} />
            <Route path="/mon-profil" element={<MyProfile />} />
            <Route path="/reservations" element={<Reservations />} />
            <Route path="/reservations/nouvelle" element={<ReservationForm />} />
            <Route path="/reservations/:id" element={<ReservationDetails />} />
            <Route path="/reservations/:id/modifier" element={<ReservationForm />} />
            <Route path="/404" element={<NotFound />} />
            {/* Réservé au Super Admin et à l'équipe RH. */}
            <Route element={<ProtectedRoute allowedRoles={STAFF} />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/salles" element={<Rooms />} />
            </Route>
            <Route element={<ProtectedRoute allowedRoles={["SUPER_ADMIN"]} />}>
              <Route path="/administration" element={<Administration />} />
            </Route>
          </Route>
        </Route>
        <Route
          path="*"
          element={<Navigate to={sessionStorage.getItem("token") ? homeForRole(sessionStorage.getItem("role")) : "/"} replace />}
        />
      </Routes>
    </BrowserRouter>
  );
}
