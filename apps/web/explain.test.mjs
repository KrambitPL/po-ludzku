import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import test from "node:test";
import { analyze, commercialCard, familyCard, humanCard } from "./explain.mjs";

const root = new URL("../../", import.meta.url);
const identity = JSON.parse(readFileSync(new URL("./identity.json", new URL("../../packages/core/src/poludzku_core/", import.meta.url)), "utf8"));
const source = readFileSync(new URL("./explain.mjs", import.meta.url), "utf8");
const page = readFileSync(new URL("./index.html", import.meta.url), "utf8")
  + readFileSync(new URL("./page.mjs", import.meta.url), "utf8");

const TAX = `Urząd Skarbowy w Lublinie
Lublin, dnia 1 marca 2026 r.

Znak: US-LUB.123.2026

Wezwanie do zapłaty

Wzywa się do zapłaty kwoty 1 250,50 zł w terminie do dnia 15.04.2026.

W terminie 14 dni od dnia doręczenia niniejszego pisma można wnieść odwołanie.

Podstawa prawna: art. 15 ustawy z dnia 29 sierpnia 1997 r.
Telefon: 81 123 45 67
PESEL 00010100008
rachunek 00000000000000000000000000
`;

function python(text, delivery) {
  const script = `
import json, sys
from poludzku_core import analyze, commercial_card, family_card, human_card
text = sys.stdin.read()
delivery = sys.argv[1] or None
result = analyze(text, delivery=delivery)
print(json.dumps({"result": result, "human": human_card(result), "family": family_card(result), "commercial": commercial_card()}, ensure_ascii=False))
`;
  const raw = execFileSync("uv", ["run", "python", "-c", script, delivery || ""], {
    cwd: new URL(".", root),
    input: text,
    encoding: "utf8",
  });
  return JSON.parse(raw);
}

test("identity strings in the browser file match the vendor file", () => {
  for (const value of Object.values(identity)) {
    assert.equal(source.includes(value), true, value);
  }
  assert.equal(source.includes("Krambit"), false);
  assert.equal(page.includes("innerHTML"), false);
  assert.equal(page.includes("fetch("), false);
  assert.equal(page.includes("sendBeacon"), false);
  assert.equal(page.includes("connect-src 'none'"), true);
});

const CONSUMER = `Sklep Testowy
Reklamacja towaru odrzucona.

Wzywa się do zapłaty kwoty 50,00 zł do dnia 1.05.2026.
Telefon: 500 600 700
`;

const BAILIFF = `Komornik Sądowy przy Sądzie Rejonowym
Znak: KM 1/26

Wezwanie

W terminie 7 dni roboczych od dnia doręczenia należy zapłacić 10,00 zł.
W piśmie jest też słowo towar, bo dłużnik kupił towar.
`;

function same(text, delivery) {
  const js = analyze(text, { delivery: delivery || null });
  const py = python(text, delivery);
  assert.deepEqual(js, py.result);
  assert.equal(humanCard(js), py.human);
  assert.equal(familyCard(js), py.family);
}

test("browser engine matches Python", () => {
  same(TAX, "2026-03-10");
  same(CONSUMER);
  same(BAILIFF);
  assert.equal(commercialCard(), python(TAX).commercial);
  assert.equal(JSON.stringify(analyze(TAX)).includes("00010100008"), false);
});
