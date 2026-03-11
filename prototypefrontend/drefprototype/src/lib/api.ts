export interface EnrichedFieldValue {
  value: any;
  source: string;
  timestamp: string;
}

export type EnrichedFormState = Record<string, EnrichedFieldValue>;

export interface FieldUpdate {
  field_id: string;
  value: any;
  source: string;
  timestamp: string;
}

export interface ConflictInfo {
  field_name: string;
  field_label: string;
  existing_value: {
    value: any;
    source: string;
    timestamp: string;
  };
  new_value: {
    value: any;
    source: string;
    timestamp: string;
  };
  conflict_id: string;
}

export interface ChatResponse {
  classification: string;
  reply: string;
  field_updates: FieldUpdate[];
  conflicts: ConflictInfo[];
  processing_summary?: {
    total_files: number;
    successful: number;
    failed: number;
  };
}

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
}

/**
 * Send a chat message and stream the response via SSE.
 *
 * Calls `onReplyChunk` as reply text arrives and resolves with the
 * full structured response once the stream completes.
 */
export async function sendChatMessage(
  userMessage: string,
  formState: EnrichedFormState,
  conversationHistory: ConversationMessage[],
  files?: File[],
  onReplyChunk?: (delta: string, snapshot: string) => void,
  onStatus?: (message: string) => void,
): Promise<ChatResponse> {
  const payload = {
    user_message: userMessage,
    form_state: formState,
    conversation_history: conversationHistory,
  };

  const formData = new FormData();
  formData.append("data", JSON.stringify(payload));

  if (files) {
    for (const file of files) {
      formData.append("files", file);
    }
  }

  const response = await fetch("/api/chat", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Chat API error: ${response.status}`);
  }

  // Parse the SSE stream
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalResult: ChatResponse | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Process complete SSE messages (terminated by double newline)
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      if (!part.trim()) continue;

      let eventType = "message";
      let eventData = "";

      for (const line of part.split("\n")) {
        if (line.startsWith("event: ")) {
          eventType = line.slice(7);
        } else if (line.startsWith("data: ")) {
          eventData += line.slice(6);
        }
      }

      if (!eventData) continue;

      try {
        const parsed = JSON.parse(eventData);

        switch (eventType) {
          case "reply_chunk":
            onReplyChunk?.(parsed.delta, parsed.snapshot);
            break;
          case "status":
            onStatus?.(parsed.message);
            break;
          case "done":
            finalResult = parsed as ChatResponse;
            break;
          case "error":
            throw new Error(parsed.detail || "Stream error");
        }
      } catch (e) {
        if (e instanceof SyntaxError) continue; // skip malformed JSON
        throw e;
      }
    }
  }

  if (!finalResult) {
    throw new Error("Stream ended without a done event");
  }

  return finalResult;
}

// --- Evaluation types ---

export interface CriterionResult {
  criterion_id: string;
  field: string;
  criterion: string;
  outcome: "accept" | "dont_accept";
  required: boolean;
  reasoning: string;
  improvement_prompt: string;
  guidance: string;
}

export interface SectionResult {
  section_name: string;
  section_display_name: string;
  status: "accept" | "needs_revision";
  criteria_results: Record<string, CriterionResult>;
  issues: string[];
}

export interface ImprovementSuggestion {
  section: string;
  field: string;
  criterion: string;
  priority: number;
  guidance: string;
  ready_prompt: string;
  auto_applicable: boolean;
}

export interface EvaluationResult {
  dref_id: number;
  overall_status: "accepted" | "needs_revision" | "pending";
  section_results: Record<string, SectionResult>;
  improvement_suggestions: ImprovementSuggestion[];
  pass_one_completed: boolean;
  pass_two_completed: boolean;
  reference_examples_used: number[];
}

export interface SectionEvaluationResult extends SectionResult {
  improvement_suggestions: ImprovementSuggestion[];
}

// --- Evaluation API functions ---

export async function evaluateDref(
  formState: EnrichedFormState,
): Promise<EvaluationResult> {
  const response = await fetch("/api/evaluate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ form_state: formState }),
  });

  if (!response.ok) {
    throw new Error(`Evaluate API error: ${response.status}`);
  }

  return response.json();
}

export async function evaluateSection(
  formState: EnrichedFormState,
  section: string,
): Promise<SectionEvaluationResult> {
  const response = await fetch("/api/evaluate/section", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ form_state: formState, section }),
  });

  if (!response.ok) {
    throw new Error(`Evaluate section API error: ${response.status}`);
  }

  return response.json();
}
