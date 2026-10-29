// Nom du produit : « Ma » en léger, « Salle » en gras, dans une police
// géométrique (Montserrat) proche de celle du mot UNISERV. La taille est donnée
// par `className`. Les couleurs viennent de la charte UNISERV (voir index.css).
export default function AppName({ light = false, className = "" }) {
  return (
    <span
      className={`app-name ${light ? "app-name--light" : ""} ${className}`}
      aria-label="MaSalle"
    >
      <span aria-hidden="true">Ma</span>
      <b aria-hidden="true">Salle</b>
    </span>
  );
}
