import { useCallback, useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";
import { apiFetch } from "../lib/api";

export default function AppLayout() {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();
  const closeMenu = useCallback(() => setOpen(false), []);
  // Le tiroir se referme dès qu'on change de page.
  const [lastPath, setLastPath] = useState(pathname);
  if (lastPath !== pathname) { setLastPath(pathname); setOpen(false); }
  useEffect(() => {
    const keepSessionAlive = () => {
      if (document.visibilityState === "visible") {
        apiFetch("/me/").catch(() => {});
      }
    };
    const interval = window.setInterval(keepSessionAlive, 5 * 60 * 1000);
    document.addEventListener("visibilitychange", keepSessionAlive);
    return () => {
      window.clearInterval(interval);
      document.removeEventListener("visibilitychange", keepSessionAlive);
    };
  }, []);
  return (
    <div className="app-shell min-h-screen overflow-x-clip">
      <Sidebar open={open} onClose={closeMenu} />
      <div className="min-w-0 lg:pl-64">
        <Navbar onMenu={() => setOpen(true)} menuOpen={open} />
        <main className="mx-auto min-w-0 w-full max-w-375 p-3 sm:p-5 lg:p-8"><Outlet /></main>
      </div>
    </div>
  );
}
