import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";
import AppName from "./AppName";

// Le logo UNISERV et le nom du produit forment un seul bloc : MaSalle est
// placé sous le logo et en fait partie. Tous les écrans qui affichent le logo
// affichent donc le nom automatiquement. Les éléments sont des <span> pour que
// le composant reste valide à l'intérieur d'un titre (<h1>).
export default function BrandLogo({
  compact = false,
  light = false,
  showName = true,
  nameClassName = "text-2xl",
  className = "",
  to = "",
  onClick,
}) {
  const lockup = (
    <span className={`brand-lockup ${className}`}>
      <span
        className={`brand-logo ${compact ? "brand-logo--compact" : ""} ${light ? "brand-logo--light" : ""}`}
      >
        <img src="/uniserv-emblem.png" alt="" className="brand-logo__emblem" />
        {/* Au survol (ou au focus clavier), l'emblème laisse place à une flèche de retour. */}
        {to && (
          <span className="brand-logo__back" aria-hidden="true">
            <ArrowLeft size="58%" strokeWidth={2.6} />
          </span>
        )}
        {!compact && (
          <span className="brand-logo__wordmark" aria-label="UNISERV BTP">
            <span>UNISERV</span>
            <small>
              B<br />T<br />P
            </small>
          </span>
        )}
      </span>
      {showName && (
        <AppName
          light={light}
          className={`brand-lockup__name ${nameClassName}`}
        />
      )}
    </span>
  );
  // Avec `to`, le logo devient un lien : un clic ramène à l'accueil.
  if (!to) return lockup;
  return (
    <Link
      to={to}
      onClick={onClick}
      className="brand-link"
      title="Retour à l'accueil"
      aria-label="MaSalle, UNISERV BTP : retour à l'accueil"
    >
      {lockup}
    </Link>
  );
}
