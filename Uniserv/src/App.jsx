import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import AppLayout from "./components/AppLayout";
import Login from "./pages/login";
import Dashboard from "./pages/dashboard";
import Planning from "./pages/Planning";
import Reservations from "./pages/Reservations";
import ReservationForm from "./pages/ReservationForm";
import ReservationDetails from "./pages/ReservationDetails";
import Rooms from "./pages/Rooms";
import NotFound from "./pages/NotFound";
import AffichageSalles from "./pages/AffichageSalles";
import DisplayRoute from "./components/DisplayRoute";
import Administration from "./pages/Administration";
import MyProfile from "./pages/MyProfile";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        {/* Route tablette authentifiée, sans layout ni menu RH. */}
        <Route element={<DisplayRoute />}>
          <Route path="/affichage" element={<AffichageSalles />} />
        </Route>
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/planning" element={<Planning />} />
            <Route path="/salles" element={<Rooms />} />
            <Route path="/salles-vue" element={<AffichageSalles />} />
            <Route path="/administration" element={<Administration />} />
            <Route path="/mon-profil" element={<MyProfile />} />
            <Route path="/reservations" element={<Reservations />} />
            <Route path="/reservations/nouvelle" element={<ReservationForm />} />
            <Route path="/reservations/:id" element={<ReservationDetails />} />
            <Route path="/reservations/:id/modifier" element={<ReservationForm />} />
            <Route path="/404" element={<NotFound />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to={!sessionStorage.getItem("token") ? "/login" : sessionStorage.getItem("role") === "AFFICHAGE" ? "/affichage" : "/404"} replace />} />
      </Routes>
    </BrowserRouter>
  );
}
