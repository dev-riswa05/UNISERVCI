export default function BrandLogo({
  compact = false,
  light = false,
  className = "",
}) {
  // Ce composant centralise le logo afin d'éviter de répéter son HTML
  // dans la barre latérale, la connexion et l'écran d'affichage.
  return (
    <div
      className={`brand-logo ${compact ? "brand-logo--compact" : ""} ${light ? "brand-logo--light" : ""} ${className}`}
    >
      <img src="/uniserv-emblem.png" alt="" className="brand-logo__emblem" />
      {!compact && (
        <div className="brand-logo__wordmark" aria-label="UNISERV BTP">
          <span>UNISERV</span>
          <small>
            B<br />T<br />P
          </small>
        </div>
      )}
    </div>
  );
}
