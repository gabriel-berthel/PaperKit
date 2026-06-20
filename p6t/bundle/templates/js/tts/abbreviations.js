
const ABBREVIATIONS = {
  "i.e.": "that is",
  "e.g.": "for example",
  "etc.": "et cetera",
  "vs.": "versus",
  "approx.": "approximately",
  "dept.": "department",
  "est.": "established",
  "fig.": "figure",
  "no.": "number",
  "vol.": "volume",
  "id.": "the same",
  "cf.": "compare",
  "viz.": "namely",
  "a.k.a.": "also known as",
  "i.": "I",
};

export function expandAbbreviations(text) {
  let out = text;

  // normalize spaced-out forms: "i. e." -> "i.e.", "e. g." -> "e.g."
  out = out.replace(/\b([a-zA-Z])\.\s+(?=[a-zA-Z]\.)/g, "$1.");

  for (const [abbr, full] of Object.entries(ABBREVIATIONS)) {
    const escaped = abbr.replace(/\./g, "\\.");
    const re = new RegExp(`\\b${escaped}(?=\\s|,|$)`, "gi");
    out = out.replace(re, full);
  }

  return out;
}
