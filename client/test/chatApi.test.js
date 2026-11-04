import assert from "node:assert/strict";
import { test } from "node:test";

let moduleId = 0;

async function loadChatApi() {
    return import(`../src/api/chatApi.js?test=${moduleId++}`);
}

function jsonResponse(body, headers = {}, status = 200) {
    return new Response(JSON.stringify(body), {
        status,
        headers: {
            "Content-Type": "application/json",
            ...headers,
        },
    });
}

test("bootstraps CSRF before writes and adopts rotated tokens", async () => {
    const originalFetch = globalThis.fetch;
    const requests = [];
    globalThis.fetch = async (url, options = {}) => {
        requests.push({ url, options });
        if (url.endsWith("/auth/csrf")) {
            return jsonResponse({ has_session: false }, { "X-CSRF-Token": "bootstrap-token" });
        }
        if (url.endsWith("/auth/register")) {
            assert.equal(new Headers(options.headers).get("X-CSRF-Token"), "bootstrap-token");
            return jsonResponse({ id: 1 }, { "X-CSRF-Token": "registered-token" }, 201);
        }
        if (url.endsWith("/settings/me")) {
            assert.equal(new Headers(options.headers).get("X-CSRF-Token"), "registered-token");
            return jsonResponse({ theme: "dark" });
        }
        throw new Error(`Unexpected request: ${url}`);
    };

    try {
        const { API_BASE_URL, chatApi } = await loadChatApi();
        assert.equal(API_BASE_URL, "/api");
        assert.deepEqual(await chatApi.register({ username: "test" }), { id: 1 });
        assert.equal(chatApi.hasSessionCookieHint(), true);
        assert.deepEqual(await chatApi.updateSettings({ theme: "dark" }), { theme: "dark" });
        assert.equal(requests.length, 3);
        assert.ok(requests.every(({ options }) => options.credentials === "include"));
        assert.equal(requests[0].url, `${API_BASE_URL}/auth/csrf`);
    } finally {
        globalThis.fetch = originalFetch;
    }
});

test("restores cross-origin sessions and refreshes with the bootstrapped token", async () => {
    const originalFetch = globalThis.fetch;
    const requests = [];
    let profileRequests = 0;
    globalThis.fetch = async (url, options = {}) => {
        requests.push({ url, options });
        if (url.endsWith("/auth/csrf")) {
            return jsonResponse({ has_session: true }, { "X-CSRF-Token": "stored-token" });
        }
        if (url.endsWith("/auth/me")) {
            profileRequests += 1;
            if (profileRequests === 1) return jsonResponse({ detail: "expired" }, {}, 401);
            return jsonResponse({ id: 1, username: "restored" });
        }
        if (url.endsWith("/auth/refresh")) {
            assert.equal(new Headers(options.headers).get("X-CSRF-Token"), "stored-token");
            return jsonResponse({ id: 1 }, { "X-CSRF-Token": "rotated-token" });
        }
        throw new Error(`Unexpected request: ${url}`);
    };

    try {
        const { chatApi } = await loadChatApi();
        await chatApi.getCsrfToken();
        assert.equal(chatApi.hasSessionCookieHint(), true);
        assert.deepEqual(await chatApi.getMe(), { id: 1, username: "restored" });
        assert.equal(profileRequests, 2);
        assert.ok(requests.every(({ options }) => options.credentials === "include"));
    } finally {
        globalThis.fetch = originalFetch;
    }
});
