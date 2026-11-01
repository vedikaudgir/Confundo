import { createElement } from "react";
import {
    ArrowRight,
    ArrowUpRight,
    Download,
    MessageSquareText,
    PanelsTopLeft,
    SlidersHorizontal,
} from "lucide-react";
import { Link } from "react-router-dom";
import { chatApi } from "../api/chatApi";
import { useExamples } from "../hooks/useExamples";

const platforms = [
    { id: "whatsapp", name: "WhatsApp", description: "Everyday chats and group-text energy." },
    { id: "instagram", name: "Instagram DM", description: "A familiar look for your made-up messages." },
    { id: "chatgpt", name: "ChatGPT", description: "A back-and-forth with an AI assistant." },
];

const features = [
    {
        icon: MessageSquareText,
        title: "Write it your way",
        description: "Set the names, status, message timing, and who says what.",
    },
    {
        icon: SlidersHorizontal,
        title: "Make it feel familiar",
        description: "Choose a chat style and theme, then shape each line of the scene.",
    },
    {
        icon: Download,
        title: "Keep the finished image",
        description: "Preview the Pillow-rendered screenshot and download it when it feels right.",
    },
];

function ExampleUnavailable({ loading, error }) {
    if (loading) return <div className="example-placeholder">Preparing fictional examples…</div>;
    if (error) {
        return (
            <div className="example-placeholder example-placeholder--error" role="status">
                Examples are temporarily unavailable. The chat maker is still ready to use.
            </div>
        );
    }
    return null;
}

