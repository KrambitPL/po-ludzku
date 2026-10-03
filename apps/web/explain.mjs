const DISCLAIMER =
  "To jest automat. Może się mylić. To nie jest pomoc prawna i nie zastępuje rozmowy z osobą, która może jej udzielić. Nic nie zostało wysłane.";

export const IDENTITY = {
  product: "Po ludzku",
  vendor: "KOD.AI sp. z o.o.",
  street: "ul. Frezerów 2",
  postal_city: "20-209 Lublin",
  krs: "0001218254",
  nip: "9462762849",
  regon: "543763281",
  email: "info@kodai.com.pl",
  phone: "+48 506 600 598",
  book: "https://book.kodai.com.pl",
  source_page: "https://kodai.com.pl/contact/",
};

const MONTHS = {
  stycznia: 1, lutego: 2, marca: 3, kwietnia: 4, maja: 5, czerwca: 6,
  lipca: 7, sierpnia: 8, września: 9, wrzesnia: 9, października: 10,
  pazdziernika: 10, listopada: 11, grudnia: 12,
};
const KINDS = [
  ["wezwanie_do_zaplaty", "wezwanie do zapłaty", ["wezwanie do zapłaty", "wezwanie do zaplaty"]],
  ["upomnienie", "upomnienie", ["upomnienie"]],
  ["postanowienie", "postanowienie", ["postanowienie"]],
  ["decyzja", "decyzja", ["decyzja"]],
  ["zawiadomienie", "zawiadomienie", ["zawiadomienie"]],
  ["uchwala", "uchwała", ["uchwała", "uchwala"]],
  ["wezwanie", "wezwanie", ["wezwanie"]],
];
const SENDER_HINTS = ["urząd", "urzad", "zus", "komornik", "sąd", "sad", "bank", "wspólnota", "wspolnota", "zarząd", "zarzad", "naczelnik", "zakład", "zaklad", "ubezpiecz"];
const CONSUMER = ["reklamacja", "sprzedawca", "rękojmi", "rekojmi", "zwrot towaru", "towar"];
const ENFORCEMENT = ["komornik", "egzekuc", "zajęcie", "zajecie", "tytuł wykonawczy", "tytul wykonawczy"];
const ZUS = ["zakład ubezpieczeń", "zaklad ubezpieczen"];
const TAX = ["urząd skarbowy", "urzad skarbowy", "urzędu skarbowego", "urzedu skarbowego", "administracja skarbowa"];
const MAX_CHARS = 200000;
const MIN_CHARS = 40;

