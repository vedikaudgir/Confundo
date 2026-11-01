import { useEffect, useState } from "react";
import {
    BrowserRouter,
    Link,
    Navigate,
    NavLink,
    Outlet,
    Route,
    Routes,
    useLocation,
    useOutletContext,
} from "react-router-dom";
import { MessageSquareText } from "lucide-react";
import { AuthProvider } from "./auth/AuthContext";
import { useAuth } from "./auth/context";
import { chatApi } from "./api/chatApi";
import { BuilderPage } from "./pages/BuilderPage";
import { LandingPage } from "./pages/LandingPage";
import { ExamplesPage } from "./pages/ExamplesPage";
import { AuthUnavailablePage } from "./pages/AuthUnavailablePage";
import { AccountPage } from "./pages/AccountPage";
import { InfoPage } from "./pages/InfoPage";
import "./App.css";

function SiteLayout() {
    const { user, logout } = useAuth();
    const [theme, setTheme] = useState(() => {
        try {
            return localStorage.getItem("chattiebaby-theme") === "dark" ? "dark" : "light";
        } catch {
            return "light";
        }
    });
    const [navError, setNavError] = useState("");
    const location = useLocation();

    useEffect(() => {
        if (!user) return;
        chatApi.getSettings()
            .then((settings) => {
                if (settings.theme === "light" || settings.theme === "dark") setTheme(settings.theme);
            })
            .catch((error) => {
                console.error("Could not load account appearance settings:", error);
                setNavError("Account settings could not be loaded from the server.");
            });
    }, [user]);

    useEffect(() => {
        try {
            localStorage.setItem("chattiebaby-theme", theme);
        } catch (error) {
            console.error("Could not save the appearance preference:", error);
        }
    }, [theme]);

    useEffect(() => {
        const titles = {
            "/": "ChattieBaby — Make a chat worth sharing",
            "/examples": "Fictional chat examples — ChattieBaby",
            "/create": "Chat generator — ChattieBaby",
            "/login": "Log in — ChattieBaby",
            "/signup": "Create an account — ChattieBaby",
            "/forgot-password": "Password help — ChattieBaby",
            "/reset-password": "Reset password — ChattieBaby",
            "/account": "Account & settings — ChattieBaby",
            "/terms": "Terms — ChattieBaby",
            "/privacy": "Privacy — ChattieBaby",
            "/cookies": "Cookies — ChattieBaby",
            "/faq": "FAQ — ChattieBaby",
            "/about": "About — ChattieBaby",
        };
        document.title = titles[location.pathname] || "ChattieBaby";
        window.scrollTo(0, 0);
    }, [location.pathname]);

    const updateTheme = async (value) => {
        setTheme(value);
        if (!user) return;
        try {
            await chatApi.updateSettings({ theme: value });
            setNavError("");
        } catch (error) {
            console.error("Could not save account appearance settings:", error);
            setNavError(`Theme preference was not saved: ${error.message}`);
        }
    };

    const handleLogout = async () => {
        try {
            await logout();
            setNavError("");
        } catch (error) {
            console.error("Could not log out:", error);
            setNavError(`Could not log out: ${error.message}`);
        }
    };

    return (
        <div className="app-shell" data-theme={theme}>
            <header className="site-header">
                <Link className="brand" to="/" aria-label="ChattieBaby home">
                    <span className="brand-mark" aria-hidden="true">
                        <MessageSquareText size={19} strokeWidth={2} />
                    </span>
                    <span>ChattieBaby</span>
                </Link>
                <nav className="site-nav" aria-label="Main navigation">
                    <NavLink to="/examples" className={({ isActive }) => isActive ? "site-nav__link is-active" : "site-nav__link"}>
                        Examples
                    </NavLink>
                    <NavLink to="/create" className={({ isActive }) => isActive ? "site-nav__link is-active" : "site-nav__link"}>
                        Generator
                    </NavLink>
                    {user ? (
                        <>
                            <NavLink to="/account" className={({ isActive }) => isActive ? "site-nav__link is-active" : "site-nav__link"}>
                                Account
                            </NavLink>
                            <button className="site-nav__login" type="button" onClick={handleLogout}>Log out</button>
                        </>
                    ) : (
                        <>
                            <Link className="site-nav__login" to="/login">Log in</Link>
                            <Link className="site-nav__signup" to="/signup">Sign up</Link>
                        </>
                    )}
                </nav>
            </header>

            {navError && <p className="feedback-message site-feedback" role="alert">{navError}</p>}

            <main className="page-main">
                <Outlet context={{ theme, setTheme: updateTheme }} />
            </main>

            <footer className="site-footer site-footer--full">
                <div className="footer-brand">
                    <Link className="brand brand--footer" to="/">
                        <span className="brand-mark" aria-hidden="true">
                            <MessageSquareText size={17} strokeWidth={2} />
                        </span>
                        <span>ChattieBaby</span>
                    </Link>
                    <p>Make a little story out of a chat.</p>
                    <span className="footer-fiction">Every example is fictional.</span>
                </div>
                <div className="footer-links">
                    <strong>Explore</strong>
                    <Link to="/examples">Examples</Link>
                    <Link to="/create">Create a chat</Link>
                    <Link to="/faq">FAQ</Link>
                </div>
                <div className="footer-links">
                    <strong>Information</strong>
                    <Link to="/about">About & contact</Link>
                    <Link to="/terms">Terms</Link>
                    <Link to="/privacy">Privacy</Link>
                    <Link to="/cookies">Cookies</Link>
                </div>
                <div className="footer-bottom">
                    <span>© {new Date().getFullYear()} ChattieBaby</span>
                    <span>Chat screenshots are for creative and fictional use.</span>
                </div>
            </footer>
        </div>
    );
}

function NotFoundPage() {
    return (
        <section className="notice-page">
            <p className="eyebrow">404 · Page not found</p>
            <h1>That chat went off-script.</h1>
            <p>We couldn&apos;t find the page you were looking for.</p>
            <Link to="/" className="action-button action-button--primary">Back to home</Link>
        </section>
    );
}

function RequireAuthentication() {
    const { user, isLoading } = useAuth();
    const location = useLocation();
    const outletContext = useOutletContext();
    if (isLoading) {
        return <section className="notice-page" role="status">Checking your account…</section>;
    }
    return user
        ? <Outlet context={outletContext} />
        : <Navigate to="/login" replace state={{ returnTo: location }} />;
}

function RoutedApp() {
    const location = useLocation();

    return (
        <Routes location={location}>
            <Route element={<SiteLayout />}>
                <Route index element={<LandingPage />} />
                <Route path="examples" element={<ExamplesPage />} />
                <Route path="login" element={<AuthUnavailablePage />} />
                <Route path="signup" element={<AuthUnavailablePage />} />
                <Route path="forgot-password" element={<AuthUnavailablePage />} />
                <Route path="reset-password" element={<AuthUnavailablePage />} />
                <Route element={<RequireAuthentication />}>
                    <Route path="create" element={<BuilderPage />} />
                    <Route path="account" element={<AccountPage />} />
                </Route>
                <Route path="terms" element={<InfoPage page="terms" />} />
                <Route path="privacy" element={<InfoPage page="privacy" />} />
                <Route path="cookies" element={<InfoPage page="cookies" />} />
                <Route path="faq" element={<InfoPage page="faq" />} />
                <Route path="about" element={<InfoPage page="about" />} />
                <Route path="*" element={<NotFoundPage />} />
            </Route>
        </Routes>
    );
}

function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <RoutedApp />
            </BrowserRouter>
        </AuthProvider>
    );
}

export default App;
