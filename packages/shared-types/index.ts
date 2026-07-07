/** Re-export shared types — mirror apps/web/lib/types.ts and backend Pydantic schemas */

export type BriefStatus = "pending" | "running" | "done" | "failed";
export type RunStatus = "queued" | "running" | "succeeded" | "failed";
export type StepName = "storyboard" | "animate" | "voiceover" | "score" | "compose";