function fold(text) {
  return text.toLowerCase();
}
function hasAny(text, needles) {
  const folded = fold(text);
  return needles.some((needle) => folded.includes(needle));
}
function word(text, value) {
  return new RegExp(`(?<![\\p{L}\\p{N}_])${value}(?![\\p{L}\\p{N}_])`, "iu").test(text);
}
function peselOk(digits) {
  if (!/^\d{11}$/.test(digits)) return false;
  const weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3];
  let total = 0;
  for (let i = 0; i < 10; i += 1) total += Number(digits[i]) * weights[i];
  return (10 - (total % 10)) % 10 === Number(digits[10]);
}
function subAll(text, patterns, mark, pred) {
  let count = 0;
  for (const pattern of patterns) {
    text = text.replace(pattern, (raw) => {
      const digits = raw.replace(/\D/g, "");
      if (pred && !pred(digits)) return raw;
      count += 1;
      return mark;
    });
  }
  return [text, count];
}
function redact(text) {
  const accounts = [
    /(?<!\d)\d{26}(?!\d)/g,
    /(?<!\d)\d{2}(?: \d{4}){6}(?!\d)/g,
    /(?<!\d)\d{2}(?:-\d{4}){6}(?!\d)/g,
    /(?<!\d)\d{2}(?: \d{2}){12}(?!\d)/g,
  ];
  const pesels = [/(?<!\d)\d{11}(?!\d)/g, /(?<!\d)\d(?: \d){10}(?!\d)/g, /(?<!\d)\d(?:-\d){10}(?!\d)/g];
  let [out, accountCount] = subAll(text, accounts, "[rachunek wycięty]");
  let peselCount;
  [out, peselCount] = subAll(out, pesels, "[PESEL wycięty]", peselOk);
  out = out.replace(/(?<!\d)\d{12,}(?!\d)/g, (digits) => {
    for (let start = 0; start <= digits.length - 11; start += 1) {
      if (peselOk(digits.slice(start, start + 11))) {
        peselCount += 1;
        return digits.slice(0, start) + "[PESEL wycięty]" + digits.slice(start + 11);
      }
    }
    return digits;
  });
  return [out, { pesel: peselCount, accounts: accountCount }];
}
// Unicode keeps every decimal digit set as a contiguous 0-9 run, so the value is the offset in the run.
function digitValue(char) {
  const code = char.codePointAt(0);
  let start = code;
  while (/\p{Nd}/u.test(String.fromCodePoint(start - 1))) start -= 1;
  return (code - start) % 10;
}
function validDate(year, month, day) {
  const value = new Date(Date.UTC(year, month - 1, day));
  if (value.getUTCFullYear() !== year || value.getUTCMonth() !== month - 1 || value.getUTCDate() !== day) return null;
  return `${year.toString().padStart(4, "0")}-${month.toString().padStart(2, "0")}-${day.toString().padStart(2, "0")}`;
}
function readable(text) {
  const stripped = text.trim();
  if (stripped.length < MIN_CHARS) return false;
  let bad = 0;
  let considered = 0;
  for (const char of stripped) {
    if (/\s/.test(char)) continue;
    considered += 1;
    if (char === "\ufffd") {
      bad += 1;
      continue;
    }
    if (!/[\p{L}\p{N}\p{P}\p{S}+#]/u.test(char)) bad += 1;
  }
  return considered > 0 && bad / considered <= 0.05;
}
function lineOf(text, needle) {
  const folded = fold(needle);
  for (const line of text.split("\n")) {
    if (fold(line).includes(folded)) {
      const clean = line.split(/\s+/).join(" ").trim();
      return clean ? clean.slice(0, 180) : null;
    }
  }
  return null;
}
function kindOf(text) {
  const folded = fold(text);
  for (const [id, label, phrases] of KINDS) {
    for (const phrase of phrases) {
      if (folded.includes(phrase)) return { id, label, quote: lineOf(text, phrase) };
    }
  }
  return null;
}
function senderOf(text) {
  const lines = text.split("\n").slice(0, 20);
  for (const line of lines) {
    const clean = line.split(/\s+/).join(" ").trim();
    if (!clean || clean.length > 120) continue;
    const folded = fold(clean);
    if (SENDER_HINTS.some((hint) => folded.includes(hint))) return clean;
  }
  return null;
}
function datesOf(text) {
  const found = [];
  const seen = new Set();
  for (const match of text.matchAll(/\b(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})(?!\d)/g)) {
    const iso = validDate(Number(match[3]), Number(match[2]), Number(match[1]));
    if (iso && !seen.has(iso)) {
      seen.add(iso);
      found.push({ iso, quote: match[0] });
    }
  }
  for (const match of text.matchAll(/\b(\d{4})-(\d{2})-(\d{2})(?!\d)/g)) {
    const iso = validDate(Number(match[1]), Number(match[2]), Number(match[3]));
    if (iso && !seen.has(iso)) {
      seen.add(iso);
      found.push({ iso, quote: match[0] });
    }
  }
  const months = Object.keys(MONTHS).join("|");
  for (const match of text.matchAll(new RegExp(`\\b(\\d{1,2})\\s+(${months})\\s+(\\d{4})(?!\\d)`, "gi"))) {
    const iso = validDate(Number(match[3]), MONTHS[fold(match[2])], Number(match[1]));
    if (iso && !seen.has(iso)) {
      seen.add(iso);
      found.push({ iso, quote: match[0] });
    }
  }
  return found;
}
function dateAt(text) {
  let match = text.match(/^(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})(?!\d)/);
  let iso = null;
  if (match) iso = validDate(Number(match[3]), Number(match[2]), Number(match[1]));
  else if ((match = text.match(/^(\d{4})-(\d{2})-(\d{2})(?!\d)/))) iso = validDate(Number(match[1]), Number(match[2]), Number(match[3]));
  else if ((match = text.match(new RegExp(`^(\\d{1,2})\\s+(${Object.keys(MONTHS).join("|")})\\s+(\\d{4})(?!\\d)`, "i")))) {
    iso = validDate(Number(match[3]), MONTHS[fold(match[2])], Number(match[1]));
  } else return null;
  return iso ? { iso, quote: match[0] } : null;
}
function letterDateOf(text) {
  let previous = "";
  for (const line of text.split("\n").slice(0, 15)) {
    const clean = line.split(/\s+/).join(" ").trim();
    if (!clean) continue;
    const header = clean.match(/^(?:[^\d,]{2,40}(?:,\s*|\s+(?=dnia\b)))?(?:dnia\s+|dn\.\s*)?(.+?)(?:\s*r(?:\.|oku)?)?$/id);
    ABSOLUTE_CUE.lastIndex = 0;
    const bare = header !== null && !header[0].slice(0, header.indices[1][0]).includes(",");
    const labelled = (bare && previous.endsWith(":")) || ABSOLUTE_CUE.test(`${previous} `);
    ABSOLUTE_CUE.lastIndex = 0;
    if (header && !labelled) {
      const found = dateAt(header[1]);
      if (found && found.quote === header[1]) return found;
    }
    previous = clean;
  }
  return null;
}
const WORD_DAYS = { jeden: 1, jednego: 1, dwa: 2, dwóch: 2, dwoch: 2, trzech: 3, trzy: 3, siedmiu: 7, siedem: 7, czternastu: 14, czternaście: 14, czternascie: 14, trzydziestu: 30, trzydzieści: 30, trzydziesci: 30, pięciu: 5, pieciu: 5, sześciu: 6, szesciu: 6, dziesięciu: 10, dziesieciu: 10, "dwudziestu jeden": 21, sześćdziesięciu: 60, szescdziesieciu: 60 };
const RELATIVE = new RegExp(
  `(?<![\\p{L}\\p{N}_])w (?:(?:(?:nieprzekraczalnym|ostatecznym|dodatkowym|wyznaczonym|zakreślonym|ustawowym|tym)\\s+)?terminie|ciągu)\\s+(?:(\\d{1,3}|${Object.keys(WORD_DAYS).map((key) => key.replace(" ", "\\s+")).join("|")})(?:\\s*\\([^)]{1,20}\\))?\\s+(dni|tygodni|miesięcy|miesiecy|miesiące|miesiace)(?![\\p{L}])|(?:jednego\\s+|jeden\\s+|1\\s+)?(tygodnia|miesiąca|miesiaca|(?<=(?:1|jeden|jednego)\\s)dnia(?!\\s+(?:miesiąca|miesiaca|każdego|kazdego))))(?:\\s+(kalendarzowych|roboczych|kalendarzowego|roboczego))?(?:\\s+od\\s+((?:(?!(?:nie później|nie pozniej|do dnia|w (?:(?:(?:nieprzekraczalnym|ostatecznym|dodatkowym|wyznaczonym|zakreślonym|ustawowym|tym)\\s+)?terminie|ciągu)\\s))(?:[0-9]\\.(?=[0-9])|[^.\\n;,])){3,80}))?`,
  "giu",
);
const ABSOLUTE_CUE = /(?:w terminie do|do dnia|nie później niż|nie pozniej niz|termin upływa|termin uplywa|termin płatności|termin platnosci|termin zapłaty|termin zaplaty|płatne do|platne do|płatna do|platna do|płatny do|platny do|płatność do|platnosc do|zapłata do|zaplata do|wpłata do|wplata do|zapłacić do|zaplacic do|wpłacić do|wplacic do)\s*:?\s+(?:up[łl]ywa\s+)?(?:z dniem\s+|dnia\s+)?/gi;
function deadlinesOf(text, delivery) {
  const items = [];
  for (const match of text.matchAll(RELATIVE)) {
    const [, count, plural, single, kindOfDays, anchorText] = match;
    const unit = fold(plural || single);
    const business = (kindOfDays || "").toLowerCase().startsWith("robocz");
    const folded = fold(anchorText || "");
    let anchor = "inny";
    if (folded.includes("doręcz") || folded.includes("dorecz") || folded.includes("otrzym")) anchor = "doreczenie";
    else if (folded.includes("niniejsz")) anchor = "data_pisma";
    let days = null;
    if (unit === "dni") days = /^\d+$/.test(count) ? Number(count) : WORD_DAYS[fold(count).split(/\s+/).join(" ")];
    else if (unit === "dnia") days = 1;
    let note;
    if (business) note = "Pismo mówi o dniach roboczych. Tych dni nie liczę.";
    else if (delivery && anchor === "doreczenie") {
      note = `Podałeś datę doręczenia ${delivery}. Nie liczę od niej terminu — sam policz, czy liczyć od tego dnia, czy od następnego.`;
    } else if (days === null) note = "Daty kalendarzowej nie liczę. W piśmie jest okres w tygodniach albo miesiącach.";
    else if (count === undefined || /^\d+$/.test(count)) note = "Daty kalendarzowej nie liczę. W piśmie jest tylko liczba dni.";
    else note = "Daty kalendarzowej nie liczę. W piśmie jest liczba dni słowem, nie cyfrą.";
    items.push({
      kind: "relative",
      quote: match[0].trim().split(/\s+/).join(" ").replace(/\s+(?:oraz|lub|albo|i|a)$/i, ""),
      days,
      business_days: business,
      anchor,
      calendar_date: null,
      note,
    });
  }
  const seenDates = new Set();
  for (const cue of text.matchAll(ABSOLUTE_CUE)) {
    const start = cue.index + cue[0].length;
    const found = dateAt(text.slice(start, start + 32));
    if (!found || seenDates.has(found.iso)) continue;
    seenDates.add(found.iso);
    items.push({
      kind: "absolute",
      quote: `${cue[0]}${found.quote}`.split(/\s+/).join(" "),
      days: null,
      business_days: false,
      anchor: "data_w_tekscie",
      calendar_date: found.iso,
      note: "Ta data jest w piśmie, przy słowie o terminie. Nie sprawdzałem, czy to na pewno ten termin.",
    });
  }
  return items;
}
function amountsOf(text) {
  const found = [];
  const seen = new Set();
  for (const match of text.matchAll(/(?<!\d)(\d{1,3}(?:[ \u00a0.]\d{3})+(?:,\d{2})?|\d+(?:,\d{2})?)\s*(zł|zl|pln)(?![a-z])/gi)) {
    const quote = match[0].split(/\s+/).join(" ");
    if (seen.has(quote)) continue;
    seen.add(quote);
    found.push({ quote, raw: match[1] });
  }
  return found;
}
function phonesOf(text) {
  const found = [];
  const seen = new Set();
  for (const match of text.matchAll(/(?:telefon|tel\.?|fax)\s*[:.]?\s*(\+48[\s-]?)?(\(?\d{2,3}\)?(?:[\s\-]\d{2,3}){2,3})/gi)) {
    const pretty = match[2].split(/\s+/).join(" ");
    if (seen.has(pretty)) continue;
    seen.add(pretty);
    found.push(pretty);
  }
  return found;
}
function quotesOf(text, pattern, limit) {
  const found = [];
  for (const match of text.matchAll(pattern)) {
    const quote = match[0].trim().split(/\s+/).join(" ").slice(0, 240);
    if (quote && !found.includes(quote)) found.push(quote);
    if (found.length >= limit) break;
  }
  return found;
}