export function LandingPage() {
    const { examples, loading, error } = useExamples();
    const heroExamples = examples.slice(0, 3);

    return (
        <div className="landing-page">
            <section className="hero-section">
                <div className="hero-copy">
                    <span className="eyebrow">A chat screenshot maker</span>
                    <h1>Make a little story out of a chat.</h1>
                    <p>
                        Build a fictional conversation, give it a familiar chat style,
                        and turn the punchline into a shareable image.
                    </p>
                    <div className="hero-actions">
                        <Link className="action-button action-button--primary" to="/create">
                            Get started <ArrowRight size={17} />
                        </Link>
                        <Link className="text-link" to="/examples">
                            Explore examples <ArrowUpRight size={16} />
                        </Link>
                    </div>
                    <p className="hero-disclaimer">Create an account to save and manage your chats.</p>
                </div>

                <div className="hero-art" aria-label="Fictional generated conversation previews">
                    <div className="hero-art__label">
                        <span className="hero-art__dot" />
                        Fictional chats, made by you
                    </div>
                    {heroExamples.length > 0 ? (
                        <div className="hero-art__images">
                            {heroExamples.map((example, index) => (
                                <article
                                    className={`hero-chat hero-chat--${index + 1}`}
                                    key={example.slug}
                                >
                                    <div className="hero-chat__meta">
                                        <span>{example.platform === "instagram" ? "Instagram DM" : example.platform === "chatgpt" ? "ChatGPT" : "WhatsApp"}</span>
                                        <span>{example.scenario}</span>
                                    </div>
                                    <img
                                        src={chatApi.getExampleUrl(example.slug)}
                                        alt={`Fictional ${example.platform} conversation: ${example.title}`}
                                    />
                                </article>
                            ))}
                        </div>
                    ) : (
                        <ExampleUnavailable loading={loading} error={error} />
                    )}
                    <div className="hero-art__note">
                        <span>01 — 03</span>
                        <span>A few ways a conversation can go</span>
                    </div>
                </div>
            </section>

            <section className="platform-section" aria-labelledby="platform-heading">
                <div className="section-heading section-heading--compact">
                    <div>
                        <span className="eyebrow">Pick your conversation</span>
                        <h2 id="platform-heading">Three familiar chat styles.</h2>
                    </div>
                    <Link className="text-link" to="/create">
                        Open the generator <ArrowRight size={16} />
                    </Link>
                </div>
                <div className="platform-grid">
                    {platforms.map((platform) => {
                        const example = examples.find((item) => item.platform === platform.id);
                        return (
                            <Link
                                className="platform-card"
                                to={`/create?platform=${platform.id}`}
                                key={platform.id}
                            >
                                <div className="platform-card__image">
                                    {example ? (
                                        <img
                                            src={chatApi.getExampleUrl(example.slug)}
                                            alt={`Fictional ${platform.name} conversation preview`}
                                            loading="lazy"
                                        />
                                    ) : (
                                        <span>{platform.name}</span>
                                    )}
                                </div>
                                <div className="platform-card__body">
                                    <div>
                                        <h3>{platform.name}</h3>
                                        <p>{platform.description}</p>
                                    </div>
                                    <ArrowUpRight size={17} />
                                </div>
                            </Link>
                        );
                    })}
                </div>
            </section>

            <section className="how-section" aria-labelledby="how-heading">
                <div className="section-heading">
                    <div>
                        <span className="eyebrow">Simple by design</span>
                        <h2 id="how-heading">From setup to screenshot in three steps.</h2>
                    </div>
                    <p>Every conversation is built from your details and rendered as an image.</p>
                </div>
                <div className="how-grid">
                    {[
                        ["01", "Set the scene", "Choose WhatsApp, Instagram DM, or ChatGPT. Add names and a status."],
                        ["02", "Write the exchange", "Pick who is speaking, add a time, and build the conversation line by line."],
                        ["03", "Preview & save", "Check the generated image, make changes, and download your finished chat."],
                    ].map(([number, title, description]) => (
                        <article className="how-step" key={number}>
                            <span>{number}</span>
                            <div>
                                <h3>{title}</h3>
                                <p>{description}</p>
                            </div>
                        </article>
                    ))}
                </div>
            </section>

            <section className="features-section" aria-labelledby="features-heading">
                <div className="feature-intro">
                    <span className="eyebrow">A tiny creative tool</span>
                    <h2 id="features-heading">The details make the joke.</h2>
                    <p>Keep the controls close to the conversation and the finished image in view.</p>
                    <Link to="/create" className="text-link">
                        Make your first chat <ArrowRight size={16} />
                    </Link>
                </div>
                <div className="feature-list">
                    {features.map(({ icon: Icon, title, description }) => (
                        <article className="feature-row" key={title}>
                            <span className="feature-icon">{createElement(Icon, { size: 19, strokeWidth: 1.8 })}</span>
                            <div>
                                <h3>{title}</h3>
                                <p>{description}</p>
                            </div>
                        </article>
                    ))}
                    <div className="feature-aside">
                        <PanelsTopLeft size={17} />
                        <span>Examples are fictional and clearly marked.</span>
                    </div>
                </div>
            </section>

            <section className="gallery-section" aria-labelledby="gallery-heading">
                <div className="section-heading">
                    <div>
                        <span className="eyebrow">Made with ChattieBaby</span>
                        <h2 id="gallery-heading">A few fictional conversations.</h2>
                    </div>
                    <Link className="text-link" to="/examples">
                        Browse all examples <ArrowRight size={16} />
                    </Link>
                </div>
                {error ? (
                    <ExampleUnavailable loading={loading} error={error} />
                ) : (
                    <div className="gallery-strip">
                        {examples.slice(0, 3).map((example) => (
                            <Link
                                className="gallery-tile"
                                to="/examples"
                                key={example.slug}
                            >
                                <div className="gallery-tile__image">
                                    <img
                                        src={chatApi.getExampleUrl(example.slug)}
                                        alt={`Fictional chat: ${example.title}`}
                                        loading="lazy"
                                    />
                                </div>
                                <div className="gallery-tile__caption">
                                    <span>{example.scenario} · {example.tone}</span>
                                    <strong>{example.title}</strong>
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </section>

            <section className="final-cta">
                <div>
                    <span className="eyebrow">Your turn</span>
                    <h2>Got a conversation in mind?</h2>
                    <p>Put the words in the right places and see where the story goes.</p>
                </div>
                <Link className="action-button action-button--primary" to="/create">
                    Create a chat <ArrowRight size={17} />
                </Link>
            </section>
        </div>
    );
}
