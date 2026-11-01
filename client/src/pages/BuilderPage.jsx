import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
    ArrowDownToLine,
    Check,
    ImagePlus,
    LoaderCircle,
    Pencil,
    Plus,
    RotateCcw,
    Send,
    Trash2,
    X,
} from "lucide-react";
import { chatApi } from "../api/chatApi";
import { ChatPreview } from "../components/chat-preview";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";

const PLATFORMS = [
    { id: "whatsapp", name: "WhatsApp", mark: "W", detail: "Friendly, familiar chats" },
    { id: "instagram", name: "Instagram DM", mark: "IG", detail: "A direct-message look" },
    { id: "chatgpt", name: "ChatGPT", mark: "GPT", detail: "User and assistant replies" },
];
const VALID_PLATFORMS = PLATFORMS.map((platform) => platform.id);

function platformLabel(platform) {
    return PLATFORMS.find((item) => item.id === platform)?.name || "WhatsApp";
}

export function BuilderPage() {
    const [searchParams, setSearchParams] = useSearchParams();
    const requestedPlatform = searchParams.get("platform");
    const requestedChat = searchParams.get("chat");
    const [config, setConfig] = useState(() => ({
        platform: VALID_PLATFORMS.includes(requestedPlatform) ? requestedPlatform : "whatsapp",
        title: "My Chat",
        subtitle: "online",
        theme: "light",
        myName: "You",
        otherName: "Friend",
    }));
    const [messages, setMessages] = useState([]);
    const [sender, setSender] = useState("me");
    const [messageText, setMessageText] = useState("");
    const [timestamp, setTimestamp] = useState("12:30 PM");
    const [editingId, setEditingId] = useState(null);
    const [chatId, setChatId] = useState(null);
    const [meId, setMeId] = useState(null);
    const [otherId, setOtherId] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(null);
    const [isSyncing, setIsSyncing] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [isExporting, setIsExporting] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const debounceTimer = useRef(null);
    const avatarInputRef = useRef(null);
    const previewObjectUrl = useRef(null);

    const loadPreview = async (targetChatId) => {
        const response = await chatApi.getChatPreview(targetChatId);
        const nextUrl = URL.createObjectURL(await response.blob());
        if (previewObjectUrl.current) URL.revokeObjectURL(previewObjectUrl.current);
        previewObjectUrl.current = nextUrl;
        setPreviewUrl(nextUrl);
    };

    useEffect(() => () => {
        clearTimeout(debounceTimer.current);
        if (previewObjectUrl.current) URL.revokeObjectURL(previewObjectUrl.current);
    }, []);

    useEffect(() => {
        if (!requestedChat) return undefined;
        let active = true;
        chatApi.getChat(requestedChat)
            .then(async (savedChat) => {
                if (!active) return;
                const me = savedChat.participants.find((participant) => participant.role === "me");
                const other = savedChat.participants.find((participant) => participant.role === "other");
                setConfig({
                    platform: savedChat.platform,
                    title: savedChat.title,
                    subtitle: savedChat.subtitle,
                    theme: savedChat.theme,
                    myName: me?.name || "You",
                    otherName: other?.name || "Friend",
                });
                setMessages(savedChat.messages.map((message) => ({
                    id: message.id,
                    sender: message.sender_role,
                    text: message.content,
                    timestamp: message.timestamp,
                    type: message.message_type,
                    direction: message.direction,
                })));
                setChatId(savedChat.id);
                setMeId(me?.id || null);
                setOtherId(other?.id || null);
                await loadPreview(savedChat.id);
            })
            .catch((error) => {
                console.error("Could not load saved chat:", error);
                if (active) setErrorMessage(`Could not load this chat: ${error.message}`);
            });
        return () => {
            active = false;
        };
    }, [requestedChat]);

    useEffect(() => {
        if (!chatId) return undefined;

        clearTimeout(debounceTimer.current);
        debounceTimer.current = setTimeout(async () => {
            setIsSyncing(true);
            try {
                await chatApi.updateChat(chatId, config);
                await loadPreview(chatId);
                setErrorMessage("");
            } catch (error) {
                console.error("Failed to sync chat settings:", error);
                setErrorMessage(`Could not save your chat settings: ${error.message}`);
            } finally {
                setIsSyncing(false);
            }
        }, 650);

        return () => clearTimeout(debounceTimer.current);
    }, [config, chatId]);

    const updateConfig = (key, value) => {
        setConfig((current) => ({ ...current, [key]: value }));
    };

    const selectPlatform = (platform) => {
        setConfig((current) => ({
            ...current,
            platform,
            theme: platform === "whatsapp" ? "light" : current.theme,
        }));
    };

    const clearEditor = () => {
        setEditingId(null);
        setMessageText("");
        setTimestamp("12:30 PM");
    };

    const handleAddMessage = async (event) => {
        event.preventDefault();
        const content = messageText.trim();
        if (!content || isSyncing) return;

        setIsSyncing(true);
        setErrorMessage("");
        try {
            let currentChatId = chatId;
            if (!currentChatId) {
                const created = await chatApi.createChat(config);
                currentChatId = created.chat_id;
                setChatId(currentChatId);
                setMeId(created.me_id);
                setOtherId(created.other_id);
            }

            const direction = sender === "me" ? "outbound" : "inbound";
            const result = await chatApi.addMessage(currentChatId, {
                sender_role: sender,
                type: "text",
                content,
                timestamp,
                direction,
            });

            setMessages((current) => [
                ...current,
                {
                    id: result.message_id,
                    sender,
                    text: content,
                    timestamp,
                    type: "text",
                    direction,
                },
            ]);
            clearEditor();
            await loadPreview(currentChatId);
        } catch (error) {
            console.error("Failed to add message:", error);
            setErrorMessage(`Could not add your message: ${error.message}`);
        } finally {
            setIsSyncing(false);
        }
    };

    const handleEditMessage = async (message) => {
        setEditingId(message.id);
        setSender(message.sender);
        setMessageText(message.text);
        setTimestamp(message.timestamp);
        document.getElementById("message-content")?.focus();
    };

    const handleSaveEdit = async (event) => {
        event.preventDefault();
        const content = messageText.trim();
        if (!chatId || !editingId || !content || isSyncing) return;

        setIsSyncing(true);
        setErrorMessage("");
        try {
            await chatApi.updateMessage(chatId, editingId, { content, timestamp });
            setMessages((current) => current.map((message) => (
                message.id === editingId ? { ...message, text: content, timestamp } : message
            )));
            clearEditor();
            await loadPreview(chatId);
        } catch (error) {
            console.error("Failed to update message:", error);
            setErrorMessage(`Could not update your message: ${error.message}`);
        } finally {
            setIsSyncing(false);
        }
    };

    const handleDeleteMessage = async (message) => {
        if (!chatId || isSyncing) return;

        setIsSyncing(true);
        setErrorMessage("");
        try {
            await chatApi.deleteMessage(chatId, message.id);
            setMessages((current) => current.filter((item) => item.id !== message.id));
            if (editingId === message.id) clearEditor();
            await loadPreview(chatId);
        } catch (error) {
            console.error("Failed to delete message:", error);
            setErrorMessage(`Could not remove your message: ${error.message}`);
        } finally {
            setIsSyncing(false);
        }
    };

    const handleAvatarUpload = async (event) => {
        const file = event.target.files?.[0];
        event.target.value = "";
        if (!file) return;
        if (!file.type.startsWith("image/")) {
            setErrorMessage("Choose an image file to use as a profile photo.");
            return;
        }
        if (!chatId) return;

        setIsUploading(true);
        setErrorMessage("");
        try {
            await chatApi.uploadAvatar(sender === "me" ? meId : otherId, file);
            await loadPreview(chatId);
        } catch (error) {
            console.error("Avatar upload failed:", error);
            setErrorMessage(`Could not upload the profile photo: ${error.message}`);
        } finally {
            setIsUploading(false);
        }
    };

    const handleDownloadImage = async () => {
        if (!previewUrl || isExporting) return;

        setIsExporting(true);
        setErrorMessage("");
        try {
            const response = await chatApi.generateChatImage(chatId);
            const image = await response.blob();
            const downloadUrl = URL.createObjectURL(image);
            const link = document.createElement("a");
            link.href = downloadUrl;
            link.download = `chattiebaby-${config.platform}.png`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);
        } catch (error) {
            console.error("Image export failed:", error);
            setErrorMessage(`Could not export the image: ${error.message}`);
        } finally {
            setIsExporting(false);
        }
    };

    const startNewChat = () => {
        clearTimeout(debounceTimer.current);
        const nextSearchParams = new URLSearchParams(searchParams);
        nextSearchParams.delete("chat");
        nextSearchParams.set("platform", config.platform);
        setSearchParams(nextSearchParams, { replace: true });
        clearEditor();
        setMessages([]);
        setChatId(null);
        setMeId(null);
        setOtherId(null);
        if (previewObjectUrl.current) URL.revokeObjectURL(previewObjectUrl.current);
        previewObjectUrl.current = null;
        setPreviewUrl(null);
        setSender("me");
        setErrorMessage("");
    };

    const selectedPlatform = platformLabel(config.platform);
    const otherLabel = config.platform === "chatgpt" ? "Assistant" : "Other person";

    return (
        <div className="generator-page">
            <section className="page-intro page-intro--wide">
                <div>
                    <span className="eyebrow">The chat generator</span>
                    <h1>Build the conversation.</h1>
                    <p className="page-intro__copy">
                        Write a fictional exchange and turn it into a chat-style image.
                    </p>
                </div>
                <div className="creation-steps" aria-label="Creation steps">
                    <span><b>01</b> Set up</span>
                    <span className="creation-steps__divider" />
                    <span><b>02</b> Write</span>
                    <span className="creation-steps__divider" />
                    <span><b>03</b> Save</span>
                </div>
            </section>

            {errorMessage && (
                <div className="feedback-message" role="alert">{errorMessage}</div>
            )}

            <section className="platform-picker" aria-labelledby="platform-heading">
                <div className="platform-picker__heading">
                    <div>
                        <span className="eyebrow">Choose a style</span>
                        <h2 id="platform-heading">Where does the chat happen?</h2>
                    </div>
                    <span className="fictional-note">Fictional conversations only</span>
                </div>
                <div className="platform-choices" role="group" aria-label="Chat platform">
                    {PLATFORMS.map((platform) => (
                        <button
                            type="button"
                            key={platform.id}
                            className={`platform-choice${config.platform === platform.id ? " is-selected" : ""}`}
                            aria-pressed={config.platform === platform.id}
                            onClick={() => selectPlatform(platform.id)}
                        >
                            <span className="platform-choice__mark">{platform.mark}</span>
                            <span>
                                <strong>{platform.name}</strong>
                                <small>{platform.detail}</small>
                            </span>
                            {config.platform === platform.id && <Check size={16} />}
                        </button>
                    ))}
                </div>
            </section>

            <div className="workspace-grid">
                <section className="workspace-panel setup-panel" aria-labelledby="setup-title">
                    <div className="panel-heading">
                        <span className="step-number">01</span>
                        <div>
                            <h2 id="setup-title">Set up your chat</h2>
                            <p>Choose the names and look for the conversation.</p>
                        </div>
                    </div>

                    <div className="panel-fields">
                        <div className="field-pair">
                            <div className="form-field">
                                <Label htmlFor="theme">Appearance</Label>
                                <select
                                    id="theme"
                                    className="form-control"
                                    value={config.theme}
                                    disabled={config.platform === "whatsapp"}
                                    onChange={(event) => updateConfig("theme", event.target.value)}
                                >
                                    <option value="light">Light</option>
                                    <option value="dark">Dark</option>
                                </select>
                            </div>
                            <div className="form-field">
                                <Label htmlFor="chat-subtitle">Status line</Label>
                                <Input
                                    id="chat-subtitle"
                                    value={config.subtitle}
                                    onChange={(event) => updateConfig("subtitle", event.target.value)}
                                    className="form-control"
                                    placeholder="online, typing..."
                                    maxLength={80}
                                />
                            </div>
                        </div>
                        <div className="form-field">
                            <Label htmlFor="chat-title">Conversation title</Label>
                            <Input
                                id="chat-title"
                                value={config.title}
                                onChange={(event) => updateConfig("title", event.target.value)}
                                className="form-control"
                                placeholder="Give this chat a name"
                                maxLength={80}
                            />
                        </div>
                        <div className="field-divider" />
                        <div className="form-field">
                            <Label htmlFor="my-name">Your name</Label>
                            <Input
                                id="my-name"
                                value={config.myName}
                                onChange={(event) => updateConfig("myName", event.target.value)}
                                className="form-control"
                                placeholder="You"
                                maxLength={60}
                            />
                        </div>
                        <div className="form-field">
                            <Label htmlFor="other-name">{otherLabel}&apos;s name</Label>
                            <Input
                                id="other-name"
                                value={config.otherName}
                                onChange={(event) => updateConfig("otherName", event.target.value)}
                                className="form-control"
                                placeholder="Friend or character"
                                maxLength={60}
                            />
                        </div>
                        <div className="helper-note">
                            <span className="helper-note__line" />
                            {config.platform === "whatsapp"
                                ? "WhatsApp keeps its original light Pillow renderer."
                                : "Changes sync with the Pillow preview after you create the first message."}
                        </div>
                    </div>
                </section>

                <section className="workspace-panel compose-panel" aria-labelledby="compose-title">
                    <div className="panel-heading">
                        <span className="step-number">02</span>
                        <div>
                            <h2 id="compose-title">Write the conversation</h2>
                            <p>Add, edit, or remove individual messages.</p>
                        </div>
                    </div>

                    <div className="message-list" aria-label="Conversation messages">
                        {messages.length === 0 ? (
                            <div className="message-list__empty">
                                <span className="message-list__empty-icon">Aa</span>
                                <strong>Your first line sets the scene.</strong>
                                <span>Write a message below to get started.</span>
                            </div>
                        ) : messages.map((message, index) => (
                            <article
                                className={`message-row${message.sender === "me" ? " message-row--mine" : ""}`}
                                key={message.id}
                            >
                                <div className="message-row__meta">
                                    <span>{message.sender === "me" ? config.myName || "You" : config.otherName || "Friend"}</span>
                                    <time>{message.timestamp}</time>
                                </div>
                                <p>{message.text}</p>
                                <div className="message-row__actions">
                                    <button
                                        type="button"
                                        className="icon-button"
                                        onClick={() => handleEditMessage(message)}
                                        aria-label={`Edit message ${index + 1}`}
                                        disabled={isSyncing}
                                    >
                                        <Pencil size={14} />
                                    </button>
                                    <button
                                        type="button"
                                        className="icon-button icon-button--danger"
                                        onClick={() => handleDeleteMessage(message)}
                                        aria-label={`Delete message ${index + 1}`}
                                        disabled={isSyncing}
                                    >
                                        <Trash2 size={14} />
                                    </button>
                                </div>
                            </article>
                        ))}
                    </div>

                    <form
                        className="panel-fields composer-form"
                        onSubmit={editingId ? handleSaveEdit : handleAddMessage}
                    >
                        <div className="field-pair">
                            <div className="form-field">
                                <Label htmlFor="sender">Speaking as</Label>
                                <select
                                    id="sender"
                                    className="form-control"
                                    value={sender}
                                    onChange={(event) => setSender(event.target.value)}
                                >
                                    <option value="me">{config.myName || "You"} · outgoing</option>
                                    <option value="other">{config.otherName || otherLabel} · incoming</option>
                                </select>
                            </div>
                            <div className="form-field">
                                <Label htmlFor="timestamp">Time</Label>
                                <Input
                                    id="timestamp"
                                    value={timestamp}
                                    onChange={(event) => setTimestamp(event.target.value)}
                                    className="form-control"
                                    placeholder="12:30 PM"
                                    maxLength={24}
                                />
                            </div>
                        </div>
                        <div className="form-field message-field">
                            <Label htmlFor="message-content">{editingId ? "Edit message" : "Message"}</Label>
                            <Textarea
                                id="message-content"
                                placeholder="What happens next?"
                                value={messageText}
                                onChange={(event) => setMessageText(event.target.value)}
                                className="form-control message-input"
                                onKeyDown={(event) => {
                                    if (event.key === "Enter" && !event.shiftKey) {
                                        event.preventDefault();
                                        event.currentTarget.form?.requestSubmit();
                                    }
                                }}
                            />
                            <span className="field-hint">Enter to add · Shift + Enter for a new line</span>
                        </div>
                        <div className="button-row composer-actions">
                            <Button
                                type="submit"
                                disabled={isSyncing || !messageText.trim()}
                                className="action-button action-button--primary"
                            >
                                {isSyncing ? (
                                    <LoaderCircle className="icon-spin" size={17} />
                                ) : editingId ? (
                                    <Check size={16} />
                                ) : (
                                    <Plus size={17} />
                                )}
                                {isSyncing ? "Saving…" : editingId ? "Save changes" : "Add message"}
                            </Button>
                            {editingId && (
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={clearEditor}
                                    className="action-button action-button--secondary"
                                >
                                    <X size={16} /> Cancel
                                </Button>
                            )}
                        </div>

                        <div className="avatar-section">
                            <div>
                                <h3>Profile photo</h3>
                                <p>
                                    {chatId
                                        ? `Upload a photo for ${sender === "me" ? config.myName || "your" : config.otherName || "the other"} side.`
                                        : "Add the first message to create a chat before uploading a photo."}
                                </p>
                            </div>
                            <input
                                ref={avatarInputRef}
                                type="file"
                                className="visually-hidden"
                                accept="image/*"
                                onChange={handleAvatarUpload}
                                disabled={!chatId || isUploading}
                                aria-label="Choose a profile photo"
                            />
                            <Button
                                type="button"
                                variant="outline"
                                onClick={() => avatarInputRef.current?.click()}
                                disabled={!chatId || isUploading}
                                className="action-button action-button--secondary"
                            >
                                {isUploading ? (
                                    <LoaderCircle className="icon-spin" size={17} />
                                ) : (
                                    <ImagePlus size={17} />
                                )}
                                {isUploading ? "Uploading…" : "Choose photo"}
                            </Button>
                        </div>
                    </form>
                </section>

                <section className="workspace-panel preview-panel" aria-labelledby="preview-title">
                    <div className="panel-heading panel-heading--preview">
                        <span className="step-number">03</span>
                        <div>
                            <h2 id="preview-title">Preview &amp; export</h2>
                            <p>Your {selectedPlatform} screenshot.</p>
                        </div>
                        <div className={`save-status${isSyncing ? " save-status--busy" : ""}`} role="status">
                            <span className="save-status__icon">
                                {isSyncing ? <LoaderCircle className="icon-spin" size={14} /> : <Check size={14} />}
                            </span>
                            {isSyncing ? "Updating" : previewUrl ? "Pillow preview" : "Draft preview"}
                        </div>
                    </div>

                    <div className={`preview-stage${previewUrl ? " preview-stage--image" : ""}`}>
                        {previewUrl ? (
                            <img
                                key={previewUrl}
                                className="generated-image"
                                src={previewUrl}
                                alt={`Generated ${selectedPlatform} chat screenshot`}
                                onError={() => {
                                    setErrorMessage("The generated image could not be loaded. Check the API connection and try again.");
                                    setPreviewUrl(null);
                                }}
                            />
                        ) : (
                            <ChatPreview config={config} messages={messages} />
                        )}
                    </div>

                    <div className="preview-actions">
                        <div className="preview-caption">
                            <span>{messages.length} {messages.length === 1 ? "message" : "messages"}</span>
                            <span className="preview-caption__separator" />
                            <span>{selectedPlatform}</span>
                            <span className="preview-caption__separator" />
                            <span>{previewUrl ? "Generated image" : "Draft"}</span>
                        </div>
                        <div className="button-row">
                            <Button
                                type="button"
                                variant="outline"
                                onClick={startNewChat}
                                disabled={isSyncing || isUploading || isExporting}
                                className="action-button action-button--secondary reset-button"
                            >
                                <RotateCcw size={16} /> New chat
                            </Button>
                            <Button
                                type="button"
                                onClick={handleDownloadImage}
                                disabled={!previewUrl || isExporting}
                                className="action-button action-button--primary export-button"
                            >
                                {isExporting ? (
                                    <LoaderCircle className="icon-spin" size={17} />
                                ) : (
                                    <ArrowDownToLine size={17} />
                                )}
                                {isExporting ? "Preparing…" : "Download image"}
                            </Button>
                        </div>
                        {chatId && (
                            <div className="preview-footnote">
                                New chat clears this workspace; previous chat records remain on the server.
                            </div>
                        )}
                    </div>
                </section>
            </div>
        </div>
    );
}

export default BuilderPage;
