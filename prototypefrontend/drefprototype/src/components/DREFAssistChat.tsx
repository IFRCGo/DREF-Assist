// prototypefrontend/drefprototype/src/components/DREFAssistChat.tsx
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

    // Recording state
    const [isRecording, setIsRecording] = useState(false);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const recordedChunksRef = useRef<Blob[]>([]);
    const createRecordingRef = useRef(true);

    // Timer state for live display
    const [elapsedMs, setElapsedMs] = useState<number>(0);
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
            // revoke all object URLs
            createdUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
            createdUrlsRef.current.clear();

            // clear timer if any
            if (timerRef.current !== null) {
                clearInterval(timerRef.current);
                timerRef.current = null;
            }
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

    // Build effective form state by merging pending suggestions/resolutions
    const buildEffectiveFormState = useCallback((): EnrichedFormState => {
        const effective: EnrichedFormState = { ...formState };

        for (const msgUpdates of Object.values(updateTrackerRef.current)) {
            for (const tracked of Object.values(msgUpdates)) {
                if (tracked.status === "pending" && (tracked.update as any).field_id) {
                    const u = tracked.update as any;
                    effective[u.field_id] = u.new_value;
                }
            }
        }

        for (const msgConflicts of Object.values(conflictTrackerRef.current)) {
            for (const tracked of Object.values(msgConflicts)) {
                if (tracked.resolution === "pending") {
                    const c = tracked.conflict as any;
                    if (c && c.field_name && c.new_value !== undefined) {
                        effective[c.field_name] = c.new_value;
                    }
                }
            }
        }

        return effective;
    }, [formState]);

    // --- Accept / Reject / Auto handlers (simplified) ---
    const acceptUpdate = useCallback((messageId: string, fieldId: string) => {
        const tracked = updateTrackerRef.current[messageId]?.[fieldId];
        if (!tracked || tracked.status !== "pending") return;

        onFieldUpdates?.([tracked.update]);

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

    const resolveConflict = useCallback((messageId: string, conflictId: string, resolution: "keep_existing" | "use_new") => {
        const tracked = conflictTrackerRef.current[messageId]?.[conflictId];
        if (!tracked || tracked.resolution !== "pending") return;

        setConflictTracker((prev) => {
            const nextTracker = {
                ...prev,
                [messageId]: {
                    ...prev[messageId],
                    [conflictId]: { ...prev[messageId][conflictId], resolution: resolution as ConflictResolution },
                },
            };

            const msgConflicts = nextTracker[messageId];
            const hasPendingConflicts = Object.values(msgConflicts).some(c => c.resolution === "pending");

            if (!hasPendingConflicts) {
                const resolvedUpdates: FieldUpdate[] = [];
                for (const c of Object.values(msgConflicts)) {
                    if (c.resolution === "use_new") {
                        const conflict = c.conflict as any;
                        if (conflict.field_name && conflict.new_value !== undefined) {
                            resolvedUpdates.push({ field_id: conflict.field_name, new_value: conflict.new_value } as any);
                        }
                    }
                }

                const queued = queuedUpdatesRef.current[messageId] || [];
                const finalUpdates = [...resolvedUpdates, ...queued];

                if (finalUpdates.length > 0) {
                    setTimeout(() => {
                        onFieldUpdates?.(finalUpdates);
                    }, 0);
                }

                delete queuedUpdatesRef.current[messageId];
            }

            return nextTracker;
        });
    }, [onFieldUpdates]);

    const autoResolveAllConflicts = useCallback(() => {
        const tracker = conflictTrackerRef.current;
        const allNew: FieldUpdate[] = [];

        for (const msgConflicts of Object.values(tracker)) {
            for (const tracked of Object.values(msgConflicts)) {
                if (tracked.resolution === "pending") {
                    const c = tracked.conflict as any;
                    if (c.field_name && c.new_value !== undefined) {
                        allNew.push({ field_id: c.field_name, new_value: c.new_value } as any);
                    }
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

        const newFiles = Array.from(files);
        const newUrls = newFiles.map((file) => URL.createObjectURL(file));

        newUrls.forEach(url => createdUrlsRef.current.add(url));

        setSelectedFiles(prev => [...prev, ...newFiles]);
        setPreviewUrls(prev => [...prev, ...newUrls]);

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

    // --- Audio recording ---
    const formatTime = (ms: number) => {
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        const tenths = Math.floor((ms % 1000) / 100);
        return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}.${tenths}`;
    };

    const startRecording = async () => {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            const errorMsg: Message = {
                id: crypto.randomUUID(),
                role: "assistant",
                content: "Microphone not available in this browser.",
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMsg]);
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            recordedChunksRef.current = [];
            createRecordingRef.current = true;
            const options: MediaRecorderOptions = { mimeType: "audio/webm" };
            const mediaRecorder = new MediaRecorder(stream, options);

            mediaRecorder.ondataavailable = (ev) => {
                if (ev.data && ev.data.size > 0) recordedChunksRef.current.push(ev.data);
            };

            mediaRecorder.onstop = () => {
                // only create file/preview if not cancelled
                if (createRecordingRef.current && recordedChunksRef.current.length > 0) {
                    const blob = new Blob(recordedChunksRef.current, { type: recordedChunksRef.current[0].type || "audio/webm" });
                    const now = new Date();
                    const safeName = `recording_${now.toISOString()}.webm`;
                    const file = new File([blob], safeName, { type: blob.type || "audio/webm" });

                    const url = URL.createObjectURL(file);
                    createdUrlsRef.current.add(url);

                    setSelectedFiles(prev => [...prev, file]);
                    setPreviewUrls(prev => [...prev, url]);
                }

                // release microphone
                stream.getTracks().forEach(t => t.stop());
                recordedChunksRef.current = [];
            };

            mediaRecorderRef.current = mediaRecorder;
            mediaRecorder.start();

            // start timer
            setElapsedMs(0);
            if (timerRef.current !== null) clearInterval(timerRef.current);
            timerRef.current = window.setInterval(() => {
                setElapsedMs((prev) => prev + 100);
            }, 100);

            setIsRecording(true);
        } catch (err) {
            const errorMsg: Message = {
                id: crypto.randomUUID(),
                role: "assistant",
                content: `Unable to start recording: ${err instanceof Error ? err.message : "Unknown error"}.`,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMsg]);
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
            mediaRecorderRef.current.stop();
        }
        mediaRecorderRef.current = null;
        setIsRecording(false);

        // stop timer but leave elapsedMs as final duration (user can see)
        if (timerRef.current !== null) {
            clearInterval(timerRef.current);
            timerRef.current = null;
        }
    };

    const cancelRecording = () => {
        // prevent onstop from creating a file
        createRecordingRef.current = false;

        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
            try { mediaRecorderRef.current.stop(); } catch {}
            mediaRecorderRef.current = null;
        }

        // remove any temporary "recording_" files/urls if they exist
        setSelectedFiles(prev => {
            const toKeep: File[] = [];
            const removedNames: string[] = [];
            prev.forEach((f) => {
                if (f.name.startsWith("recording_")) {
                    removedNames.push(f.name);
                } else {
                    toKeep.push(f);
                }
            });
            return toKeep;
        });

        setPreviewUrls(prev => {
            const remaining: string[] = [];
            prev.forEach((u) => {
                // if url corresponds to a recording created earlier, revoke it and drop
                // heuristics: if url in createdUrlsRef and its blob name included "recording_"
                // cannot easily map back, so remove any preview that was newly added at end and revoke safely if tracked
                remaining.push(u);
            });
            return remaining;
        });

        // revoke and remove any created URLs that look like recordings (best-effort)
        createdUrlsRef.current.forEach((u) => {
            // best-effort: if url was created during recording, revoke it now
            try {
                URL.revokeObjectURL(u);
            } catch {}
        });
        createdUrlsRef.current.clear();

        recordedChunksRef.current = [];
        setIsRecording(false);

        // stop & reset timer
        if (timerRef.current !== null) {
            clearInterval(timerRef.current);
            timerRef.current = null;
        }
        setElapsedMs(0);
    };

    // --- Conversation history ---
    const buildConversationHistory = (): ConversationMessage[] => {
        return messages
            .filter((m) => m.id !== "welcome")
            .map((m) => ({
                role: m.role,
                content: m.content,
            }));
    };

    const sendMessage = async () => {
        const text = input.trim();
        if (!text && selectedFiles.length === 0) return;

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
        setElapsedMs(0);

        try {
            const effectiveFormState = buildEffectiveFormState();

            const response = await sendChatMessage(
                text || `Please analyze the attached file(s): ${filesToSend?.map(f => f.name).join(', ')}`,
                effectiveFormState,
                buildConversationHistory(),
                filesToSend,
            );

            const msgId = crypto.randomUUID();
            let replyContent = response.reply ?? "";

            const hasUpdates = Array.isArray(response.field_updates) && response.field_updates.length > 0;
            const hasConflicts = Array.isArray(response.conflicts) && response.conflicts.length > 0;

            if (hasConflicts) {
                const conflictFields = response.conflicts
                    .map((c: any) => c.field_label || getFieldLabel(c.field_name))
                    .join(", ");
                if (hasUpdates) {
                    replyContent += `\n\nI've also noticed conflicting information for ${conflictFields}. Please review below and choose which values to keep.`;
                } else {
                    replyContent += `\n\nI found conflicting information for ${conflictFields}. Please review below.`;
                }
            }

            const assistantMsg: Message = {
                id: msgId,
                role: "assistant",
                content: replyContent,
                timestamp: new Date(),
                fieldUpdates: hasConflicts ? undefined : response.field_updates,
                conflicts: response.conflicts,
            };

            setMessages((prev) => [...prev, assistantMsg]);

            if (hasConflicts && hasUpdates) {
                queuedUpdatesRef.current[msgId] = response.field_updates;
            }

            if (!hasConflicts && hasUpdates) {
                const tracked: Record<string, TrackedFieldUpdate> = {};
                for (const update of response.field_updates) {
                    const u: any = update;
                    tracked[u.field_id] = { update, status: "pending" as FieldUpdateStatus };
                }
                setUpdateTracker((prev) => ({ ...prev, [msgId]: tracked }));
            }

            if (response.conflicts && response.conflicts.length > 0) {
                const tracked: Record<string, TrackedConflict> = {};
                for (const conflict of response.conflicts) {
                    const c: any = conflict;
                    tracked[c.conflict_id] = { conflict, resolution: "pending" as ConflictResolution };
                }
                setConflictTracker((prev) => ({ ...prev, [msgId]: tracked }));
            }
        } catch (error) {
            const errorMsg: Message = {
                id: crypto.randomUUID(),
                role: "assistant",
                content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : "Unknown error"}. Please try again.`,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMsg]);
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

    // --- Render helpers for updates/conflicts (basic) ---
    const renderFieldUpdatesCard = (msg: Message) => {
        if (!msg.fieldUpdates || msg.fieldUpdates.length === 0) return null;
        const msgUpdates = updateTracker[msg.id];
        if (!msgUpdates) {
            return (
                <div className="mt-2 rounded border border-border bg-card text-foreground text-xs px-2 py-1.5">
                    {msg.fieldUpdates.length} suggested change{msg.fieldUpdates.length !== 1 ? "s" : ""} loading...
                </div>
            );
        }

        const entries = Object.entries(msgUpdates);
        return (
            <div className="mt-2 rounded border border-border bg-card text-foreground text-xs overflow-hidden">
                <div className="flex items-center justify-between px-2 py-1.5 bg-muted/50 border-b border-border">
                    <span className="font-medium">Suggested changes</span>
                    <div className="text-xs text-muted-foreground">{entries.filter(([, t]) => t.status === "pending").length} pending</div>
                </div>
                <div className="divide-y divide-border">
                    {entries.map(([fieldId, tracked]) => (
                        <div key={fieldId} className="px-2 py-2 flex items-center justify-between">
                            <div>
                                <div className="font-medium text-sm">{getFieldLabel(fieldId)}</div>
                                <div className="text-xs text-muted-foreground">{String((tracked.update as any).new_value)}</div>
                            </div>
                            <div className="flex items-center gap-2">
                                {tracked.status === "pending" ? (
                                    <>
                                        <Button size="icon" onClick={() => acceptUpdate(msg.id, fieldId)} title="Accept"><Check className="h-4 w-4" /></Button>
                                        <Button size="icon" onClick={() => rejectUpdate(msg.id, fieldId)} title="Reject"><X className="h-4 w-4" /></Button>
                                    </>
                                ) : (
                                    <div className="text-xs">{tracked.status}</div>
                                )}
                            </div>
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
        return (
            <div className="mt-2 rounded border border-amber-300 bg-amber-50 text-foreground text-xs overflow-hidden">
                <div className="flex items-center justify-between px-2 py-1.5 bg-amber-100/50 border-b border-amber-200">
                    <span className="font-medium text-amber-800">Conflicts</span>
                    <div className="text-xs text-amber-700">{entries.filter(([, t]) => t.resolution === "pending").length} pending</div>
                </div>
                <div className="divide-y divide-amber-200">
                    {entries.map(([conflictId, tracked]) => {
                        const c: any = tracked.conflict;
                        return (
                            <div key={conflictId} className="px-2 py-2 flex items-center justify-between">
                                <div>
                                    <div className="font-medium text-sm">{c.field_label || getFieldLabel(c.field_name)}</div>
                                    <div className="text-xs text-muted-foreground">Current: {formatDisplayValue(c.current_value)} — Suggested: {formatDisplayValue(c.new_value)}</div>
                                </div>
                                <div className="flex items-center gap-2">
                                    {tracked.resolution === "pending" ? (
                                        <>
                                            <Button size="icon" onClick={() => resolveConflict(msg.id, conflictId, "use_new")} title="Use suggested">Use</Button>
                                            <Button size="icon" onClick={() => resolveConflict(msg.id, conflictId, "keep_existing")} title="Keep existing">Keep</Button>
                                        </>
                                    ) : (
                                        <div className="text-xs">{tracked.resolution}</div>
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
        <div
            className={`fixed bottom-20 right-6 z-50 flex flex-col rounded-xl border border-border bg-card shadow-2xl ${isOpen ? "" : "hidden"}`}
            style={{ width: `${chatSize.width}px`, height: `${chatSize.height}px` }}
        >
            <div className="relative flex items-center justify-between rounded-t-xl bg-primary px-4 py-3 overflow-hidden">
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

            <ScrollArea className="flex-1 px-4 py-3" ref={scrollRef}>
                <div className="space-y-4">
                    {messages.map((msg) => (
                        <div key={msg.id} className={`p-2 rounded ${msg.role === "assistant" ? "bg-muted/10" : "bg-card"}`}>
                            <div className="flex items-start justify-between gap-2">
                                <div>
                                    <div className="text-sm"><ReactMarkdown>{msg.content}</ReactMarkdown></div>
                                    {msg.fileAttachments && msg.fileAttachments.length > 0 && (
                                        <div className="mt-2 space-y-2">
                                            {msg.fileAttachments.map((att, i) => (
                                                <div key={i} className="flex items-center gap-2">
                                                    {att.type?.startsWith("audio") ? (
                                                        <audio controls src={att.url} />
                                                    ) : (
                                                        <a href={att.url} download={att.name} className="underline text-xs">{att.name}</a>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                    {renderFieldUpdatesCard(msg)}
                                    {renderConflictsCard(msg)}
                                </div>
                                <div className="text-xs text-muted-foreground">
                                    {msg.timestamp.toLocaleTimeString()}
                                    <div>
                                        <Button size="icon" onClick={() => toggleSave(msg.id)} title="Save"><Save className="h-4 w-4" /></Button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </ScrollArea>

            {messages.some((m) => m.saved) && (
                <div className="border-t border-border px-4 py-1.5">
                    <p className="text-[10px] text-muted-foreground">
                        Saved messages are marked for later review.
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
                    <input ref={fileInputRef} type="file" multiple className="hidden" onChange={handleFilePick} />
                    <Button
                        size="icon"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isTyping}
                        className="h-9 w-9 shrink-0"
                        title="Attach file"
                        aria-label="Attach file"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M21.44 11.05L12.95 1.56a6 6 0 00-8.48 8.48l8.49 8.49a4 4 0 005.66-5.66L10.12 5.35" />
                        </svg>
                    </Button>

                    <div className="flex items-center gap-2">
                        <Button
                            size="icon"
                            onClick={() => { if (isRecording) stopRecording(); else startRecording(); }}
                            disabled={isTyping}
                            className={`relative h-9 w-9 shrink-0 ${isRecording ? "bg-red-600/80 hover:bg-red-600" : ""}`}
                            title={isRecording ? "Stop recording" : "Record audio"}
                            aria-label="Record audio"
                        >
                            <Mic className="h-4 w-4" />
                            {isRecording && (
                                // diagonal dash across the icon
                                <span className="pointer-events-none absolute inset-0 flex items-center justify-center">
                                    <span className="block w-[2px] h-5 bg-white/90 rotate-45" />
                                </span>
                            )}
                        </Button>

                        {isRecording && (
                            <div className="flex items-center gap-2">
                                <span className="text-[11-px] font-mono text-foreground/90 select-none">{formatTime(elapsedMs)}</span>
                                <Button size="icon" onClick={cancelRecording} title="Cancel recording" aria-label="Cancel recording">
                                    <span className="text-sm">✕</span>
                                </Button>
                            </div>
                        )}
                    </div>

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

                {selectedFiles.length > 0 && (
                    <div className="mt-2 flex flex-col gap-2 max-h-[120px] overflow-y-auto pr-1">
                        {selectedFiles.map((file, idx) => (
                            <div key={idx} className="flex items-center justify-between gap-2 rounded border border-border px-2 py-1 text-sm">
                                <div className="flex items-center gap-2 flex-1 min-w-0">
                                    {file.type.startsWith("audio") ? (
                                        <audio controls src={previewUrls[idx]} className="w-full h-6 max-w-full" />
                                    ) : (
                                        <span className="text-xs truncate">{file.name}</span>
                                    )}
                                </div>
                                <div className="flex items-center gap-2 shrink-0">
                                    <Button
                                        size="icon"
                                        onClick={() => removeSelectedFile(idx)}
                                        title="Remove"
                                        aria-label="Remove"
                                        className="h-7 w-7 p-1"
                                    >
                                        <X className="h-3 w-3" />
                                    </Button>
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
