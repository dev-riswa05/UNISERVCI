import { Navigate, Outlet, useLocation } from "react-router-dom";

export default function DisplayRoute() {
  const location = useLocation();
  if (!sessionStorage.getItem("token")) {
    return <Navigate to="/login" replace state={{ from: `${location.pathname}${location.search}` }} />;
  }
  if (sessionStorage.getItem("role") !== "AFFICHAGE") {
    return <Navigate to="/salles-vue" replace />;
  }
  return <Outlet />;
}
