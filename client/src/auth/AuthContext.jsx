import { useEffect, useMemo, useState } from "react";
import { chatApi } from "../api/chatApi";
import { AuthContext } from "./context";

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(() => chatApi.hasSessionCookieHint());

    useEffect(() => {
        let active = true;
        const expireSession = () => {
            if (active) setUser(null);
        };
        const cleanup = () => {
            active = false;
            window.removeEventListener("chattiebaby:session-expired", expireSession);
        };
        window.addEventListener("chattiebaby:session-expired", expireSession);
        if (!chatApi.hasSessionCookieHint()) {
            return cleanup;
        }
        chatApi.getMe()
            .then((profile) => {
                if (active) setUser(profile);
            })
            .catch((error) => {
                if (active && error.status !== 401) {
                    console.error("Could not restore the signed-in session:", error);
                }
                if (active) setUser(null);
            })
            .finally(() => {
                if (active) setIsLoading(false);
            });
        return cleanup;
    }, []);

    const value = useMemo(() => ({
        user,
        isLoading,
        async login(credentials) {
            await chatApi.login(credentials);
            const profile = await chatApi.getMe();
            setUser(profile);
            return profile;
        },
        async register(details) {
            await chatApi.register(details);
            const profile = await chatApi.getMe();
            setUser(profile);
            return profile;
        },
        async logout() {
            await chatApi.logout();
            setUser(null);
        },
        setUser,
    }), [user, isLoading]);

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
