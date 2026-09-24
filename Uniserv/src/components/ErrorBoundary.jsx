import { Component } from "react";

export default class ErrorBoundary extends Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    // Le détail reste disponible pour le diagnostic sans être montré à
    // l'utilisateur final.
    console.error("Erreur d'affichage React", error, info);
  }

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <main className="grid min-h-screen place-items-center bg-slate-100 p-5">
        <section className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-lg">
          <p className="text-sm font-bold uppercase tracking-wider text-slate-400">UNISERV BTP</p>
          <h1 className="mt-3 text-2xl font-black text-slate-900">La page n’a pas pu s’afficher</h1>
          <p className="mt-3 text-sm leading-relaxed text-slate-600">
            Votre session est toujours active. Rechargez simplement l’interface pour continuer.
          </p>
          <button className="btn-primary mt-6" onClick={() => window.location.reload()}>
            Recharger la page
          </button>
        </section>
      </main>
    );
  }
}
