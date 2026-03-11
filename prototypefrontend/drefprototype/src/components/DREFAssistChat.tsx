import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import { Bot, Send, X, Save, Check, Mic } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
    sendChatMessage,
    type EnrichedFormState,
    type ConversationMessage,
    type FieldUpdate,
    type ConflictInfo,
} from "@/lib/api";
import { getFieldLabel } from "@/lib/fieldLabels";

interface FileAttachment {
    name: string;
    url: string;
    type?: string;
    size?: number;
}

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: Date;
    saved?: boolean;
    streaming?: boolean;
    fileAttachments?: FileAttachment[];
    fieldUpdates?: FieldUpdate[];
    conflicts?: ConflictInfo[];
}

type FieldUpdateStatus = "pending" | "accepted" | "rejected";

interface TrackedFieldUpdate {
    update: FieldUpdate;
    status: FieldUpdateStatus;
}

type ConflictResolution = "pending" | "keep_existing" | "use_new";

interface TrackedConflict {
    conflict: ConflictInfo;
    resolution: ConflictResolution;
}

interface DREFAssistChatProps {
    onClose: () => void;
    formState: EnrichedFormState;
    onFieldUpdates?: (updates: FieldUpdate[]) => void;
    isOpen: boolean;
    pendingMessage?: string | null;
    onPendingMessageConsumed?: () => void;
}

function formatDisplayValue(value: any): string {
    if (value === true) return "Yes";
    if (value === false) return "No";
    if (value == null) return "";
    return String(value);
}

