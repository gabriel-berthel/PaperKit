import { convert_all_footnotes_to_bullet, run_all_annotations} from "./marking/annotation.js";
import { initSelectionToolbar } from './actions/selection.js'
import { initBlockActions } from './actions/blocks.js'
import { initSpanActions } from './actions/spans.js'
import { initMediaPopup } from "./actions/medias.js";
import { initCallouts } from "./marking/callouts.js";
import { initSnapshots } from './dom/snapshots.js';
import { initTTS } from './tts/player.js'
import { initExplorer } from "./dom/explorer.js";

document.addEventListener('DOMContentLoaded', async () => {
  
  initExplorer()
  initSpanActions()
  initSelectionToolbar()
  initBlockActions()
  initMediaPopup()
  initCallouts()
  initTTS() 

  document.querySelectorAll('[data-type="paragraph"]').forEach(el => {
    let t = el.innerHTML;
    t = run_all_annotations(t);
    el.innerHTML = t;
  })

  document.querySelectorAll('[data-type="bullet"]').forEach(el => {
    let t = el.innerHTML;
    t = run_all_annotations(t);
    el.innerHTML = t;
  })

  document.querySelectorAll('[data-type="caption"]').forEach(el => {
    let t = el.innerHTML;
    t = run_all_annotations(t);
    el.innerHTML = t;
  })


  document.querySelectorAll('[data-type="formula"]').forEach(el => {
    const og = el.innerText;
    el.innerText = `$$ ${el.innerText} $$`;
    el.dataset.latex = og;

    
  })

  document.querySelectorAll('[data-type="footnote"]').forEach(el => {
    let t = el.innerHTML;
    t = run_all_annotations(t);
    el.innerHTML = t;
  })

  renderMathInElement(document.body, {
      delimiters: [
          { left: '$$', right: '$$', display: true,       output: 'html',     }
      ]
  });


  convert_all_footnotes_to_bullet()
  initSnapshots()
})