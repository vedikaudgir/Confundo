import { useEffect, useState } from "react";
import { ArrowDownToLine, Check, CircleHelp, Trash2, UserRound } from "lucide-react";
import { Link, useNavigate, useOutletContext } from "react-router-dom";
import { chatApi } from "../api/chatApi";
import { useAuth } from "../auth/context";

export function AccountPage() {
    const { theme, setTheme } = useOutletContext();
    const { user, setUser } = useAuth();
    const navigate = useNavigate();
    const [username, setUsername] = useState(user.username);
    const [email, setEmail] = useState(user.email);
    const [settings, setSettings] = useState(null);
    const [chats, setChats] = useState([]);
    const [history, setHistory] = useState([]);
    const [imageUrls, setImageUrls] = useState({});
    const [currentPassword, setCurrentPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [deletePassword, setDeletePassword] = useState("");
    const [notice, setNotice] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        let active = true;
        Promise.all([chatApi.getSettings(), chatApi.listChats(), chatApi.listHistory()])
            .then(([nextSettings, nextChats, nextHistory]) => {
                if (!active) return;
                setSettings(nextSettings);
                setChats(nextChats);
                setHistory(nextHistory);
            })
            .catch((loadError) => {
                console.error("Could not load account data:", loadError);
                if (active) setError(`Could not load account data: ${loadError.message}`);
            })
            .finally(() => {
                if (active) setIsLoading(false);
            });
        return () => {
            active = false;
        };
    }, []);

    useEffect(() => {
        let active = true;
        const urls = {};
        Promise.all(history.map(async (item) => {
            try {
                const response = await chatApi.getHistoryImage(item.id);
                urls[item.id] = URL.createObjectURL(await response.blob());
            } catch (imageError) {
                console.error(`Could not load generation ${item.id}:`, imageError);
            }
        })).then(() => {
            if (active) setImageUrls(urls);
            else Object.values(urls).forEach((url) => URL.revokeObjectURL(url));
        });
        return () => {
            active = false;
            Object.values(urls).forEach((url) => URL.revokeObjectURL(url));
        };
    }, [history]);

    const saveProfile = async (event) => {
        event.preventDefault();
        setIsSaving(true);
        setError("");
        setNotice("");
        try {
            const updated = await chatApi.updateProfile({ username, email });
            setUser(updated);
            setNotice("Profile updated.");
        } catch (saveError) {
            console.error("Could not update profile:", saveError);
            setError(saveError.message);
        } finally {
            setIsSaving(false);
        }
    };

    const savePassword = async (event) => {
        event.preventDefault();
        setIsSaving(true);
        setError("");
        setNotice("");
        try {
            const result = await chatApi.changePassword({
                current_password: currentPassword,
                new_password: newPassword,
            });
            setCurrentPassword("");
            setNewPassword("");
            setUser(null);
            navigate("/login", { replace: true });
            setNotice(`${result.status}.`);
        } catch (saveError) {
            console.error("Could not change password:", saveError);
            setError(saveError.message);
        } finally {
            setIsSaving(false);
        }
    };

    const changeTheme = async (value) => {
        setSettings((current) => ({ ...current, theme: value }));
        await setTheme(value);
    };

    const removeChat = async (chatId) => {
        if (!window.confirm("Delete this chat and its generated image? This cannot be undone.")) return;
        setError("");
        try {
            await chatApi.deleteChat(chatId);
            setChats((current) => current.filter((chat) => chat.id !== chatId));
            setHistory((current) => current.filter((item) => item.chat_id !== chatId));
            setNotice("Chat deleted.");
        } catch (deleteError) {
            console.error("Could not delete chat:", deleteError);
            setError(deleteError.message);
        }
    };

    const removeHistoryItem = async (item) => {
        setError("");
        try {
            await chatApi.deleteHistory(item.id);
            setHistory((current) => current.filter((entry) => entry.id !== item.id));
            setNotice("Generation removed from history.");
        } catch (deleteError) {
            console.error("Could not delete generation history:", deleteError);
            setError(deleteError.message);
        }
    };

    const downloadHistoryItem = async (item) => {
        setError("");
        try {
            const response = await chatApi.getHistoryImage(item.id);
            const url = URL.createObjectURL(await response.blob());
            const anchor = document.createElement("a");
            anchor.href = url;
            anchor.download = `confundo-${item.platform}-${item.chat_id}.png`;
            document.body.appendChild(anchor);
            anchor.click();
            anchor.remove();
            setTimeout(() => URL.revokeObjectURL(url), 1000);
        } catch (downloadError) {
            console.error("Could not download generation:", downloadError);
            setError(downloadError.message);
        }
    };

    const removeAccount = async (event) => {
        event.preventDefault();
        setError("");
        if (!window.confirm("Permanently delete your account, chats, settings, and generation history?")) return;
        try {
            await chatApi.deleteAccount(deletePassword);
            setUser(null);
            navigate("/", { replace: true });
        } catch (deleteError) {
            console.error("Could not delete account:", deleteError);
            setError(deleteError.message);
        }
    };

    return (
        <div className="account-page">
            <section className="page-intro page-intro--wide">
                <div>
                    <span className="eyebrow">Your account</span>
                    <h1>Account and settings.</h1>
                    <p className="page-intro__copy">Manage your profile, saved chats, and preferences.</p>
                </div>
            </section>

            {error && <div className="feedback-message" role="alert">{error}</div>}
            {notice && <div className="success-message" role="status">{notice}</div>}

            <div className="account-layout">
                <aside className="account-sidebar">
                    <span className="account-avatar"><UserRound size={22} /></span>
                    <strong>{user.username}</strong>
                    <span>{user.email}</span>
                    <span>Account created {new Date(user.created_at).toLocaleDateString()}</span>
                </aside>

                <div className="account-content">
                    <section className="setting-card">
                        <div className="setting-card__heading">
                            <div><span className="eyebrow">Profile</span><h2>Your details</h2></div>
                        </div>
                        <form className="account-form" onSubmit={saveProfile}>
                            <div className="form-field">
                                <label htmlFor="account-username">Username</label>
                                <input id="account-username" className="form-control" value={username} minLength={3} maxLength={32} onChange={(event) => setUsername(event.target.value)} required />
                            </div>
                            <div className="form-field">
                                <label htmlFor="account-email">Email</label>
                                <input id="account-email" className="form-control" type="email" value={email} maxLength={254} onChange={(event) => setEmail(event.target.value)} required />
                            </div>
                            <button className="action-button action-button--primary" disabled={isSaving}>Save profile</button>
                        </form>
                    </section>

                    <section className="setting-card">
                        <div className="setting-card__heading">
                            <div><span className="eyebrow">Appearance</span><h2>Theme preference</h2></div>
                            <span className="setting-saved"><Check size={14} /> {settings ? "Saved to account" : "Loading"}</span>
                        </div>
                        <div className="form-field setting-select">
                            <label htmlFor="theme-preference">Website theme</label>
                            <select id="theme-preference" className="form-control" value={settings?.theme || theme} onChange={(event) => changeTheme(event.target.value)}>
                                <option value="light">Light</option>
                                <option value="dark">Dark</option>
                            </select>
                            <span className="field-hint">This preference is saved to your account.</span>
                        </div>
                    </section>

                    <section className="setting-card">
                        <div className="setting-card__heading">
                            <div><span className="eyebrow">Security</span><h2>Change password</h2></div>
                        </div>
                        <form className="account-form" onSubmit={savePassword}>
                            <div className="form-field">
                                <label htmlFor="current-password">Current password</label>
                                <input id="current-password" className="form-control" type="password" autoComplete="current-password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} minLength={8} maxLength={128} required />
                            </div>
                            <div className="form-field">
                                <label htmlFor="new-password">New password</label>
                                <input id="new-password" className="form-control" type="password" autoComplete="new-password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} minLength={8} maxLength={128} required />
                            </div>
                            <button className="action-button action-button--primary" disabled={isSaving}>Update password</button>
                        </form>
                    </section>

                    <section className="setting-card">
                        <div className="setting-card__heading">
                            <div><span className="eyebrow">Your chats</span><h2>Saved conversations</h2></div>
                            <Link to="/create" className="text-link">Create a chat</Link>
                        </div>
                        {isLoading ? <p>Loading saved chats…</p> : chats.length ? (
                            <ul className="account-list">
                                {chats.map((chat) => (
                                    <li key={chat.id}>
                                        <span><strong>{chat.title}</strong><small>{chat.platform} · updated {new Date(chat.updated_at).toLocaleString()}</small></span>
                                        <span className="account-list__actions">
                                            <Link to={`/create?chat=${chat.id}`}>Open</Link>
                                            <button type="button" onClick={() => removeChat(chat.id)} aria-label={`Delete ${chat.title}`}><Trash2 size={15} /></button>
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        ) : <p>No saved chats yet.</p>}
                    </section>

                    <section className="setting-card">
                        <div className="setting-card__heading">
                            <div><span className="eyebrow">Generated images</span><h2>Generation history</h2></div>
                        </div>
                        {isLoading ? <p>Loading history…</p> : history.length ? (
                            <div className="history-grid">
                                {history.map((item) => (
                                    <article className="history-item" key={item.id}>
                                        {imageUrls[item.id]
                                            ? <img src={imageUrls[item.id]} alt={`Generated ${item.platform} chat: ${item.title}`} />
                                            : <div className="history-image-placeholder" role="status">Image unavailable</div>}
                                        <strong>{item.title}</strong>
                                        <small>{item.platform} · {new Date(item.created_at).toLocaleString()}</small>
                                        <div className="account-list__actions">
                                            <button type="button" onClick={() => downloadHistoryItem(item)}><ArrowDownToLine size={15} /> Download</button>
                                            <button type="button" onClick={() => removeHistoryItem(item)} aria-label={`Delete ${item.title} history`}><Trash2 size={15} /></button>
                                        </div>
                                    </article>
                                ))}
                            </div>
                        ) : <p>Generated chats appear here after you create them.</p>}
                    </section>

                    <section className="setting-card setting-card--danger">
                        <div className="setting-card__heading">
                            <div><span className="eyebrow">Account management</span><h2>Delete your account</h2></div>
                        </div>
                        <p>Deleting your account permanently removes its profile, settings, chats, generated images, and refresh sessions.</p>
                        <form className="account-form" onSubmit={removeAccount}>
                            <div className="form-field">
                                <label htmlFor="delete-password">Confirm password</label>
                                <input id="delete-password" className="form-control" type="password" autoComplete="current-password" value={deletePassword} onChange={(event) => setDeletePassword(event.target.value)} minLength={8} maxLength={128} required />
                            </div>
                            <button className="action-button action-button--danger" type="submit">Delete account</button>
                        </form>
                    </section>

                    <section className="setting-card setting-card--muted">
                        <span className="setting-card__icon"><CircleHelp size={18} /></span>
                        <div>
                            <h2>Password recovery</h2>
                            <p>Email-based password reset is not configured. You can change your password here while signed in.</p>
                            <Link to="/about" className="text-link">Product information</Link>
                        </div>
                    </section>
                </div>
            </div>
        </div>
    );
}
