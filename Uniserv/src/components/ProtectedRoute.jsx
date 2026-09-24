import { Navigate, Outlet, useLocation } from "react-router-dom";

export default function ProtectedRoute() {
  const location = useLocation();
  // Cette garde améliore l'expérience côté React. La sécurité réelle reste
  // assurée par IsAuthenticated dans Django pour chaque endpoint privé.
  if (!sessionStorage.getItem("token")) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (sessionStorage.getItem("role") === "AFFICHAGE") {
    return <Navigate to="/affichage" replace />;
  }
  return <Outlet />;
}
