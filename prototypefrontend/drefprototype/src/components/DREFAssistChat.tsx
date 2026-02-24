import { useState, useRef, useEffect } from "react";
import { Bot, Send, X, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";

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
    fileAttachment?: FileAttachment;
}

const PLACEHOLDER_RESPONSES = [
    "Based on the DREF guidelines, I'd recommend focusing on the most vulnerable populations first. Would you like me to help draft the targeting strategy section?",
    "For the operational timeframe, DREF operations typically run between 2-6 months. Consider the scale of the disaster and your National Society's capacity when setting the duration.",
    "The budget summary should align with your planned interventions. Make sure each sector (Shelter, WASH, Health, etc.) has a corresponding budget line item.",
    "When describing the event, be sure to include: 1) What happened, 2) Where it occurred, 3) When it started, and 4) The scale of impact with numeric data.",
    "For the risk analysis section, consider security risks, operational constraints, and any access limitations. The IFRC Risk Management Framework Annex III provides useful categories.",
    "I can help you draft the objective statement. A good format is: 'The operation aims to [action] for [number] [target population] affected by [disaster] in [location] over [timeframe].'",
];

const DREFAssistChat = ({ onClose }: { onClose: () => void }) => {
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
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);

    const scrollRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Keep track of created object URLs so we can revoke them on unmount
    const createdUrlsRef = useRef<Set<string>>(new Set());

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isTyping]);

    useEffect(() => {
        return () => {
            // Revoke all created object URLs when component unmounts
            createdUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
            createdUrlsRef.current.clear();
        };
    }, []);

    const handleFilePick = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0] ?? null;
        if (!file) return;

        // Revoke previous preview if any
        if (previewUrl) {
            URL.revokeObjectURL(previewUrl);
            createdUrlsRef.current.delete(previewUrl);
        }

        const url = URL.createObjectURL(file);
        createdUrlsRef.current.add(url);
        setSelectedFile(file);
        setPreviewUrl(url);

        // Clear the native input's value so same file can be picked again if needed
        if (fileInputRef.current) fileInputRef.current.value = "";
    };

    const removeSelectedFile = () => {
        if (previewUrl) {
            URL.revokeObjectURL(previewUrl);
            createdUrlsRef.current.delete(previewUrl);
        }
        setSelectedFile(null);
        setPreviewUrl(null);
    };

    const sendMessage = () => {
        const text = input.trim();
        if (!text && !selectedFile) return;

        const userMsg: Message = {
            id: crypto.randomUUID(),
            role: "user",
            content: text || (selectedFile ? `Sent a file: ${selectedFile.name}` : ""),
            timestamp: new Date(),
            fileAttachment: selectedFile
                ? {
                    name: selectedFile.name,
                    url:
                        previewUrl ??
                        (selectedFile ? URL.createObjectURL(selectedFile) : ""),
                    type: selectedFile.type,
                    size: selectedFile.size,
                }
                : undefined,
        };

        // If we created a URL here (in case previewUrl was null), add it to tracking
        if (userMsg.fileAttachment?.url) {
            createdUrlsRef.current.add(userMsg.fileAttachment.url);
        }

        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setIsTyping(true);
        // clear selected file after sending
        setSelectedFile(null);
        setPreviewUrl(null);

        // Simulate LLM response
        setTimeout(() => {
            const reply =
                PLACEHOLDER_RESPONSES[
                    Math.floor(Math.random() * PLACEHOLDER_RESPONSES.length)
                    ];
            setMessages((prev) => [
                ...prev,
                {
                    id: crypto.randomUUID(),
                    role: "assistant",
                    content: reply,
                    timestamp: new Date(),
                },
            ]);
            setIsTyping(false);
        }, 1200);
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

    return (
        <div className="fixed bottom-20 right-6 z-50 flex h-[520px] w-[380px] flex-col rounded-xl border border-border bg-card shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between rounded-t-xl bg-primary px-4 py-3">
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
                            className={`flex flex-col ${
                                msg.role === "user" ? "items-end" : "items-start"
                            }`}
                        >
                            <div
                                className={`group relative max-w-[85%] rounded-lg px-3 py-2 text-sm leading-relaxed ${
                                    msg.role === "user"
                                        ? "bg-primary text-primary-foreground"
                                        : "bg-muted text-foreground"
                                }`}
                            >
                                <div className="break-words">{msg.content}</div>

                                {msg.fileAttachment && (
                                    <div className="mt-2">
                                        <a
                                            href={msg.fileAttachment.url}
                                            download={msg.fileAttachment.name}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="inline-flex items-center gap-2 rounded px-2 py-1 text-xs bg-secondary/10 hover:bg-secondary/20"
                                        >
                                            <svg
                                                xmlns="http://www.w3.org/2000/svg"
                                                className="h-4 w-4"
                                                viewBox="0 0 24 24"
                                                fill="none"
                                                stroke="currentColor"
                                                strokeWidth="2"
                                            >
                                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                                <polyline points="7 10 12 15 17 10" />
                                                <line x1="12" y1="15" x2="12" y2="3" />
                                            </svg>
                                            <span className="truncate max-w-[160px]">
                        {msg.fileAttachment.name}
                      </span>
                                            <span className="text-[10px] text-muted-foreground">
                        {msg.fileAttachment.size
                            ? ` • ${Math.round(msg.fileAttachment.size / 1024)} KB`
                            : ""}
                      </span>
                                        </a>
                                    </div>
                                )}

                                {/* Save button on hover */}
                                <button
                                    onClick={() => toggleSave(msg.id)}
                                    className={`absolute -right-7 top-1 rounded p-0.5 transition-opacity ${
                                        msg.saved
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
                <span className="inline-flex gap-1">
                  <span className="animate-bounce">·</span>
                  <span
                      className="animate-bounce"
                      style={{ animationDelay: "0.1s" }}
                  >
                    ·
                  </span>
                  <span
                      className="animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                  >
                    ·
                  </span>
                </span>
                            </div>
                        </div>
                    )}
                </div>
            </ScrollArea>

            {/* Saved prompts indicator */}
            {messages.some((m) => m.saved) && (
                <div className="border-t border-border px-4 py-1.5">
                    <p className="text-[10px] text-muted-foreground">
                        {messages.filter((m) => m.saved).length} prompt(s) saved
                    </p>
                </div>
            )}

            {/* Input */}
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
                    <input
                        ref={fileInputRef}
                        type="file"
                        className="hidden"
                        onChange={handleFilePick}
                    />
                    <Button
                        size="icon"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isTyping}
                        className="h-9 w-9 shrink-0"
                        title="Attach file"
                        aria-label="Attach file"
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-4 w-4"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                        >
                            <path d="M21.44 11.05L12.6 19.9a5.5 5.5 0 0 1-7.78 0 5.5 5.5 0 0 1 0-7.78l8.84-8.84a3.5 3.5 0 0 1 4.95 4.95L10 17.1" />
                        </svg>
                    </Button>
                    <Button
                        size="icon"
                        onClick={sendMessage}
                        disabled={(!input.trim() && !selectedFile) || isTyping}
                        className="h-9 w-9 shrink-0"
                        title="Send"
                        aria-label="Send"
                    >
                        <Send className="h-4 w-4" />
                    </Button>
                </div>

                {selectedFile && previewUrl && (
                    <div className="mt-2 flex items-center justify-between gap-2 rounded border border-border px-2 py-1 text-sm">
                        <div className="flex items-center gap-2">
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                className="h-5 w-5 text-muted-foreground"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                            >
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                <polyline points="7 10 12 15 17 10" />
                                <line x1="12" y1="15" x2="12" y2="3" />
                            </svg>
                            <div className="truncate max-w-[220px]">
                                {selectedFile.name}{" "}
                                <span className="text-[11px] text-muted-foreground">
                  • {Math.round(selectedFile.size / 1024)} KB
                </span>
                            </div>
                        </div>
                        <div className="flex items-center gap-1">
                            <Button size="icon" onClick={removeSelectedFile} className="h-7 w-7">
                                <X className="h-3.5 w-3.5" />
                            </Button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DREFAssistChat;
