// Horaires d'ouverture communs à tous les formulaires du frontend.
export const OPENING_TIME = "08:00";
export const CLOSING_TIME = "17:30";
export const TIME_STEP_SECONDS = 1800;

// La liste commune garantit que les deux écrans proposent exactement les
// mêmes créneaux de 30 minutes, sans saisie manuelle possible.
export const TIME_OPTIONS = Array.from({ length: 20 }, (_, index) => {
  const totalMinutes = (8 * 60) + (index * 30);
  const hours = String(Math.floor(totalMinutes / 60)).padStart(2, "0");
  const minutes = String(totalMinutes % 60).padStart(2, "0");
  return `${hours}:${minutes}`;
});

export const START_TIME_OPTIONS = TIME_OPTIONS.slice(0, -1);

export function formatTimeOption(value) {
  return value.replace(":", "h");
}

export function isSlotWithinOpeningHours(start, end) {
  return Boolean(
    start
    && end
    && start >= OPENING_TIME
    && end <= CLOSING_TIME
    && start < end
  );
}
