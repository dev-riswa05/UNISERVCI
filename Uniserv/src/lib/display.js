export function meetingStatus(meeting, currentTime) {
  if (currentTime < meeting.heure_debut) return "À venir";
  if (currentTime < meeting.heure_fin) return "En cours";
  return "Terminée";
}

export function roomSchedule(room, reservations, currentTime) {
  const meetings = reservations.filter(
    (meeting) => Number(meeting.id_salle) === Number(room.id_salle)
  );

  return {
    currentTime,
    meetings,
    current: meetings.find(
      (meeting) => currentTime >= meeting.heure_debut
        && currentTime < meeting.heure_fin
    ),
    next: meetings.find((meeting) => currentTime < meeting.heure_debut),
  };
}

export function countdownLabel(schedule) {
  const target = schedule.current?.heure_fin || schedule.next?.heure_debut;
  if (!target) return "Aucune autre réservation aujourd’hui";
  const seconds = (value) => { const [h, m, s = 0] = value.slice(0, 8).split(":").map(Number); return h * 3600 + m * 60 + s; };
  const remaining = Math.max(0, seconds(target) - seconds(schedule.currentTime));
  const hours = Math.floor(remaining / 3600);
  const minutes = Math.floor((remaining % 3600) / 60);
  const secs = remaining % 60;
  const value = `${hours ? `${hours} h ` : ""}${String(minutes).padStart(2, "0")} min ${String(secs).padStart(2, "0")} s`;
  return schedule.current ? `Fin dans ${value}` : `Disponible pendant ${value}`;
}

function timeInSeconds(value) {
  const [hours, minutes, seconds = 0] = value.slice(0, 8).split(":").map(Number);
  return hours * 3600 + minutes * 60 + seconds;
}

function durationLabel(totalSeconds) {
  const remaining = Math.max(0, totalSeconds);
  const hours = Math.floor(remaining / 3600);
  const minutes = Math.floor((remaining % 3600) / 60);
  const seconds = remaining % 60;
  return `${hours ? `${hours} h ` : ""}${String(minutes).padStart(2, "0")} min ${String(seconds).padStart(2, "0")} s`;
}

export function meetingCountdown(meeting, currentTime) {
  const now = timeInSeconds(currentTime);
  const start = timeInSeconds(meeting.heure_debut);
  const end = timeInSeconds(meeting.heure_fin);
  if (now < start) return `Commence dans ${durationLabel(start - now)}`;
  if (now < end) return `Se termine dans ${durationLabel(end - now)}`;
  return `Terminée depuis ${durationLabel(now - end)}`;
}
