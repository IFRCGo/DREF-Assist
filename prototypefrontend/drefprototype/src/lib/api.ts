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

export async function sendChatMessage(
  userMessage: string,
  formState: EnrichedFormState,
  conversationHistory: ConversationMessage[],
  files?: File[],
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

  return response.json();
}

export async function evaluateDref(formState: EnrichedFormState) {
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

export async function evaluateSection(formState: EnrichedFormState, section: string) {
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
