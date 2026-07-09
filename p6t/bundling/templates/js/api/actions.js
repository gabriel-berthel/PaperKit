import {ENDPOINTS, request} from "./utils.js";

export const MODES = {
  EXPERT:  'expert',
  STUDENT: 'student',
  MATHS:   'maths',
  FORMULA: 'formula',
  WORDING: 'wording',
  CAPTION: 'caption',
  CODE: 'code'
}

export async function SREConvertion(text) {
  const mathml = katex.renderToString(text, { output: 'mathml' });
  const wrapper = document.createElement('div');
  wrapper.innerHTML = mathml;
  wrapper.querySelectorAll('annotation').forEach(n => n.remove());
  const cleanMathml = wrapper.querySelector('math').outerHTML;
  const res = await SRE.toSpeech(cleanMathml, { modality: 'speech', domain: 'clearspeak', semantics: true });
  return res;
}


export function simplify(text, mode) {
  return request(`${ENDPOINTS.SIMPLIFY}/${mode}`, {
    method: "POST",
    payload: { 'text': text }
  });
}

export function summarize(text) {
  return request(ENDPOINTS.SUMMARIZE, {
    method: "POST",
    payload: { 'text': text }
  });
}


export function fetchWhatIsIt(term, context) {
  return request(ENDPOINTS.WHAT_IS_IT, {
    method: "POST",
    payload:{ 'term': term, 'context': context },
  });
}