function caseIdOf(text) {
  const match = text.match(/\b(?:znak sprawy|numer sprawy|nr sprawy|sygn\.?\s*akt|sygnatura|sygn\.|znak)\s*[:.]?\s*([A-Z0-9][A-Z0-9./\-]*(?:[ ]+[A-Z0-9][A-Z0-9./\-]*){0,5})/i);
  if (match) {
    const raw = match[1].split(/\.\s/)[0];
    const kept = [];
    for (const token of raw.split(/\s+/)) {
      const clean = token.replace(/[.,;]+$/g, "");
      if (!clean) continue;
      if (/\d|\//.test(clean) || kept.length === 0 || clean.length <= 2) kept.push(clean);
      else break;
    }
    if (kept.length) return kept.join(" ");
  }
  const km = text.match(/\bKM\s*\d+\/\d+\b/i);
  return km ? km[0].split(/\s+/).join(" ") : null;
}
function parseDelivery(value) {
  if (!value) return [null, false];
  const cleaned = value.trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(cleaned)) {
    const [year, month, day] = cleaned.split("-").map(Number);
    return validDate(year, month, day) ? [cleaned, false] : [null, true];
  }
  const dotted = cleaned.match(/^(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})$/);
  if (dotted) {
    const iso = validDate(Number(dotted[3]), Number(dotted[2]), Number(dotted[1]));
    return iso ? [iso, false] : [null, true];
  }
  return [null, true];
}

