export const meta = {
  name: 'xai-ntc-deep-read',
  description: 'Read the selected corpus papers end-to-end in batches and extract methods, explanation-evaluation practice, limitations and gaps',
  phases: [
    { title: 'Read', detail: 'batch readers, full text where retrievable' },
    { title: 'Distill', detail: 'cluster gap statements across all notes' },
  ],
}

const ROOT = 'C:\\Users\\nakul\\OneDrive\\Desktop\\Academics\\xai-ntc-research'
const SEL = ROOT + '\\analysis\\deepread-selection.json'
const NOTES = ROOT + '\\corpus\\notes'

const READ_SCHEMA = {
  type: 'object',
  properties: {
    papers_read: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          read_depth: { type: 'string', enum: ['full_text', 'html_partial', 'abstract_only', 'unretrievable'] },
          task: { type: 'string' },
          model: { type: 'string' },
          input_repr: { type: 'string' },
          xai_method: { type: 'string' },
          xai_evaluation: { type: 'string', description: 'EXACTLY how explanation quality was evaluated; "none" if only plots shown' },
          ground_truth_used: { type: 'string', enum: ['none', 'human_expert', 'architectural', 'synthetic', 'interventional', 'other'] },
          datasets: { type: 'string' },
          key_numbers: { type: 'string' },
          stated_limitations: { type: 'string', description: 'authors own limitations/future work, near-verbatim' },
          gap_observations: { type: 'string', description: 'gaps YOU observe that authors do not state' },
        },
        required: ['title', 'read_depth', 'xai_evaluation', 'ground_truth_used', 'stated_limitations', 'gap_observations'],
      },
    },
    batch_gap_summary: { type: 'string' },
  },
  required: ['papers_read', 'batch_gap_summary'],
}

const DISTILL_SCHEMA = {
  type: 'object',
  properties: {
    gaps: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          gap: { type: 'string' },
          evidence: { type: 'string' },
          solvable_solo: { type: 'string', enum: ['yes', 'partly', 'no'] },
          ml_layer: { type: 'string', enum: ['yes', 'no'] },
          effort: { type: 'string' },
          risk: { type: 'string' },
        },
        required: ['gap', 'evidence', 'solvable_solo', 'ml_layer'],
      },
    },
    reading_stats: { type: 'string' },
  },
  required: ['gaps'],
}

const TOOLING = `
TOOLING RULES:
- NEVER use any mcp__claude-in-chrome__* tool.
- READ FULL TEXT. Best method, use it aggressively:
    Bash: python "${ROOT}\\scripts\\pdftext.py" "<pdf_url>" "${NOTES}\\tmp-<slug>.txt"
    then Grep/Read that .txt file. Works on arxiv.org/pdf/<id>, ACM/IEEE open mirrors, author PDFs.
- Fallback order: arXiv HTML (https://arxiv.org/html/<id>) via WebFetch -> open-access mirror -> S2 abstract.
- If a PDF URL is missing, find one: WebSearch "<title> pdf", or try https://arxiv.org/pdf/<arxiv-id>.
- Semantic Scholar and OpenAlex rate-limit hard; do not loop on 429s, move to arXiv/WebSearch.
- FOCUS your reading on two sections: (1) how explanation quality is EVALUATED, (2) LIMITATIONS / FUTURE WORK.
  Skim the rest. Quote where you can.
`

phase('Read')

const N_BATCHES = 13
const idxs = []
for (let i = 0; i < N_BATCHES; i++) idxs.push(i)

const results = await parallel(idxs.map(function (i) {
  return function () {
    return agent(
      `You are a careful academic reader building notes for a journal paper on EXPLAINABLE AI FOR NETWORK TRAFFIC CLASSIFICATION.

STEP 1. Get your batch. Run this Bash command to print the papers assigned to you:
    python -c "import json;d=json.load(open(r'${SEL}',encoding='utf-8'));print(json.dumps(d['batches'][${i}],indent=1))"

STEP 2. Read every paper in that batch END TO END (full text wherever retrievable).

${TOOLING}

STEP 3. For EACH paper fill the structured record. The fields that matter most:
- "xai_evaluation": exactly how the paper evaluates explanation quality. Quote the metric name.
  Write "none" if explanations are merely displayed as plots/tables without evaluation.
- "ground_truth_used": none | human_expert | architectural | synthetic | interventional | other.
  This is the single most important field for my project. Be strict: a deletion/occlusion curve is
  NOT ground truth (it is a proxy); an expert-nominated feature list IS human_expert; a model whose
  true decision regions are known by construction IS architectural.
- "stated_limitations": near-verbatim from the paper.

STEP 4. Write your full notes as markdown to ${NOTES}\\deepread-batch-${i}.md

Return the structured object. Be honest about read_depth.`,
      { label: 'read:b' + i, phase: 'Read', schema: READ_SCHEMA, model: 'fable' }
    )
  }
}))

const ok = results.filter(Boolean)
log('read complete: ' + ok.length + '/' + N_BATCHES + ' batches')

const nFull = ok.reduce(function (n, r) {
  return n + (r.papers_read || []).filter(function (p) { return p.read_depth === 'full_text' }).length
}, 0)
const nPapers = ok.reduce(function (n, r) { return n + (r.papers_read || []).length }, 0)
log('papers: ' + nPapers + ', full-text: ' + nFull)

// ground-truth census - the key statistic for the paper's motivation
const census = {}
for (const r of ok) {
  for (const p of (r.papers_read || [])) {
    const g = p.ground_truth_used || 'unknown'
    census[g] = (census[g] || 0) + 1
  }
}
log('ground-truth census: ' + JSON.stringify(census))

phase('Distill')

const digest = ok.map(function (r, i) {
  return '--- batch (' + (r.papers_read || []).length + ' papers) ---\n' +
    (r.batch_gap_summary || '') + '\n' +
    (r.papers_read || []).map(function (p) {
      return '* ' + p.title +
        ' [' + p.read_depth + '][gt=' + p.ground_truth_used + ']' +
        ' eval=' + String(p.xai_evaluation || '').slice(0, 220) +
        ' | lims=' + String(p.stated_limitations || '').slice(0, 260) +
        ' | gaps=' + String(p.gap_observations || '').slice(0, 260)
    }).join('\n')
}).join('\n\n')

const distilled = await agent(
  `Distil research gaps for a journal paper on explainable AI for network traffic classification.

Reading notes from ${ok.length} batches (${nPapers} papers, ${nFull} read in full text).
Ground-truth-usage census across all papers read: ${JSON.stringify(census)}

${digest.slice(0, 200000)}

Cluster into 10-20 DISTINCT research gaps. For each state: is it solvable by ONE researcher with
public data and modest compute (no testbed, no paid data)? Is it at the ML/DL layer applied to
computer networks? What is the risk it is already solved?

Prioritise: ground-truth validation of explanations, causal/interventional faithfulness, explanation
redundancy and multiplicity, dataset artifacts interacting with explanations, drift x explanations,
plausibility vs faithfulness.

Write the full distillation to ${ROOT}\\analysis\\05-distilled-gaps.md via Write.
Return the structured object.`,
  { label: 'distill:gaps', phase: 'Distill', schema: DISTILL_SCHEMA }
)

return {
  batches_done: ok.length,
  papers_read: nPapers,
  full_text: nFull,
  ground_truth_census: census,
  gaps: distilled ? distilled.gaps : null,
}
