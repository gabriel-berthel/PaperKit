import json

from ollama import AsyncClient
from pylatexenc.latex2text import LatexNodes2Text

from p6t.tools.bootsrap import init_llama32

init_llama32()

texer = LatexNodes2Text()


async def ask_llm(system: str, user: str):

    response = await AsyncClient().chat(
        model='llama3.2', 
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        format="json",
        options={
            'num_ctx': 32768, # up to 2^17
            'temperature': 0,
            'top_p':  1,
            'top_k': 1,
            'repeat_penalty': 1.00,
            'num_predict':  -1,
        }
    )

    try:
        return json.loads(response.message.content)
    except Exception:
        return {"error": "Invalid LLM response", "raw": response}


async def llm_simple_task(user, instr: str):
    
    system = f"""
    [Task] {instr}
    
    [Requirements]
    - Put tasks output in the "output" field
    - Only use the "remark" field if strictly necessary
    
    
    [Format]
    {{
        "output": "",
        "remark": ""
    }}

    """
     
    response = await ask_llm(system, user)
    return response.get('output', None)


async def llm_simplify_text(text: str, level: str):
    
    simplify = f"""
    [Task] Rewrite the given text in simpler English.

    [Requirements]
    - Simplify unnecessary jargon and replace pompous terms with plain language
    - Make text accessible to **ESL {level}** students
    - Preserve structure and domain terminology (**assume familiarity** with the field)
    - Use simple, consistent verb tenses (prefer simple present or past; avoid complex tense forms when not necessary)
    - Prefer natural, spoken English style over formal or academic phrasing
    - Do not add any extra explanation
    - Only use the "remark" field if strictly necessary
    - Embed math expressions into natural language where necessary (focus on readability)

    [Format]
    {{
        "output": "",
        "remark": ""
    }}
    """
    
    response = await ask_llm(simplify, text)
    
    return response.get('output', "")

async def llm_explain_term(term: str, context: str, search_result: str | None):
    """
    Validate or correct a dictionary/Wikipedia definition for a selected term,
    using the surrounding paragraph as disambiguation context.

    Args:
        term: the selected text/phrase the user wants explained
        context: the full paragraph the term appears in
        search_result: a candidate definition (WordNet gloss or Wikipedia summary),
                        or None if no result was found
    """

    if search_result:
        prompt = f"""
[Task] You are given a TERM, the PARAGRAPH it appears in, and a CANDIDATE DEFINITION
retrieved from a dictionary or encyclopedia.

[Requirements]
- Check if the CANDIDATE DEFINITION matches the meaning of TERM as used in PARAGRAPH
- If it is correct and fits the context, return it (lightly cleaned up if needed)
- If it is wrong, ambiguous, or for a different sense of the word, REWRITE it so
  it correctly explains TERM as used in this PARAGRAPH
- Keep the explanation short (1-2 sentences)
- Use simple, plain English
- Do not add extra commentary or meta-remarks about the correction
- Set "corrected" to true ONLY if you made a significant change in meaning
  (e.g. fixed wrong word sense, wrong topic, factual error). Minor wording/style
  cleanup that doesn't change the meaning should be "corrected": false
- Only use the "remark" field if strictly necessary (e.g. to flag remaining uncertainty)

[Format]
{{
    "output": "",
    "corrected": false,
    "remark": ""
}}

[TERM]
{term}

[PARAGRAPH]
{context}

[CANDIDATE DEFINITION]
{search_result}
"""
    else:
        prompt = f"""
[Task] No dictionary or encyclopedia definition was found for TERM.
Explain TERM as it is used in PARAGRAPH.

[Requirements]
- Give a short (1-2 sentence) explanation of what TERM means in this context
- Use simple, plain English
- Do not add extra commentary or meta-remarks
- Set "corrected" to true (since no candidate existed, this is a new explanation)
- Only use the "remark" field if strictly necessary

[Format]
{{
    "output": "",
    "corrected": false,
    "remark": ""
}}

[TERM]
{term}

[PARAGRAPH]
{context}
"""

    response = await ask_llm(prompt, "")
    return {
        "output": response.get("output", ""),
        "corrected": response.get("corrected", search_result is None),
        "remark": response.get("remark", ""),
    }