const DREFAssistChat = ({ onClose, formState, onFieldUpdates, isOpen, pendingMessage, onPendingMessageConsumed }: DREFAssistChatProps) => {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: "welcome",
            role: "assistant",
            content:
                "Hello! I'm your DREF Application Assistant. I can help you draft sections, explain requirements, and provide guidance on completing your DREF application. How can I help you today?",
            timestamp: new Date(),
        },
    ]);
    const [input, setInput] = useState("");
    const [isTyping, setIsTyping] = useState(false);
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [previewUrls, setPreviewUrls] = useState<string[]>([]);
    const [updateTracker, setUpdateTracker] = useState<Record<string, Record<string, TrackedFieldUpdate>>>({});
    const [conflictTracker, setConflictTracker] = useState<Record<string, Record<string, TrackedConflict>>>({});
    const [chatSize, setChatSize] = useState({ width: 380, height: 520 });
    const [isResizing, setIsResizing] = useState(false);
    const [isRecording, setIsRecording] = useState(false);
    const recorderRef = useRef<MediaRecorder | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const [elapsedMs, setElapsedMs] = useState(0);
    const timerRef = useRef<number | null>(null);

    // Refs to read latest state without stale closures
    const updateTrackerRef = useRef(updateTracker);
    updateTrackerRef.current = updateTracker;
    const conflictTrackerRef = useRef(conflictTracker);
    conflictTrackerRef.current = conflictTracker;

    const scrollRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const createdUrlsRef = useRef<Set<string>>(new Set());
    const queuedUpdatesRef = useRef<Record<string, FieldUpdate[]>>({});
    const latestSnapshotRef = useRef("");
    const rafPendingRef = useRef(false);

    const formatTime = (ms: number) => {
        const totalSec = Math.floor(ms / 1000);
        const mm = Math.floor(totalSec / 60).toString().padStart(2, "0");
        const ss = (totalSec % 60).toString().padStart(2, "0");
        return `${mm}:${ss}`;
    };

    const startRecording = async () => {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            streamRef.current = stream;
            audioChunksRef.current = [];

            const mime = MediaRecorder.isTypeSupported("audio/webm")
                ? "audio/webm"
                : "audio/ogg;codecs=opus";

            const mr = new MediaRecorder(stream, { mimeType: mime });
            recorderRef.current = mr;

            mr.ondataavailable = (e) => {
                if (e.data && e.data.size > 0) audioChunksRef.current.push(e.data);
            };

            mr.onstop = () => {
                const blob = new Blob(audioChunksRef.current, { type: mime });
                const filename = `recording-${Date.now()}.${mime.includes("webm") ? "webm" : "ogg"}`;
                const file = new File([blob], filename, { type: blob.type });
                const url = URL.createObjectURL(blob);
                createdUrlsRef.current.add(url);

                // Only allow one file per message — replace any existing selection
                previewUrls.forEach(oldUrl => {
                    URL.revokeObjectURL(oldUrl);
                    createdUrlsRef.current.delete(oldUrl);
                });
                setSelectedFiles([file]);
                setPreviewUrls([url]);

                // stop tracks
                if (streamRef.current) {
                    streamRef.current.getTracks().forEach(t => t.stop());
                    streamRef.current = null;
                }
                recorderRef.current = null;
                audioChunksRef.current = [];
                setIsRecording(false);
                if (timerRef.current) {
                    clearInterval(timerRef.current);
                    timerRef.current = null;
                }
                setElapsedMs(0);
            };

            mr.start();
            setIsRecording(true);
            setElapsedMs(0);
            if (timerRef.current) clearInterval(timerRef.current);
            timerRef.current = window.setInterval(() => {
                setElapsedMs((prev) => prev + 1000);
            }, 1000);
        } catch (err) {
            // permission denied or other error - swallow silently
            console.error("Recording failed:", err);
        }
    };

    const stopRecording = () => {
        if (recorderRef.current && recorderRef.current.state !== "inactive") {
            recorderRef.current.stop();
        } else {
            // no recorder but stream exists
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(t => t.stop());
                streamRef.current = null;
            }
            setIsRecording(false);
            if (timerRef.current) {
                clearInterval(timerRef.current);
                timerRef.current = null;
            }
            setElapsedMs(0);
        }
    };

    const cancelRecording = () => {
        // stop and discard chunks
        if (recorderRef.current && recorderRef.current.state !== "inactive") {
            recorderRef.current.stop();
        }
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(t => t.stop());
            streamRef.current = null;
        }
        audioChunksRef.current = [];
        recorderRef.current = null;
        setIsRecording(false);
        if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
        }
        setElapsedMs(0);
    };

    // ensure cleanup on unmount
    useEffect(() => {
        return () => {
            if (recorderRef.current && recorderRef.current.state !== "inactive") {
                recorderRef.current.stop();
            }
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(t => t.stop());
                streamRef.current = null;
            }
            if (timerRef.current) {
                clearInterval(timerRef.current);
                timerRef.current = null;
            }
        };
    }, []);

    const handleMouseDown = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizing(true);
    };

    useEffect(() => {
        if (!isResizing) return;

        const handleMouseMove = (e: MouseEvent) => {
            const newWidth = Math.max(300, Math.min(1000, window.innerWidth - e.clientX));
            const newHeight = Math.max(300, Math.min(1000, window.innerHeight - e.clientY));
            setChatSize({ width: newWidth, height: newHeight });
        };

        const handleMouseUp = () => {
            setIsResizing(false);
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);

        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isResizing]);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isTyping]);

    useEffect(() => {
        return () => {
            createdUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
            createdUrlsRef.current.clear();
        };
    }, []);

    // Handle pending message from evaluation panel "Improve with AI" button
    useEffect(() => {
        if (pendingMessage && isOpen) {
            setInput(pendingMessage);
            onPendingMessageConsumed?.();
            inputRef.current?.focus();
        }
    }, [pendingMessage, isOpen, onPendingMessageConsumed]);

    // Build effective form state: accepted formState + all pending suggestions
    // This way the LLM sees what it already suggested and doesn't re-ask
    const buildEffectiveFormState = useCallback((): EnrichedFormState => {
        const effective: EnrichedFormState = { ...formState };

        // Merge in pending field updates so the LLM knows about its own suggestions
        for (const msgUpdates of Object.values(updateTrackerRef.current)) {
            for (const tracked of Object.values(msgUpdates)) {
                if (tracked.status === "pending") {
                    effective[tracked.update.field_id] = {
                        value: tracked.update.value,
                        source: tracked.update.source,
                        timestamp: tracked.update.timestamp,
                    };
                }
            }
        }

        // Merge in pending conflict new_values (the LLM suggested these)
        for (const msgConflicts of Object.values(conflictTrackerRef.current)) {
            for (const tracked of Object.values(msgConflicts)) {
                if (tracked.resolution === "pending") {
                    effective[tracked.conflict.field_name] = {
                        value: tracked.conflict.new_value.value,
                        source: tracked.conflict.new_value.source,
                        timestamp: tracked.conflict.new_value.timestamp,
                    };
                }
            }
        }

        return effective;
    }, [formState]);

    // --- Accept / Reject field updates (no side effects in state updaters) ---

    const acceptUpdate = useCallback((messageId: string, fieldId: string) => {
        const tracked = updateTrackerRef.current[messageId]?.[fieldId];
        if (!tracked || tracked.status !== "pending") return;

        // Side effect: apply to form
        onFieldUpdates?.([tracked.update]);

        // State update: mark as accepted
        setUpdateTracker((prev) => ({
            ...prev,
            [messageId]: {
                ...prev[messageId],
                [fieldId]: { ...prev[messageId][fieldId], status: "accepted" as const },
            },
        }));
    }, [onFieldUpdates]);

    const rejectUpdate = useCallback((messageId: string, fieldId: string) => {
        setUpdateTracker((prev) => {
            const msgUpdates = prev[messageId];
            if (!msgUpdates?.[fieldId] || msgUpdates[fieldId].status !== "pending") return prev;
            return {
                ...prev,
                [messageId]: {
                    ...msgUpdates,
                    [fieldId]: { ...msgUpdates[fieldId], status: "rejected" as const },
                },
            };
        });
    }, []);

    const acceptAllForMessage = useCallback((messageId: string) => {
        const msgUpdates = updateTrackerRef.current[messageId];
        if (!msgUpdates) return;

        const pending: FieldUpdate[] = [];
        for (const tracked of Object.values(msgUpdates)) {
            if (tracked.status === "pending") pending.push(tracked.update);
        }

        if (pending.length > 0) onFieldUpdates?.(pending);

        setUpdateTracker((prev) => {
            const updated = { ...prev[messageId] };
            for (const fieldId of Object.keys(updated)) {
                if (updated[fieldId].status === "pending") {
                    updated[fieldId] = { ...updated[fieldId], status: "accepted" };
                }
            }
            return { ...prev, [messageId]: updated };
        });
    }, [onFieldUpdates]);

    const rejectAllForMessage = useCallback((messageId: string) => {
        setUpdateTracker((prev) => {
            const msgUpdates = prev[messageId];
            if (!msgUpdates) return prev;
            const updated = { ...msgUpdates };
            for (const fieldId of Object.keys(updated)) {
                if (updated[fieldId].status === "pending") {
                    updated[fieldId] = { ...updated[fieldId], status: "rejected" };
                }
            }
            return { ...prev, [messageId]: updated };
        });
    }, []);

    // Auto-accept all pending updates across all messages
    const autoAcceptAllPending = useCallback(() => {
        const tracker = updateTrackerRef.current;
        const allPending: FieldUpdate[] = [];

        for (const msgUpdates of Object.values(tracker)) {
            for (const tracked of Object.values(msgUpdates)) {
                if (tracked.status === "pending") allPending.push(tracked.update);
            }
        }

        if (allPending.length > 0) onFieldUpdates?.(allPending);

        setUpdateTracker((prev) => {
            const next = { ...prev };
            for (const [msgId, msgUpdates] of Object.entries(next)) {
                let changed = false;
                const updated = { ...msgUpdates };
                for (const fieldId of Object.keys(updated)) {
                    if (updated[fieldId].status === "pending") {
                        updated[fieldId] = { ...updated[fieldId], status: "accepted" };
                        changed = true;
                    }
                }
                if (changed) next[msgId] = updated;
            }
            return next;
        });
    }, [onFieldUpdates]);

    // --- Conflict resolution (no side effects in state updaters) ---

    const resolveConflict = useCallback((messageId: string, conflictId: string, resolution: "keep_existing" | "use_new") => {
        const tracked = conflictTrackerRef.current[messageId]?.[conflictId];
        if (!tracked || tracked.resolution !== "pending") return;

        setConflictTracker((prev) => {
            const nextTracker = {
                ...prev,
                [messageId]: {
                    ...prev[messageId],
                    [conflictId]: { ...prev[messageId][conflictId], resolution },
                },
            };

            // Check if this was the last pending conflict for this message
            const msgConflicts = nextTracker[messageId];
            const hasPendingConflicts = Object.values(msgConflicts).some(c => c.resolution === "pending");

            if (!hasPendingConflicts) {
                // All conflicts resolved!
                // Group resolved "use_new" values and any queued non-conflicting updates
                const resolvedUpdates: FieldUpdate[] = [];
                for (const c of Object.values(msgConflicts)) {
                    if (c.resolution === "use_new") {
                        resolvedUpdates.push({
                            field_id: c.conflict.field_name,
                            value: c.conflict.new_value.value,
                            source: c.conflict.new_value.source,
                            timestamp: c.conflict.new_value.timestamp,
                        });
                    }
                }

                const queued = queuedUpdatesRef.current[messageId] || [];
                const finalUpdates = [...resolvedUpdates, ...queued];

                if (finalUpdates.length > 0) {
                    setTimeout(() => {
                        const newMsgId = crypto.randomUUID();
                        const newMsg: Message = {
                            id: newMsgId,
                            role: "assistant",
                            content: "Thanks for reviewing those! Here are the final suggested changes based on your conflict resolution and the extracted documents:",
                            timestamp: new Date(),
                            fieldUpdates: finalUpdates,
                        };

                        setMessages((prevMsg) => [...prevMsg, newMsg]);

                        const trackedUpdates: Record<string, TrackedFieldUpdate> = {};
                        for (const update of finalUpdates) {
                            trackedUpdates[update.field_id] = { update, status: "pending" };
                        }
                        setUpdateTracker((prevTrk) => ({ ...prevTrk, [newMsgId]: trackedUpdates }));
                    }, 0);
                } else {
                    setTimeout(() => {
                        const newMsgId = crypto.randomUUID();
                        setMessages((prevMsg) => [...prevMsg, {
                            id: newMsgId,
                            role: "assistant",
                            content: "Thanks! All conflicts resolved to keep existing values. No changes will be applied to the form.",
                            timestamp: new Date(),
                        }]);
                    }, 0);
                }

                delete queuedUpdatesRef.current[messageId];
            }

            return nextTracker;
        });
    }, []);

    const autoResolveAllConflicts = useCallback(() => {
        const tracker = conflictTrackerRef.current;
        const allNew: FieldUpdate[] = [];

        for (const msgConflicts of Object.values(tracker)) {
            for (const tracked of Object.values(msgConflicts)) {
                if (tracked.resolution === "pending") {
                    const c = tracked.conflict;
                    allNew.push({
                        field_id: c.field_name,
                        value: c.new_value.value,
                        source: c.new_value.source,
                        timestamp: c.new_value.timestamp,
                    });
                }
            }
        }

        if (allNew.length > 0) onFieldUpdates?.(allNew);

        setConflictTracker((prev) => {
            const next = { ...prev };
            for (const [msgId, msgConflicts] of Object.entries(next)) {
                let changed = false;
                const updated = { ...msgConflicts };
                for (const cId of Object.keys(updated)) {
                    if (updated[cId].resolution === "pending") {
                        updated[cId] = { ...updated[cId], resolution: "use_new" };
                        changed = true;
                    }
                }
                if (changed) next[msgId] = updated;
            }
            return next;
        });
    }, [onFieldUpdates]);

    // --- File handling ---

    const handleFilePick = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (!files || files.length === 0) return;

        // Only allow one file per message — replace any existing selection
        const file = files[0];
        const url = URL.createObjectURL(file);

        // Revoke old preview URLs
        previewUrls.forEach(oldUrl => {
            URL.revokeObjectURL(oldUrl);
            createdUrlsRef.current.delete(oldUrl);
        });

        createdUrlsRef.current.add(url);

        setSelectedFiles([file]);
        setPreviewUrls([url]);

        if (fileInputRef.current) fileInputRef.current.value = "";
    };

    const removeSelectedFile = (index: number) => {
        const urlToRemove = previewUrls[index];
        if (urlToRemove) {
            URL.revokeObjectURL(urlToRemove);
            createdUrlsRef.current.delete(urlToRemove);
        }
        setSelectedFiles(prev => prev.filter((_, i) => i !== index));
        setPreviewUrls(prev => prev.filter((_, i) => i !== index));
    };

    const buildConversationHistory = (): ConversationMessage[] => {
        return messages
            .filter((m) => m.id !== "welcome")
            .map((m) => ({
                role: m.role,
                content: m.content,
            }));
    };

    // --- Send message ---

    const sendMessage = async () => {
        const text = input.trim();
        if (!text && selectedFiles.length === 0) return;

        // Auto-accept all pending changes and resolve conflicts before sending
        autoAcceptAllPending();
        autoResolveAllConflicts();

        const attachments: FileAttachment[] = selectedFiles.map((file, i) => ({
            name: file.name,
            url: previewUrls[i] ?? URL.createObjectURL(file),
            type: file.type,
            size: file.size,
        }));

        const userMsg: Message = {
            id: crypto.randomUUID(),
            role: "user",
            content: text || (selectedFiles.length > 0 ? `Sent ${selectedFiles.length} file(s)` : ""),
            timestamp: new Date(),
            fileAttachments: attachments.length > 0 ? attachments : undefined,
        };

        if (userMsg.fileAttachments) {
            userMsg.fileAttachments.forEach(att => {
                if (att.url) createdUrlsRef.current.add(att.url);
            });
        }

        const filesToSend = selectedFiles.length > 0 ? [...selectedFiles] : undefined;

        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setIsTyping(true);
        setSelectedFiles([]);
        setPreviewUrls([]);

        const msgId = crypto.randomUUID();
        let messageInserted = false;

        try {
            // Send effective form state (includes pending suggestions) so
            // the LLM knows what it already suggested and doesn't re-ask
            const effectiveFormState = buildEffectiveFormState();

            const response = await sendChatMessage(
                text || `Please analyze the attached file(s): ${filesToSend?.map(f => f.name).join(', ')}`,
                effectiveFormState,
                buildConversationHistory(),
                filesToSend,
                // onReplyChunk — buffer snapshots and flush once per animation frame
                // so React doesn't re-render on every single token.
                (_delta, snapshot) => {
                    latestSnapshotRef.current = snapshot;
                    if (!rafPendingRef.current) {
                        rafPendingRef.current = true;
                        requestAnimationFrame(() => {
                            rafPendingRef.current = false;
                            const text = latestSnapshotRef.current;
                            if (!messageInserted) {
                                messageInserted = true;
                                setMessages((prev) => [...prev, {
                                    id: msgId,
                                    role: "assistant" as const,
                                    content: text,
                                    timestamp: new Date(),
                                    streaming: true,
                                }]);
                            } else {
                                setMessages((prev) =>
                                    prev.map((m) =>
                                        m.id === msgId ? { ...m, content: text } : m
                                    )
                                );
                            }
                        });
                    }
                },
                // onStatus — no-op; the existing isTyping indicator already
                // shows "Response Generating..." so we skip duplicate status text.
                undefined,
            );

            // Build reply with natural conflict acknowledgment
            let replyContent = response.reply;

            const hasUpdates = response.field_updates.length > 0;
            const hasConflicts = response.conflicts && response.conflicts.length > 0;

            if (hasConflicts) {
                const conflictFields = response.conflicts
                    .map((c: ConflictInfo) => c.field_label || getFieldLabel(c.field_name))
                    .join(", ");

                if (hasUpdates) {
                    replyContent += `\n\nI've also noticed conflicting information for **${conflictFields}**. Please review below and choose which values to keep.`;
                } else {
                    replyContent += `\n\nI noticed conflicting information for **${conflictFields}**. Please review below and choose which values to keep.`;
                }
            }

            // Replace or insert the final structured response
            const finalMsg: Message = {
                id: msgId,
                role: "assistant",
                content: replyContent,
                timestamp: new Date(),
                fieldUpdates: hasConflicts ? undefined : response.field_updates,
                conflicts: response.conflicts,
            };

            if (messageInserted) {
                setMessages((prev) =>
                    prev.map((m) => (m.id === msgId ? finalMsg : m))
                );
            } else {
                setMessages((prev) => [...prev, finalMsg]);
            }

            if (hasConflicts && hasUpdates) {
                queuedUpdatesRef.current[msgId] = response.field_updates;
            }

            // Store field updates as pending — ONLY if they are rendered now
            if (!hasConflicts && hasUpdates) {
                const tracked: Record<string, TrackedFieldUpdate> = {};
                for (const update of response.field_updates) {
                    tracked[update.field_id] = { update, status: "pending" };
                }
                setUpdateTracker((prev) => ({ ...prev, [msgId]: tracked }));
            }

            // Store conflicts as pending for interactive resolution
            if (response.conflicts && response.conflicts.length > 0) {
                const tracked: Record<string, TrackedConflict> = {};
                for (const conflict of response.conflicts) {
                    tracked[conflict.conflict_id] = { conflict, resolution: "pending" };
                }
                setConflictTracker((prev) => ({ ...prev, [msgId]: tracked }));
            }
        } catch (error) {
            const errorContent = `Sorry, I encountered an error: ${error instanceof Error ? error.message : "Unknown error"}. Please try again.`;
            if (messageInserted) {
                setMessages((prev) =>
                    prev.map((m) =>
                        m.id === msgId ? { ...m, content: errorContent } : m
                    )
                );
            } else {
                setMessages((prev) => [...prev, {
                    id: msgId,
                    role: "assistant" as const,
                    content: errorContent,
                    timestamp: new Date(),
                }]);
            }
        } finally {
            setIsTyping(false);
        }
    };

    const toggleSave = (id: string) => {
        setMessages((prev) =>
            prev.map((m) => (m.id === id ? { ...m, saved: !m.saved } : m))
        );
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    // --- Render cards ---

    const renderFieldUpdatesCard = (msg: Message) => {
        if (!msg.fieldUpdates || msg.fieldUpdates.length === 0) return null;

        const msgUpdates = updateTracker[msg.id];

        // Brief flash before tracker populates — show pending badge, NOT the old "Updated" badge
        if (!msgUpdates) {
            return (
                <div className="mt-2 rounded border border-border bg-card text-foreground text-xs px-2 py-1.5">
                    {msg.fieldUpdates.length} suggested change{msg.fieldUpdates.length !== 1 ? "s" : ""} loading...
                </div>
            );
        }

        const entries = Object.entries(msgUpdates);
        const hasPending = entries.some(([, t]) => t.status === "pending");
        const pendingCount = entries.filter(([, t]) => t.status === "pending").length;

        return (
            <div className="mt-2 rounded border border-border bg-card text-foreground text-xs overflow-hidden">
                <div className="flex items-center justify-between px-2 py-1.5 bg-muted/50 border-b border-border">
                    <span className="font-medium">
                        {hasPending
                            ? `${pendingCount} suggested change${pendingCount !== 1 ? "s" : ""}`
                            : `${entries.length} change${entries.length !== 1 ? "s" : ""} resolved`
                        }
                    </span>
                    {hasPending && (
                        <div className="flex items-center gap-1">
                            <button
                                onClick={() => acceptAllForMessage(msg.id)}
                                className="flex items-center gap-0.5 rounded px-1.5 py-0.5 text-green-700 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors"
                                title="Accept all"
                            >
                                <Check className="h-3 w-3" />
                                <span>All</span>
                            </button>
                            <button
                                onClick={() => rejectAllForMessage(msg.id)}
                                className="flex items-center gap-0.5 rounded px-1.5 py-0.5 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
                                title="Reject all"
                            >
                                <X className="h-3 w-3" />
                                <span>All</span>
                            </button>
                        </div>
                    )}
                </div>

                <div className="divide-y divide-border">
                    {entries.map(([fieldId, tracked]) => (
                        <div
                            key={fieldId}
                            className={`flex items-center justify-between px-2 py-1.5 gap-2 ${tracked.status === "rejected" ? "opacity-50" : ""
                                }`}
                        >
                            <div className="flex-1 min-w-0">
                                <span className="font-medium">{getFieldLabel(fieldId)}: </span>
                                <span
                                    className={
                                        tracked.status === "rejected"
                                            ? "line-through text-muted-foreground"
                                            : tracked.status === "accepted"
                                                ? "text-green-700 dark:text-green-400"
                                                : ""
                                    }
                                >
                                    {formatDisplayValue(tracked.update.value)}
                                </span>
                            </div>

                            {tracked.status === "pending" ? (
                                <div className="flex items-center gap-0.5 shrink-0">
                                    <button
                                        onClick={() => acceptUpdate(msg.id, fieldId)}
                                        className="rounded p-0.5 text-green-700 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors"
                                        title="Accept"
                                    >
                                        <Check className="h-3.5 w-3.5" />
                                    </button>
                                    <button
                                        onClick={() => rejectUpdate(msg.id, fieldId)}
                                        className="rounded p-0.5 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
                                        title="Reject"
                                    >
                                        <X className="h-3.5 w-3.5" />
                                    </button>
                                </div>
                            ) : (
                                <span className="shrink-0">
                                    {tracked.status === "accepted" ? (
                                        <Check className="h-3.5 w-3.5 text-green-700 dark:text-green-400" />
                                    ) : (
                                        <X className="h-3.5 w-3.5 text-red-600 dark:text-red-400" />
                                    )}
                                </span>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    const renderConflictsCard = (msg: Message) => {
        if (!msg.conflicts || msg.conflicts.length === 0) return null;

        const msgConflicts = conflictTracker[msg.id];
        if (!msgConflicts) return null;

        const entries = Object.entries(msgConflicts);
        const hasPending = entries.some(([, t]) => t.resolution === "pending");
        const pendingCount = entries.filter(([, t]) => t.resolution === "pending").length;

        return (
            <div className="mt-2 rounded border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-950/30 text-foreground text-xs overflow-hidden">
                <div className="flex items-center justify-between px-2 py-1.5 bg-amber-100/50 dark:bg-amber-900/30 border-b border-amber-200 dark:border-amber-800">
                    <span className="font-medium text-amber-800 dark:text-amber-300">
                        {hasPending
                            ? `${pendingCount} conflict${pendingCount !== 1 ? "s" : ""} to resolve`
                            : `${entries.length} conflict${entries.length !== 1 ? "s" : ""} resolved`
                        }
                    </span>
                </div>

                <div className="divide-y divide-amber-200 dark:divide-amber-800">
                    {entries.map(([conflictId, tracked]) => {
                        const c = tracked.conflict;
                        const label = c.field_label || getFieldLabel(c.field_name);
                        const resolved = tracked.resolution !== "pending";

                        return (
                            <div key={conflictId} className={`px-2 py-2 ${resolved ? "opacity-60" : ""}`}>
                                <div className="font-medium mb-1">{label}</div>

                                <div className="flex items-center justify-between gap-1 mb-1">
                                    <span className={
                                        tracked.resolution === "keep_existing"
                                            ? "text-green-700 dark:text-green-400"
                                            : tracked.resolution === "use_new"
                                                ? "line-through text-muted-foreground"
                                                : ""
                                    }>
                                        {formatDisplayValue(c.existing_value.value)}
                                        <span className="text-muted-foreground ml-1">({c.existing_value.source})</span>
                                    </span>
                                    {!resolved && (
                                        <button
                                            onClick={() => resolveConflict(msg.id, conflictId, "keep_existing")}
                                            className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium border border-border hover:bg-muted transition-colors"
                                        >
                                            Keep
                                        </button>
                                    )}
                                    {tracked.resolution === "keep_existing" && (
                                        <Check className="h-3.5 w-3.5 shrink-0 text-green-700 dark:text-green-400" />
                                    )}
                                </div>

                                <div className="flex items-center justify-between gap-1">
                                    <span className={
                                        tracked.resolution === "use_new"
                                            ? "text-green-700 dark:text-green-400"
                                            : tracked.resolution === "keep_existing"
                                                ? "line-through text-muted-foreground"
                                                : ""
                                    }>
                                        {formatDisplayValue(c.new_value.value)}
                                        <span className="text-muted-foreground ml-1">({c.new_value.source})</span>
                                    </span>
                                    {!resolved && (
                                        <button
                                            onClick={() => resolveConflict(msg.id, conflictId, "use_new")}
                                            className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium border border-primary text-primary hover:bg-primary hover:text-primary-foreground transition-colors"
                                        >
                                            Use
                                        </button>
                                    )}
                                    {tracked.resolution === "use_new" && (
                                        <Check className="h-3.5 w-3.5 shrink-0 text-green-700 dark:text-green-400" />
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        );
    };

    return (
        <div className={`fixed bottom-20 right-6 z-50 flex flex-col rounded-xl border border-border bg-card shadow-2xl ${isOpen ? "" : "hidden"}`}
            style={{ width: `${chatSize.width}px`, height: `${chatSize.height}px` }}
        >
            {/* Header */}
            <div className="relative flex items-center justify-between rounded-t-xl bg-primary px-4 py-3 overflow-hidden">
                {/* Resize handle - top-left corner */}
                <div
                    onMouseDown={handleMouseDown}
                    className="absolute -left-3 -top-3 h-8 w-8 rotate-45 overflow-hidden opacity-75 cursor-nwse-resize hover:opacity-30 transition-opacity"
                >
                    <div className="flex h-full w-full flex-col gap-0.5">
                        <div className="h-1 bg-primary-foreground"></div>
                        <div className="h-1 bg-transparent"></div>
                        <div className="h-1 bg-primary-foreground"></div>
                        <div className="h-1 bg-transparent"></div>
                        <div className="h-1 bg-primary-foreground"></div>
                        <div className="h-1 bg-transparent"></div>
                        <div className="h-1 bg-primary-foreground"></div>
                    </div>
                </div>

                <div className="flex items-center gap-2 text-primary-foreground">
                    <Bot className="h-5 w-5" />
                    <span className="font-semibold text-sm">DREF Assist</span>
                </div>
                <button
                    onClick={onClose}
                    className="rounded p-1 text-primary-foreground/80 hover:text-primary-foreground hover:bg-primary-foreground/10 transition-colors"
                >
                    <X className="h-4 w-4" />
                </button>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 px-4 py-3" ref={scrollRef}>
                <div className="space-y-4">
                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"
                                }`}
                        >
                            <div
                                className={`group relative max-w-[85%] rounded-lg px-3 py-2 text-sm leading-relaxed ${msg.role === "user"
                                    ? "bg-primary text-primary-foreground"
                                    : "bg-muted text-foreground"
                                    }`}
                            >
                                <div className="break-words prose prose-sm dark:prose-invert max-w-none prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-headings:my-1.5">
                                    {msg.streaming ? (
                                        <p className="whitespace-pre-wrap">{msg.content}<span className="inline-block w-1.5 h-4 ml-0.5 bg-current animate-pulse align-text-bottom" /></p>
                                    ) : (
                                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                                    )}
                                </div>

                                {msg.fileAttachments && msg.fileAttachments.length > 0 && (
                                    <div className="mt-2 flex flex-wrap gap-2">
                                        {msg.fileAttachments.map((attachment, idx) => (
                                            <a
                                                key={idx}
                                                href={attachment.url}
                                                download={attachment.name}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="inline-flex items-center gap-2 rounded px-2 py-1 text-xs bg-secondary/10 hover:bg-secondary/20 max-w-full"
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                                    <polyline points="7 10 12 15 17 10" />
                                                    <line x1="12" y1="15" x2="12" y2="3" />
                                                </svg>
                                                <span className="truncate max-w-[160px]">{attachment.name}</span>
                                                <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                                                    {attachment.size ? ` • ${Math.round(attachment.size / 1024)} KB` : ""}
                                                </span>
                                            </a>
                                        ))}
                                    </div>
                                )}

                                {/* Render conflicts FIRST, then updates (which are hidden if conflicts exist) */}
                                {renderConflictsCard(msg)}
                                {renderFieldUpdatesCard(msg)}

                                <button
                                    onClick={() => toggleSave(msg.id)}
                                    className={`absolute -right-7 top-1 rounded p-0.5 transition-opacity ${msg.saved
                                        ? "opacity-100 text-primary"
                                        : "opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-primary"
                                        }`}
                                    title={msg.saved ? "Unsave" : "Save prompt"}
                                >
                                    <Save className="h-3.5 w-3.5" />
                                </button>
                            </div>
                            {msg.saved && (
                                <span className="mt-0.5 text-[10px] text-primary">Saved</span>
                            )}
                        </div>
                    ))}
                    {isTyping && (
                        <div className="flex items-start">
                            <div className="rounded-lg bg-muted px-3 py-2 text-sm text-muted-foreground">
                                <div className="flex items-center gap-2">
                                    <div className="flex gap-1">
                                        <div className="h-2 w-2 rounded-full bg-muted-foreground/60 animate-bounce" style={{ animationDelay: '0ms', animationDuration: '1s' }}></div>
                                        <div className="h-2 w-2 rounded-full bg-muted-foreground/60 animate-bounce" style={{ animationDelay: '150ms', animationDuration: '1s' }}></div>
                                        <div className="h-2 w-2 rounded-full bg-muted-foreground/60 animate-bounce" style={{ animationDelay: '300ms', animationDuration: '1s' }}></div>
                                    </div>
                                    <span>Response Generating...</span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </ScrollArea>

            {messages.some((m) => m.saved) && (
                <div className="border-t border-border px-4 py-1.5">
                    <p className="text-[10px] text-muted-foreground">
                        {messages.filter((m) => m.saved).length} prompt(s) saved
                    </p>
                </div>
            )}

            <div className="flex flex-col border-t border-border px-3 py-3">
                <div className="flex items-center gap-2">
                    <Input
                        ref={inputRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask DREF Assist..."
                        className="flex-1 text-sm"
                        disabled={isTyping}
                    />
                    <input ref={fileInputRef} type="file" className="hidden" onChange={handleFilePick} />
                    <Button
                        size="icon"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isTyping}
                        className="h-9 w-9 shrink-0"
                        title="Attach file"
                        aria-label="Attach file"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M21.44 11.05L12.6 19.9a5.5 5.5 0 0 1-7.78 0 5.5 5.5 0 0 1 0-7.78l8.84-8.84a3.5 3.5 0 0 1 4.95 4.95L10 17.1" />
                        </svg>
                    </Button>

                    {/* Record button */}
                    <Button
                        size="icon"
                        onClick={() => { if (isRecording) stopRecording(); else startRecording(); }}
                        disabled={isTyping}
                        className={`h-9 w-9 shrink-0 ${isRecording ? "bg-red-600/80 hover:bg-red-600" : ""}`}
                        title={isRecording ? "Stop recording" : "Record audio"}
                        aria-label="Record audio"
                    >
                        {isRecording ? (
                            <span className="relative flex items-center justify-center">
                                <Mic className="h-4 w-4" />
                                <span className="pointer-events-none absolute inset-0 flex items-center justify-center">
                                    <span className="block w-[1.5px] h-5 bg-white/90 rotate-45 translate-y-px" />
                                </span>
                            </span>
                        ) : (
                            <Mic className="h-4 w-4" />
                        )}
                    </Button>

                    <Button
                        size="icon"
                        onClick={sendMessage}
                        disabled={(!input.trim() && selectedFiles.length === 0) || isTyping}
                        className="h-9 w-9 shrink-0"
                        title="Send"
                        aria-label="Send"
                    >
                        <Send className="h-4 w-4" />
                    </Button>
                </div>

                {/* Recording status (timer) */}
                {isRecording && (
                    <div className="mt-2 flex items-center gap-2">
                        <span className="text-[11px] font-mono text-foreground/90 select-none">{formatTime(elapsedMs)}</span>
                        <Button
                            size="icon"
                            onClick={cancelRecording}
                            title="Cancel recording"
                            aria-label="Cancel recording"
                            className="h-7 w-7 p-1"
                        >
                            <X className="h-3 w-3" />
                        </Button>
                    </div>
                )}

                {selectedFiles.length > 0 && (
                    <div className="mt-2 flex flex-col gap-2 max-h-[120px] overflow-y-auto pr-1">
                        {selectedFiles.map((file, idx) => (
                            <div key={idx} className="flex items-center justify-between gap-2 rounded border border-border px-2 py-1 text-sm">
                                <div className="flex items-center gap-2 flex-1 min-w-0">
                                    {file.type?.startsWith("audio") ? (
                                        <audio controls src={previewUrls[idx]} className="w-full h-6 max-w-full" />
                                    ) : (
                                        <div className="flex items-center gap-2 min-w-0">
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 shrink-0 text-muted-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                                <polyline points="7 10 12 15 17 10" />
                                                <line x1="12" y1="15" x2="12" y2="3" />
                                            </svg>
                                            <div className="truncate">
                                                {file.name}{" "}
                                                <span className="text-[11px] text-muted-foreground whitespace-nowrap">• {Math.round((file.size ?? 0) / 1024)} KB</span>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <div className="flex items-center gap-1 shrink-0">
                                    <button onClick={() => removeSelectedFile(idx)} className="h-7 w-7 p-1 rounded hover:bg-muted flex items-center justify-center text-muted-foreground hover:text-foreground">
                                        <X className="h-3 w-3" />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default DREFAssistChat;
