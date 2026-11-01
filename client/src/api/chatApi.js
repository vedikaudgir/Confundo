export const API_BASE_URL = (
    import.meta.env.VITE_API_BASE_URL ||
    (import.meta.env.DEV
        ? "http://localhost:8000"
        : "https://chatmemegenerator-production.up.railway.app")
).replace(/\/+$/, "");

const PUBLIC_PATHS = ["/examples"];
const AUTH_NO_REFRESH = ["/auth/login", "/auth/register", "/auth/logout", "/auth/refresh"];
let refreshInFlight = null;

function csrfToken() {
    if (typeof document === "undefined") return "";
    const cookie = document.cookie
        .split("; ")
        .find((item) => item.startsWith("chattiebaby_csrf="));
    return cookie ? decodeURIComponent(cookie.slice("chattiebaby_csrf=".length)) : "";
}

function hasSessionHint() {
    return Boolean(csrfToken());
}

function expireFrontendSession() {
    if (typeof window !== "undefined") {
        window.dispatchEvent(new Event("chattiebaby:session-expired"));
    }
}

function requestHeaders(options) {
    const headers = new Headers(options.headers || {});
    const method = (options.method || "GET").toUpperCase();
    if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
        const token = csrfToken();
        if (token) headers.set("X-CSRF-Token", token);
    }
    return headers;
}

async function parseResponse(response) {
    if (response.status === 204) return null;
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) return response.json();
    return response;
}

async function refreshSession() {
    if (!refreshInFlight) {
        refreshInFlight = fetch(`${API_BASE_URL}/auth/refresh`, {
            method: "POST",
            credentials: "include",
            headers: requestHeaders({ method: "POST" }),
        }).finally(() => {
            refreshInFlight = null;
        });
    }
    const response = await refreshInFlight;
    if (!response.ok) {
        expireFrontendSession();
        return false;
    }
    return true;
}

async function request(path, options = {}, canRefresh = true) {
    const mayRefresh = hasSessionHint();
    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        credentials: "include",
        headers: requestHeaders(options),
    });

    if (
        response.status === 401 &&
        canRefresh &&
        mayRefresh &&
        !AUTH_NO_REFRESH.includes(path) &&
        !PUBLIC_PATHS.some((publicPath) => path.startsWith(publicPath))
    ) {
        if (await refreshSession()) return request(path, options, false);
    }
    if (!response.ok) {
        let detail = `Request failed (${response.status})`;
        try {
            const body = await response.json();
            detail = typeof body.detail === "string"
                ? body.detail
                : body.detail
                    ? JSON.stringify(body.detail)
                    : detail;
        } catch {
            // Proxies can return non-JSON error pages.
        }
        const error = new Error(detail);
        error.status = response.status;
        throw error;
    }
    return parseResponse(response);
}

const jsonRequest = (method, body) => ({
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
});

export const chatApi = {
    hasSessionCookieHint: hasSessionHint,
    register: (data) => request("/auth/register", jsonRequest("POST", data), false),
    login: (data) => request("/auth/login", jsonRequest("POST", data), false),
    logout: () => request("/auth/logout", { method: "POST" }, false),
    getMe: () => request("/auth/me"),
    updateProfile: (data) => request("/users/me", jsonRequest("PATCH", data)),
    changePassword: (data) => request("/users/me/password", jsonRequest("PATCH", data)),
    deleteAccount: (password) => request("/users/me", jsonRequest("DELETE", { password })),
    getSettings: () => request("/settings/me"),
    updateSettings: (data) => request("/settings/me", jsonRequest("PATCH", data)),
    listChats: () => request("/chats"),
    getChat: (chatId) => request(`/chats/${chatId}/data`),
    deleteChat: (chatId) => request(`/chats/${chatId}`, { method: "DELETE" }),
    listHistory: () => request("/history"),
    deleteHistory: (historyId) => request(`/history/${historyId}`, { method: "DELETE" }),
    getHistoryImage: (historyId) => request(`/history/${historyId}/image`),
    getChatPreview: (chatId) => request(`/chats/${chatId}/preview?time=${Date.now()}`),
    generateChatImage: (chatId) => request(`/chats/${chatId}/generate`, { method: "POST" }),

    createChat: (chatConfig) => request("/chats", jsonRequest("POST", {
        platform: chatConfig.platform.toLowerCase(),
        title: chatConfig.title,
        subtitle: chatConfig.subtitle,
        theme: chatConfig.theme || "light",
        my_name: chatConfig.myName || "You",
        other_name: chatConfig.otherName || chatConfig.title || "Friend",
    })),

    updateChat: (chatId, chatConfig) => request(`/chats/${chatId}`, jsonRequest("PATCH", {
        platform: chatConfig.platform,
        title: chatConfig.title,
        subtitle: chatConfig.subtitle,
        theme: chatConfig.theme || "light",
        my_name: chatConfig.myName || "You",
        other_name: chatConfig.otherName || chatConfig.title || "Friend",
    })),

    addMessage: (chatId, messageData) => request(
        `/chats/${chatId}/messages`,
        jsonRequest("POST", {
            sender_role: messageData.sender_role || messageData.sender,
            type: messageData.type || "text",
            content: messageData.content,
            timestamp: messageData.timestamp,
            direction: messageData.direction,
            reply_to: messageData.reply_to,
            meta: messageData.meta,
        }),
    ),

    updateMessage: (chatId, messageId, message) => request(
        `/chats/${chatId}/messages/${messageId}`,
        jsonRequest("PATCH", message),
    ),

    deleteMessage: (chatId, messageId) => request(
        `/chats/${chatId}/messages/${messageId}`,
        { method: "DELETE" },
    ),

    addParticipant: (chatId, data) => request(
        `/participants/chats/${chatId}`,
        jsonRequest("POST", data),
    ),

    updateParticipant: (participantId, name) => request(
        `/participants/${participantId}`,
        jsonRequest("PATCH", { name }),
    ),

    deleteParticipant: (participantId) => request(
        `/participants/${participantId}`,
        { method: "DELETE" },
    ),

    uploadAvatar: async (participantId, file) => {
        const formData = new FormData();
        formData.append("file", file);
        return request(`/participants/${participantId}/avatar`, {
            method: "POST",
            body: formData,
        });
    },

    getPreviewUrl: (chatId) => `${API_BASE_URL}/chats/${chatId}/preview?t=${Date.now()}`,
    getHistoryImageUrl: (historyId) => `${API_BASE_URL}/history/${historyId}/image`,
    getAvatarUrl: (participantId) => `${API_BASE_URL}/participants/${participantId}/avatar`,
    getExamples: () => request("/examples"),
    getExampleUrl: (slug) => `${API_BASE_URL}/examples/${encodeURIComponent(slug)}.png`,
};
