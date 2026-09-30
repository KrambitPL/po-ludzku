import { IDENTITY, analyze, commercialCard, familyCard, humanCard } from "./explain.mjs";

const letter = document.querySelector("#letter");
const delivery = document.querySelector("#delivery");
const out = document.querySelector("#out");
const copy = document.querySelector("#copy");
document.querySelector("#ad").textContent = commercialCard();
document.querySelector("#who").textContent =
  `${IDENTITY.vendor}, ${IDENTITY.street}, ${IDENTITY.postal_city}. KRS ${IDENTITY.krs}, NIP ${IDENTITY.nip}, REGON ${IDENTITY.regon}. ${IDENTITY.email}. ${IDENTITY.phone}. Skarga: napisz na ten adres.`;

let family = "";
document.querySelector("#go").addEventListener("click", () => {
  family = "";
  copy.hidden = true;
  try {
    const value = delivery.value.trim();
    const result = analyze(letter.value, { delivery: value || null });
    out.hidden = false;
    out.textContent = humanCard(result);
    family = familyCard(result);
    copy.hidden = false;
  } catch (error) {
    out.hidden = false;
    out.textContent = error instanceof Error ? error.message : "nie czytam tego. wklej tekst.";
  }
});
copy.addEventListener("click", async () => {
  if (!family) return;
  try {
    await navigator.clipboard.writeText(family);
    copy.textContent = "Skopiowane. Wyślij sam, jeśli chcesz.";
  } catch {
    copy.textContent = "Nie skopiowałem. Zaznacz kartkę sam.";
  }
});
