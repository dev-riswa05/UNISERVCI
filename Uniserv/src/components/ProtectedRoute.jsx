import { Navigate, Outlet, useLocation } from "react-router-dom";
import { homeForRole } from "../lib/session";

export default function ProtectedRoute({ allowedRoles }) {
  const location = useLocation();
  const role = sessionStorage.getItem("role");
  // Cette garde améliore l'expérience côté React. La sécurité réelle reste
  // assurée par les permissions Django pour chaque endpoint privé.
  if (!sessionStorage.getItem("token")) {
    return <Navigate to="/" replace state={{ from: location.pathname }} />;
  }
  if (allowedRoles && !allowedRoles.includes(role)) {
    return <Navigate to={homeForRole(role)} replace />;
  }
  return <Outlet />;
}