export function analyze(text, options = {}) {
  if (text == null) throw new Error("brak tekstu. wklej pismo.");
  if (text.length > MAX_CHARS) throw new Error("za długi tekst. wklej samo pismo, bez załączników.");
  text = text
    .normalize("NFC")
    .replace(/\r\n?|[\v\f\x85\u2028\u2029]/g, "\n")
    .replace(/[\u00a0\u2007\u2009\u202f]/g, " ")
    .replace(/[^\x00-\x7f]/gu, (char) => (/\p{Nd}/u.test(char) ? String(digitValue(char)) : char));
  if (!readable(text)) {
    throw new Error("Nie czytam skanu, zdjęcia ani pustego pliku. Przepisz: kto napisał, znak sprawy, datę, zdanie o terminie, kwotę i telefon z pisma.");
  }
  const [delivery, deliveryIgnored] = parseDelivery(options.delivery ?? null);
  const [redacted, stats] = redact(text);
  const kind = kindOf(redacted);
  const sender = senderOf(redacted);
  const caseId = caseIdOf(redacted);
  const dates = datesOf(redacted);
  const deadlines = deadlinesOf(redacted, delivery);
  const amounts = amountsOf(redacted);
  const phones = phonesOf(redacted);
  const legal = quotesOf(redacted, /[^.\n]{0,40}(?:art\.|ustawy|rozporządzen)[^.\n]{0,160}/gi, 3);
  const demand = quotesOf(redacted, /[^.\n]{0,40}(?:wzywa|zobowiązuje|zobowiazuje|należy zapłacić|nalezy zaplacic|wnosi się o zapłatę)[^.\n]{0,180}/gi, 1);
  const enforcement = hasAny(redacted, ["komornik", "egzekuc", "zajęcie", "zajecie", "zajęciu", "zajeciu", "zajęciem", "zajeciem", "zajęcia wynagrodzenia", "zajecia wynagrodzenia", "tytuł wykonawczy", "tytul wykonawczy"]);
  const zus = word(redacted, "zus") || hasAny(redacted, ["zakład ubezpiecze", "zaklad ubezpiecze", "zakładu ubezpiecze", "zakladu ubezpiecze"]);
  const tax = fold(redacted).includes("skarbow");
  const consumer = word(redacted, "towar") || hasAny(redacted, ["reklamacj", "sprzedawc", "rękojmi", "rekojmi"]);
  const unknown = [];
  if (!kind) unknown.push("nie rozpoznałem rodzaju pisma");
  if (!sender) unknown.push("nie widzę, kto pismo wysłał");
  if (!caseId) unknown.push("nie widzę znaku sprawy");
  if (!deadlines.length) unknown.push("nie widzę terminu");
  if (!amounts.length) unknown.push("nie widzę kwoty");
  if (!phones.length) unknown.push("nie widzę telefonu w tekście");
  if (!demand.length) unknown.push("nie widzę zdania, czego pismo żąda");
  return {
    disclaimer: DISCLAIMER,
    kind,
    sender,
    case_id: caseId,
    letter_date: letterDateOf(redacted),
    dates_found: dates,
    deadlines,
    amounts,
    phones_in_text: phones,
    legal_basis_quotes: legal,
    demand_quote: demand[0] || null,
    unknown,
    pesel_redacted: stats.pesel > 0,
    accounts_redacted: stats.accounts,
    enforcement,
    consumer_hotline: consumer && !enforcement && !zus && !tax
      ? {
          phones: ["801 440 220", "222 66 76 76"],
          hours: "dni robocze 10:00–18:00",
          tariff: "opłata według taryfy operatora",
          source: "https://uokik.gov.pl/pomoc-dla-konsumentow",
          note: "To pomoc przy sporze o zakup. Nie jest numerem z tego pisma.",
        }
      : null,
    delivery_given: delivery,
    delivery_ignored: deliveryIgnored,
  };
}

