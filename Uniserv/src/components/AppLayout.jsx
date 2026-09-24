import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";
import { apiFetch } from "../lib/api";

export default function AppLayout() {
  const [open, setOpen] = useState(false);
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
    <div className="app-shell min-h-screen">
      <Sidebar open={open} onClose={() => setOpen(false)} />
      <div className="min-w-0 lg:pl-64">
        <Navbar onMenu={() => setOpen(true)} />
        <main className="mx-auto min-w-0 w-full max-w-[1500px] p-3 sm:p-5 lg:p-8"><Outlet /></main>
      </div>
    </div>
  );
}
