import { STOP_WORDS } from './stopwords.js';

export const REF_BRACKET_RE = /\s\[\d+(?:\s*[-–,]\s*\d+)*\]/g;

export const IN_TEXT_AUTHOR_YEAR =
  /(?:[A-Z][A-Za-z'`-]+(?:,\s*[A-Z][A-Za-z'`-]+)*(?:\s+(?:and|&)\s+[A-Z][A-Za-z'`-]+)?(?:\s+et al\.)?)\s*\(\d{4}[a-z]?\)/g;

export const IN_TEXT_AUTHOR_ETAL = /[A-Z][A-Za-z'`-]+\s+et al\./g;

export const AUTHOR_YEAR_RE = /\([^()]*?[A-Z][^()]+?\d{4}[a-z]?[^()]*?\)/g;

const stopWordPattern = [...STOP_WORDS].map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
export const STOP_WORD_REF = new RegExp(
  `(?:\\b(?:${stopWordPattern})\\b)\\s+(${AUTHOR_YEAR_RE.source}|${REF_BRACKET_RE.source})`,
  'gi'
);

const IDENTIFIERS = [
  "table","figure","section","equation",
  "appendix","algorithm","references","footnote","page", 
  "definition", "theorem", "lemma", "proposition", "corollary"
];

const NUM   = String.raw`(?:\d+(?:\.\d+)*|[A-Za-z])`;
const RANGE = `${NUM}(?:-${NUM})?`;
const LIST  = `${RANGE}(?:\\s*(?:,|and|or)\\s*${RANGE})*`;
export const REF_RE = new RegExp(
  `\\b(${IDENTIFIERS.join('|')})\\s+(${LIST})\\b`,
  'gi'
);