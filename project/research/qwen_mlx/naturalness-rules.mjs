/** Editorial specifications, not a detector-evasion recipe or empirical result. */
export const NATURALNESS_RULES = Object.freeze([
  {
    id:'specific_subject_action',label:'Name the actor and action',
    goal:'Make the existing actor, operation, and object easy to identify.',
    when:'An agentless or nominalised construction obscures an actor or action already stated in the passage.',
    notWhen:'The actor is genuinely unknown, or a passive construction appropriately keeps the scientific object in focus.',
    before:'The retrieval of relevant examples is performed by the revision planner.',
    after:'The revision planner retrieves relevant examples.',
    avoid:'Our intelligent planner retrieves the best examples.',
    caution:'Do not add intelligence claims or a guarantee of optimal retrieval.',
  },
  {
    id:'concrete_wording',label:'Replace vague wording with supported detail',
    goal:'State the operation or relationship rather than praise it.',
    when:'A vague phrase has an explicit, more informative equivalent in the current passage or retained surrounding text.',
    notWhen:'Greater specificity would require inventing a method, number, result, or implementation detail.',
    before:'The system uses a sophisticated mechanism to improve revision: it retrieves earlier editing examples.',
    after:'The system retrieves earlier editing examples to guide revision.',
    avoid:'The system retrieves three verified examples to improve accuracy.',
    caution:'Neither the number, verification status, nor an accuracy gain is supported by this example.',
  },
  {
    id:'remove_redundancy',label:'Remove repetition, retain substance',
    goal:'Remove repeated meaning and empty modifiers without losing qualifications.',
    when:'Two phrases repeat the same proposition, or an intensifier adds no supported meaning.',
    notWhen:'Repetition disambiguates a technical reference, or a repeated caveat is needed at the claim it qualifies.',
    before:'The proposed method may potentially reduce repeated edits, although this has not yet been tested.',
    after:'The proposed method may reduce repeated edits, although this has not yet been tested.',
    avoid:'The method reduces repeated edits.',
    caution:'Removing uncertainty or planned-study status changes the scientific claim.',
  },
  {
    id:'information_flow',label:'Connect given information to the next point',
    goal:'Make the existing referent and logical relation explicit; order sentences coherently.',
    when:'A pronoun has an ambiguous referent, or an existing contrast or dependency is obscured by sentence order.',
    notWhen:'A transition would imply causality, agreement, or contrast that the passage does not establish.',
    before:'The checker examines the revision. The editor proposes the revision before this check.',
    after:'The editor proposes a revision. The checker then examines it.',
    avoid:'The editor proposes a revision, so the checker approves it.',
    caution:'Keep the established actors and order; do not turn a check into a guaranteed approval.',
  },
  {
    id:'sentence_focus',label:'Give each sentence a clear focus',
    goal:'Separate competing points or combine needless fragments while retaining dependencies.',
    when:'Nested clauses obscure distinct operations, or disconnected short sentences conceal a close relationship.',
    notWhen:'A long sentence clearly expresses a necessary qualification, definition, or comparison.',
    before:'The editor proposes a revision, which is then assessed by the checker, which compares the citations with those in the original draft.',
    after:'The editor proposes a revision. The checker then compares its citations with those in the original draft.',
    avoid:'The editor revises the text. The checker approves it.',
    caution:'Sentence length is descriptive, not a target; do not omit the operation or presume approval.',
  },
  {
    id:'calibrated_claims',label:'Keep claims calibrated to evidence',
    goal:'Express the same uncertainty and study status clearly, without stacked hedges or promotional certainty.',
    when:'Stacked hedges, promotional modifiers, or awkward qualification obscure an otherwise identifiable evidence boundary.',
    notWhen:'The sentence already communicates a necessary uncertainty, limitation, or attributed source finding precisely.',
    before:'We aim to investigate whether the proposed memory may potentially support clearer revisions.',
    after:'We propose testing whether the memory supports clearer revisions.',
    avoid:'Our memory produces clearer revisions.',
    caution:'An intended test is not a finding; do not remove uncertainty, citations, or limitations.',
  },
].map(rule=>Object.freeze(rule)));

export const RULE_IDS = Object.freeze(NATURALNESS_RULES.map(rule=>rule.id));

export function naturalnessInstructions() {
  return 'Operational naturalness means readable academic expression: an identifiable subject and action, precise supported wording, economical phrasing, coherent information flow, manageable sentence focus, and calibrated claims. Apply only a rule whose WHEN condition is evidenced in the current text; honour every NOT-WHEN condition. These are editorial specifications, not empirically proven gains or instructions to evade AI detection. Do not ban hyphens, passive voice, technical terms, first-person pronouns, or long sentences. Do not add conversational filler or intentionally vary wording to look human. The examples below are illustrative and supply no facts for the proposal.\n'+JSON.stringify(NATURALNESS_RULES);
}
