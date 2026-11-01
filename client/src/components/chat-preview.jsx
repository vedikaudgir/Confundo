function MessageBubble({ message }) {
    return (
        <div className={`chat-preview__message${message.sender === "me" ? " chat-preview__message--outbound" : ""}`}>
            <p>{message.text}</p>
            <time>{message.timestamp}</time>
        </div>
    );
}

export function ChatPreview({ config, messages }) {
    const platform = config.platform || "whatsapp";
    const theme = config.theme || "light";

    return (
        <div
            className={`chat-preview chat-preview--${platform}`}
            data-theme={theme}
            aria-label={`${platform} chat preview`}
        >
            <div className="chat-preview__header">
                <span className="chat-preview__avatar" aria-hidden="true">
                    {(config.title || "C").trim().charAt(0).toUpperCase()}
                </span>
                <div className="chat-preview__identity">
                    <strong>{config.title || "Your chat"}</strong>
                    <span>{config.subtitle || " "}</span>
                </div>
                <span className="chat-preview__header-mark" aria-hidden="true">•••</span>
            </div>
            <div className="chat-preview__body">
                {messages.length === 0 ? (
                    <div className="chat-preview__empty">
                        <span className="chat-preview__empty-icon" aria-hidden="true">Aa</span>
                        <strong>Your conversation starts here</strong>
                        <span>Add a message to see it in the preview.</span>
                    </div>
                ) : (
                    <div className="chat-preview__messages">
                        {messages.map((message) => (
                            <MessageBubble key={message.id} message={message} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