export function commercialCard() {
  return [
    "INFORMACJA HANDLOWA",
    "",
    IDENTITY.vendor,
    `${IDENTITY.street}, ${IDENTITY.postal_city}`,
    `KRS ${IDENTITY.krs}, NIP ${IDENTITY.nip}, REGON ${IDENTITY.regon}`,
    IDENTITY.email,
    IDENTITY.phone,
    "",
    "Po ludzku streszcza pismo, które już masz. Jest darmowe. Nie wysyła go nigdzie.",
    "Jeśli w firmie utykacie na poczcie wpływającej, można o tym porozmawiać:",
    IDENTITY.book,
    "",
    "Tej kartki nie wysyłamy za Ciebie. Skopiuj ją sam, jeśli chcesz.",
    "Nie dołączaj do niej swojego pisma. Nie przysyłaj pisma na ten adres.",
  ].join("\n");
}

function familyDemand(analysis) {
  const quote = analysis.demand_quote;
  if (!quote) return null;
  const folded = quote.toLowerCase();
  if (["ul.", "ulica", "al.", "aleja", "osiedle"].some((token) => folded.includes(token))) return null;
  if (/\d{2}[-\u2013]\d{3}|\d{11,}/.test(quote)) return null;
  return quote;
}

export function familyCard(analysis) {
  const lines = [
    "Kartka do rodziny. Możesz ją skopiować.",
    "Nie ma tu PESEL ani numeru rachunku. To nie jest porada. Nic nie zostało wysłane.",
    "",
    `Rodzaj: ${analysis.kind ? analysis.kind.label : "nie wiem"}`,
    `Kto napisał: ${analysis.sender || "nie wiem"}`,
    `Znak: ${analysis.case_id || "nie wiem"}`,
  ];
  const deadlines = analysis.deadlines || [];
  if (!deadlines.length) lines.push("Termin: nie widzę go w tekście");
  else {
    lines.push("Terminy, cytat z pisma:");
    for (const item of deadlines) {
      lines.push(`- ${item.quote}`);
      lines.push(`  ${item.note}`);
    }
  }
  const phones = analysis.phones_in_text || [];
  lines.push(phones.length ? `Telefon zapisany w piśmie: ${phones.join(", ")}` : "Telefonu w tekście nie znalazłem. Nie podaję numeru z głowy.");
  const demand = familyDemand(analysis);
  if (demand) lines.push(`Czego żąda, cytat: ${demand}`);
  if (analysis.enforcement) {
    lines.push("To wygląda jak pismo komornicze albo egzekucyjne. Tu jest tylko opis. Nie ma instrukcji, co robić wobec zajęcia.");
  }
  if ((analysis.unknown || []).length) lines.push(`Czego nie znalazłem: ${analysis.unknown.join("; ")}.`);
  lines.push("", DISCLAIMER);
  return lines.join("\n");
}

