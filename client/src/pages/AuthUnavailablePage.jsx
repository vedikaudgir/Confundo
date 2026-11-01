import { useEffect, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, LockKeyhole } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/context";

const recoveryPages = {
    "/forgot-password": {
        eyebrow: "Password help",
        title: "Forgot your password?",
        message: "Self-service password recovery is not available because no email-delivery or reset-token workflow is configured.",
    },
    "/reset-password": {
        eyebrow: "Password help",
        title: "Reset password",
        message: "Password reset links are not available. If you can sign in, you can change your password in account settings.",
    },
};

export function AuthUnavailablePage() {
    const location = useLocation();
    const navigate = useNavigate();
    const { user, login, register } = useAuth();
    const authAttemptInProgress = useRef(false);
    const [username, setUsername] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [identifier, setIdentifier] = useState("");
    const [error, setError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const mode = location.pathname === "/signup" ? "signup" : "login";
    const recovery = recoveryPages[location.pathname];

    useEffect(() => {
        if (user && !recovery && !authAttemptInProgress.current) {
            navigate("/account", { replace: true });
        }
    }, [user, recovery, navigate]);

    if (user && !recovery) return null;

    const handleSubmit = async (event) => {
        event.preventDefault();
        authAttemptInProgress.current = true;
        setError("");
        setIsSubmitting(true);
        try {
            if (mode === "signup") {
                await register({ username, email, password });
            } else {
                await login({ identifier, password });
            }
            const returnTo = location.state?.returnTo;
            const returnPath = returnTo
                ? `${returnTo.pathname}${returnTo.search || ""}${returnTo.hash || ""}`
                : "/account";
            navigate(returnPath, { replace: true });
        } catch (requestError) {
            console.error(`Could not ${mode === "signup" ? "create the account" : "sign in"}:`, requestError);
            setError(requestError.message);
        } finally {
            authAttemptInProgress.current = false;
            setIsSubmitting(false);
        }
    };

    return (
        <section className="auth-page">
            <div className="auth-card">
                <span className="auth-icon"><LockKeyhole size={21} /></span>
                <span className="eyebrow">{recovery?.eyebrow || (mode === "signup" ? "New around here" : "Welcome back")}</span>
                <h1>{recovery?.title || (mode === "signup" ? "Create an account" : "Log in")}</h1>
                {recovery ? (
                    <>
                        <p className="auth-card__description">{recovery.message}</p>
                        <div className="capability-notice" role="status">
                            <strong>Password change is available after sign-in</strong>
                            <p>Use your current password in account settings to choose a new one.</p>
                        </div>
                        <div className="auth-links">
                            <Link className="text-link" to="/login">Back to log in <ArrowRight size={15} /></Link>
                            <Link className="text-link" to="/signup">Create an account <ArrowRight size={15} /></Link>
                        </div>
                    </>
                ) : (
                    <>
                        <p className="auth-card__description">
                            {mode === "signup"
                                ? "Create an account to save chats and keep a private generation history."
                                : "Sign in to continue to your chats and settings."}
                        </p>
                        <form className="auth-form" onSubmit={handleSubmit}>
                            {mode === "signup" ? (
                                <>
                                    <div className="form-field">
                                        <label htmlFor="auth-username">Username</label>
                                        <input
                                            id="auth-username"
                                            className="form-control"
                                            autoComplete="username"
                                            value={username}
                                            onChange={(event) => setUsername(event.target.value)}
                                            minLength={3}
                                            maxLength={32}
                                            required
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label htmlFor="auth-email">Email</label>
                                        <input
                                            id="auth-email"
                                            className="form-control"
                                            type="email"
                                            autoComplete="email"
                                            value={email}
                                            onChange={(event) => setEmail(event.target.value)}
                                            maxLength={254}
                                            required
                                        />
                                    </div>
                                </>
                            ) : (
                                <div className="form-field">
                                    <label htmlFor="auth-identifier">Username or email</label>
                                    <input
                                        id="auth-identifier"
                                        className="form-control"
                                        autoComplete="username"
                                        value={identifier}
                                        onChange={(event) => setIdentifier(event.target.value)}
                                        maxLength={254}
                                        required
                                    />
                                </div>
                            )}
                            <div className="form-field">
                                <label htmlFor="auth-password">Password</label>
                                <input
                                    id="auth-password"
                                    className="form-control"
                                    type="password"
                                    autoComplete={mode === "signup" ? "new-password" : "current-password"}
                                    value={password}
                                    onChange={(event) => setPassword(event.target.value)}
                                    minLength={8}
                                    maxLength={128}
                                    required
                                />
                            </div>
                            {error && <p className="feedback-message" role="alert">{error}</p>}
                            <button
                                className="action-button action-button--primary auth-submit"
                                type="submit"
                                disabled={isSubmitting}
                            >
                                {isSubmitting ? "Please wait…" : mode === "signup" ? "Create account" : "Log in"}
                                {!isSubmitting && <ArrowRight size={16} />}
                            </button>
                        </form>
                        {mode === "login" && (
                            <Link className="text-link auth-recovery" to="/forgot-password">Forgot password?</Link>
                        )}
                        <div className="auth-links">
                            {mode === "signup" ? (
                                <Link className="text-link" to="/login">Already have an account? Log in <ArrowRight size={15} /></Link>
                            ) : (
                                <Link className="text-link" to="/signup">New here? Create an account <ArrowRight size={15} /></Link>
                            )}
                        </div>
                    </>
                )}
                <Link className="back-link" to="/">
                    <ArrowLeft size={14} /> Back to ChattieBaby
                </Link>
            </div>
        </section>
    );
}
