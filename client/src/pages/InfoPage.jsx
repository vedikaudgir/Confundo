import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";

const pageContent = {
    terms: {
        eyebrow: "Terms & conditions",
        title: "Using ChattieBaby",
        intro: "These notes describe the current creative tool and are not a substitute for reviewed legal terms.",
        sections: [
            ["A fictional chat maker", "ChattieBaby creates mock chat screenshots from information you enter. Do not present fictional screenshots as genuine conversations or use them to impersonate, harass, or mislead someone."],
            ["Content you provide", "You choose the text, names, and images submitted to the generator. Avoid entering sensitive personal information or images you do not have permission to use."],
            ["Responsible use", "You are responsible for the content you submit and how you use generated images. Do not present fictional screenshots as genuine conversations or use them to impersonate, harass, or mislead someone."],
            ["Review before relying on these terms", "These product notes are informational. The project owner should review and replace them with appropriate legal terms before relying on them as a binding agreement."],
        ],
    },
    privacy: {
        eyebrow: "Privacy information",
        title: "What the current app does with your input",
        intro: "This summary reflects the application code currently present in this project. It is not a promise about hosting-provider logs or deployment retention.",
        sections: [
            ["Information sent to the API", "When you register, the API receives your username, email address, and password. Passwords are stored as password hashes. Chat titles, participant names, message text and times, and any uploaded profile photo are stored when you use the generator."],
            ["Application storage", "Account and chat records, settings, refresh-session hashes, and generation-history records are stored in SQLite. Generated PNGs and normalized profile photos are stored in private server directories and are served only after account ownership checks."],
            ["Cookies and sessions", "Sign-in uses HttpOnly access and refresh cookies. A separate CSRF cookie is used to protect state-changing requests. Refresh sessions are stored as hashes and are revoked when you log out, change your password, or delete your account."],
            ["Retention and deletion", "You can delete chats, history entries, or your account in account settings. Account deletion removes application-owned account records and private files. Backup and hosting-provider retention are deployment-specific and are not established by this source code."],
            ["Questions and updates", "A verified privacy contact address has not been configured in the project. This page should be reviewed and updated by the project owner before being treated as a formal privacy notice."],
        ],
    },
    cookies: {
        eyebrow: "Cookie information",
        title: "Browser storage and cookies",
        intro: "ChattieBaby uses browser cookies for secure sign-in sessions and a CSRF check.",
        sections: [
            ["Authentication cookies", "The API sets HttpOnly access and refresh cookies after sign-in. These cookies are used to authenticate requests and maintain the session; JavaScript cannot read them."],
            ["CSRF cookie", "A separate CSRF cookie is readable by the frontend and sent in a request header for state-changing API calls. It is not an authentication token."],
            ["Theme preference", "Appearance is saved to your account when signed in and also cached in this browser for display."],
            ["Manage cookies", "Sign out to revoke the current refresh session. You can also clear site cookies in your browser; clearing them signs you out of this browser."],
        ],
    },
    about: {
        eyebrow: "About ChattieBaby",
        title: "A small tool for made-up conversations.",
        intro: "ChattieBaby turns a fictional exchange you write into a chat-style image using the project’s Pillow renderers.",
        sections: [
            ["Supported styles", "The generator offers WhatsApp, Instagram DM, and ChatGPT-style screenshots. The examples gallery is made from fictional sample conversations rendered by the backend."],
            ["Built around your words", "Choose participant names, add messages and timestamps, and preview the result before downloading it. Signed-in users can save chats and review their generated images."],
            ["Contact", "A public support email or contact endpoint is not configured in this project. No contact details are shown here rather than inventing one."],
        ],
    },
};

const faqItems = [
    ["Are the gallery conversations real?", "No. Gallery conversations are fictional examples generated for demonstration."],
    ["How are screenshots generated?", "The frontend sends chat details to the FastAPI backend. Platform renderers use Pillow to generate PNG images."],
    ["Which styles can I choose?", "WhatsApp, Instagram DM, and ChatGPT are available in the generator."],
    ["Do I need an account?", "Yes. Sign in to create, save, and manage chats. Your chats and generated images are scoped to your account."],
    ["Can I edit a message after adding it?", "Yes. Messages in the current generator can be edited or removed, and the image preview is regenerated."],
    ["Where is my generation history?", "Signed-in users can view and remove generated images from the account settings page."],
    ["Can I reset my password by email?", "Not currently. Email delivery and self-service password reset are not configured. You can change your password from account settings while signed in."],
    ["Can I use a real person’s name or photo?", "Use names and images responsibly, and only upload images you have permission to use. Do not use fictional screenshots to impersonate or mislead."],
];

export function InfoPage({ page }) {
    if (page === "faq") {
        return (
            <article className="info-page faq-page">
                <header className="info-heading">
                    <span className="eyebrow">Good to know</span>
                    <h1>Frequently asked questions.</h1>
                    <p>What the generator does today—and what it doesn&apos;t.</p>
                </header>
                <div className="faq-list">
                    {faqItems.map(([question, answer]) => (
                        <details className="faq-item" key={question}>
                            <summary>{question}</summary>
                            <p>{answer}</p>
                        </details>
                    ))}
                </div>
                <Link to="/create" className="action-button action-button--primary">
                    Try the generator <ArrowRight size={16} />
                </Link>
            </article>
        );
    }

    const content = pageContent[page] || pageContent.about;

    return (
        <article className="info-page">
            <header className="info-heading">
                <span className="eyebrow">{content.eyebrow}</span>
                <h1>{content.title}</h1>
                <p>{content.intro}</p>
            </header>
            <div className="info-sections">
                {content.sections.map(([title, body]) => (
                    <section className="info-section" key={title}>
                        <h2>{title}</h2>
                        <p>{body}</p>
                    </section>
                ))}
            </div>
            {(page === "privacy" || page === "terms") && (
                <p className="legal-review-note">
                    This page is a plain-language product summary, not legal advice. Have the project owner review it.
                </p>
            )}
        </article>
    );
}
