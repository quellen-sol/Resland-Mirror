// The landing page's looping "Improve This Bullet" demo, as pure data.
// Every frame is derived from how far into the loop we are, so the
// animation is deterministic and the reduced-motion / no-JS render is just
// a fixed frame.

export const DEMO_SCRIPT = {
  bullet: "Worked on migrating services to Kubernetes.",
  question:
    "How many services moved over, and what changed for the team afterward?",
  answer: "About 40. Deploys went from 25 min to 6.",
  // Three ways to lead with the same facts, like the real suggestion dialog.
  // Only numbers from the answer: the demo can't make anything up either.
  options: [
    "Cut deploys from 25 minutes to 6 by moving 40 services to Kubernetes.",
    "Moved 40 services to Kubernetes, taking deploys from 25 minutes to 6.",
    "Migrated 40 services to Kubernetes so the team deploys in 6 minutes, not 25.",
  ],
  /** The option the demo picks before accepting. */
  picked: 0,
} as const;

export interface DemoFrame {
  /** Resland's question bubble is on screen. */
  questionVisible: boolean;
  /** The bubble shows "Thinking…" instead of the question. */
  thinking: boolean;
  /** Question text typed so far. */
  question: string;
  answerVisible: boolean;
  answer: string;
  /** The original bullet is struck through. */
  struck: boolean;
  /** How many of the options are on screen; they arrive one at a time. */
  optionsShown: number;
  /** The option highlighted as chosen, once all of them are up. */
  picked: number | null;
  actionsVisible: boolean;
  /** Accept is mid-click. */
  acceptPressed: boolean;
  toastVisible: boolean;
  /** Which text is typing right now (it gets the caret), if any. */
  typing: "question" | "answer" | null;
}

// Beats, in ms. The answer types slower than Resland's lines so it reads
// like a person typing.
const IDLE = 900;
const THINKING = 1300;
const QUESTION_PER_CHAR = 16;
const BEFORE_ANSWER = 700;
const ANSWER_PER_CHAR = 42;
const BEFORE_REWRITE = 600;
const OPTION_STAGGER = 450;
const BEFORE_PICK = 1100;
const BEFORE_ACCEPT = 800;
const PRESS = 220;
const HOLD = 3200;

const QUESTION_AT = IDLE;
const QUESTION_TYPE_AT = QUESTION_AT + THINKING;
const QUESTION_DONE_AT =
  QUESTION_TYPE_AT + DEMO_SCRIPT.question.length * QUESTION_PER_CHAR;
const ANSWER_AT = QUESTION_DONE_AT + BEFORE_ANSWER;
const ANSWER_DONE_AT = ANSWER_AT + DEMO_SCRIPT.answer.length * ANSWER_PER_CHAR;
const REWRITE_AT = ANSWER_DONE_AT + BEFORE_REWRITE;
const OPTIONS_DONE_AT =
  REWRITE_AT + (DEMO_SCRIPT.options.length - 1) * OPTION_STAGGER;
const PICK_AT = OPTIONS_DONE_AT + BEFORE_PICK;
const PRESS_AT = PICK_AT + BEFORE_ACCEPT;
const TOAST_AT = PRESS_AT + PRESS;

export const DEMO_LOOP_MS = TOAST_AT + HOLD;

/** The frame shown without motion: the whole exchange, an option picked,
 *  waiting on Accept. */
export const DEMO_STATIC_FRAME: DemoFrame = {
  questionVisible: true,
  thinking: false,
  question: DEMO_SCRIPT.question,
  answerVisible: true,
  answer: DEMO_SCRIPT.answer,
  struck: true,
  optionsShown: DEMO_SCRIPT.options.length,
  picked: DEMO_SCRIPT.picked,
  actionsVisible: true,
  acceptPressed: false,
  toastVisible: false,
  typing: null,
};

/** `text` as typed so far, starting at `start` at `perChar` ms a character. */
function typed(text: string, start: number, perChar: number, ms: number) {
  if (ms < start) return "";
  return text.slice(0, Math.min(text.length, Math.floor((ms - start) / perChar)));
}

export function demoFrameAt(ms: number): DemoFrame {
  const t = ((ms % DEMO_LOOP_MS) + DEMO_LOOP_MS) % DEMO_LOOP_MS;
  const question = typed(DEMO_SCRIPT.question, QUESTION_TYPE_AT, QUESTION_PER_CHAR, t);
  const answer = typed(DEMO_SCRIPT.answer, ANSWER_AT, ANSWER_PER_CHAR, t);
  const optionsShown =
    t < REWRITE_AT
      ? 0
      : Math.min(
          DEMO_SCRIPT.options.length,
          1 + Math.floor((t - REWRITE_AT) / OPTION_STAGGER),
        );

  let typing: DemoFrame["typing"] = null;
  if (t >= QUESTION_TYPE_AT && question.length < DEMO_SCRIPT.question.length) typing = "question";
  else if (t >= ANSWER_AT && answer.length < DEMO_SCRIPT.answer.length) typing = "answer";

  return {
    questionVisible: t >= QUESTION_AT,
    thinking: t >= QUESTION_AT && t < QUESTION_TYPE_AT,
    question,
    answerVisible: t >= ANSWER_AT,
    answer,
    struck: t >= REWRITE_AT,
    optionsShown,
    picked: t >= PICK_AT ? DEMO_SCRIPT.picked : null,
    actionsVisible: t >= OPTIONS_DONE_AT,
    acceptPressed: t >= PRESS_AT && t < TOAST_AT,
    toastVisible: t >= TOAST_AT,
    typing,
  };
}