function draft(analysis) {
  const bits = ["nawiązuję do pisma"];
  if (analysis.letter_date) bits.push(`z dnia ${analysis.letter_date.quote}`);
  if (analysis.case_id) bits.push(`znak ${analysis.case_id}`);
  return [
    "Szkic do własnej edycji. Nic nie zostało wysłane.",
    "To nie jest pismo do sądu i nie jest pomocą prawną.",
    "",
    "Szanowni Państwo,",
    "",
    `${bits.join(" ")}.`,
    "",
    "[Tu napisz jednym zdaniem, o co prosisz. Automat tego nie wpisuje.]",
    "",
    "Proszę o pisemną odpowiedź.",
    "",
    "[imię]",
    "[adres do odpowiedzi]",
  ].join("\n");
}

export function humanCard(analysis) {
  const lines = [analysis.disclaimer, ""];
  lines.push(`Rodzaj: ${analysis.kind ? analysis.kind.label : "nie rozpoznałem"}`);
  if (analysis.kind?.quote) lines.push(`Cytat: ${analysis.kind.quote}`);
  lines.push(`Kto napisał: ${analysis.sender || "nie widzę"}`);
  lines.push(`Znak sprawy: ${analysis.case_id || "nie widzę"}`);
  if (analysis.letter_date) lines.push(`Data pisma: ${analysis.letter_date.quote}`);
  const dates = analysis.dates_found || [];
  lines.push(dates.length
    ? `Daty znalezione w tekście (to nie znaczy, że to termin): ${dates.map((item) => item.quote).join(", ")}`
    : "Daty w tekście: nie widzę");
  lines.push("", "Terminy:");
  const deadlines = analysis.deadlines || [];
  if (!deadlines.length) lines.push("- nie widzę terminu. Nie wymyślam daty.");
  for (const item of deadlines) {
    lines.push(`- ${item.quote} (${item.calendar_date || "bez daty kalendarzowej"})`);
    lines.push(`  ${item.note}`);
  }
  lines.push("");
  const amounts = analysis.amounts || [];
  if (amounts.length) {
    lines.push("Kwoty zapisane w tekście. Nie wiem, która jest do zapłaty:");
    for (const item of amounts) lines.push(`- ${item.quote}`);
  } else lines.push("Kwoty: nie widzę");
  const phones = analysis.phones_in_text || [];
  lines.push(phones.length ? `Telefon z pisma: ${phones.join(", ")}` : "Telefonu w piśmie nie ma. Nie podaję innego.");
  if (analysis.demand_quote) lines.push(`Czego żąda, cytat: ${analysis.demand_quote}`);
  if ((analysis.legal_basis_quotes || []).length) {
    lines.push("Podstawa, cytat, bez oceny:");
    for (const quote of analysis.legal_basis_quotes) lines.push(`- ${quote}`);
  }
  if (analysis.pesel_redacted) lines.push("Wyciąłem numer, który wygląda jak PESEL. Został tylko w tekście, który wkleiłeś.");
  if (analysis.accounts_redacted) lines.push("Wyciąłem numer rachunku. Został tylko w tekście, który wkleiłeś.");
  if (analysis.enforcement) {
    lines.push("To wygląda jak pismo komornicze albo egzekucyjne. Pokazuję, co jest w tekście. Nie podpowiadam, jak zachować się wobec zajęcia.");
  }
  if (analysis.consumer_hotline) {
    const hotline = analysis.consumer_hotline;
    lines.push(`Spór o zakup: ${hotline.phones.join(" i ")}, ${hotline.hours}, ${hotline.tariff}.`);
    lines.push(hotline.note);
  }
  if ((analysis.unknown || []).length) {
    lines.push("");
    lines.push(`Czego nie znalazłem: ${analysis.unknown.join("; ")}.`);
  }
  if (analysis.delivery_given) lines.push(`Data doręczenia, którą podałeś: ${analysis.delivery_given}.`);
  if (analysis.delivery_ignored) lines.push("Daty doręczenia nie rozumiem, więc jej nie używam. Kartka jest z samego pisma.");
  lines.push("", "--- szkic ---", draft(analysis), "--- koniec szkicu ---");
  lines.push("", "--- do skopiowania rodzinie ---", familyCard(analysis), "--- koniec kartki dla rodziny ---");
  return lines.join("\n");
}
