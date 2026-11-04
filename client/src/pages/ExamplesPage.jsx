import { useEffect, useState } from "react";
import { ArrowDownToLine, ArrowRight, X } from "lucide-react";
import { Link } from "react-router-dom";
import { chatApi } from "../api/chatApi";
import { useExamples } from "../hooks/useExamples";

const PLATFORM_LABELS = {
    whatsapp: "WhatsApp",
    instagram: "Instagram DM",
    chatgpt: "ChatGPT",
};

export function ExamplesPage() {
    const { examples, loading, error } = useExamples();
    const [platform, setPlatform] = useState("all");
    const [selected, setSelected] = useState(null);
    const [downloadError, setDownloadError] = useState("");
    const [isDownloading, setIsDownloading] = useState(false);
    const filtered = platform === "all"
        ? examples
        : examples.filter((example) => example.platform === platform);

    useEffect(() => {
        if (!selected) return undefined;
        const handleEscape = (event) => {
            if (event.key === "Escape") setSelected(null);
        };
        window.addEventListener("keydown", handleEscape);
        return () => window.removeEventListener("keydown", handleEscape);
    }, [selected]);

    const downloadExample = async () => {
        if (!selected || isDownloading) return;
        setIsDownloading(true);
        setDownloadError("");
        try {
            const response = await fetch(chatApi.getExampleUrl(selected.slug));
            if (!response.ok) throw new Error(`Download failed (${response.status}).`);
            const downloadUrl = URL.createObjectURL(await response.blob());
            const link = document.createElement("a");
            link.href = downloadUrl;
            link.download = `confundo-${selected.slug}.png`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);
        } catch (downloadFailure) {
            console.error("Could not download the example:", downloadFailure);
            setDownloadError(downloadFailure.message);
        } finally {
            setIsDownloading(false);
        }
    };

    return (
        <div className="examples-page">
            <section className="page-intro page-intro--wide">
                <div>
                    <span className="eyebrow">The fictional chat gallery</span>
                    <h1>Little stories, different chat styles.</h1>
                    <p className="page-intro__copy">
                        Browse a handful of Pillow-rendered examples, then make one of your own.
                    </p>
                </div>
                <Link to="/create" className="action-button action-button--primary">
                    Open the generator <ArrowRight size={17} />
                </Link>
            </section>

            <div className="gallery-notice" role="note">
                Every conversation below is fictional and created for demonstration.
            </div>

            <div className="gallery-toolbar">
                <div className="filter-tabs" role="group" aria-label="Filter examples by platform">
                    {[
                        ["all", "All examples"],
                        ["whatsapp", "WhatsApp"],
                        ["instagram", "Instagram DM"],
                        ["chatgpt", "ChatGPT"],
                    ].map(([value, label]) => (
                        <button
                            type="button"
                            key={value}
                            className={platform === value ? "filter-tab is-selected" : "filter-tab"}
                            aria-pressed={platform === value}
                            onClick={() => setPlatform(value)}
                        >
                            {label}
                        </button>
                    ))}
                </div>
                <span className="gallery-count">
                    {loading ? "Loading examples…" : `${filtered.length} ${filtered.length === 1 ? "example" : "examples"}`}
                </span>
            </div>

            {error ? (
                <div className="notice-page notice-page--inline" role="alert">
                    <h2>Examples couldn&apos;t load.</h2>
                    <p>{error}</p>
                    <p>The generator is available; please try again shortly.</p>
                </div>
            ) : loading ? (
                <div className="gallery-grid gallery-grid--loading" aria-label="Loading fictional examples">
                    {[1, 2, 3].map((item) => <div className="gallery-skeleton" key={item} />)}
                </div>
            ) : (
                <div className="gallery-grid">
                    {filtered.map((example) => (
                        <button
                            type="button"
                            className="example-card"
                            key={example.slug}
                            onClick={() => setSelected(example)}
                            aria-label={`View fictional example: ${example.title}`}
                        >
                            <span className="example-card__image">
                                <img
                                    src={chatApi.getExampleUrl(example.slug)}
                                    alt=""
                                    loading="lazy"
                                />
                                <span className="fictional-badge">Fictional</span>
                            </span>
                            <span className="example-card__caption">
                                <span className="example-card__eyebrow">
                                    {PLATFORM_LABELS[example.platform]} · {example.scenario}
                                </span>
                                <strong>{example.title}</strong>
                                <span>{example.tone}</span>
                            </span>
                        </button>
                    ))}
                </div>
            )}

            {selected && (
                <div className="example-dialog-backdrop" role="presentation" onMouseDown={(event) => {
                    if (event.target === event.currentTarget) setSelected(null);
                }}>
                    <section
                        className="example-dialog"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="example-dialog-title"
                    >
                        <button
                            type="button"
                            className="icon-button dialog-close"
                            onClick={() => setSelected(null)}
                            aria-label="Close example preview"
                        >
                            <X size={19} />
                        </button>
                        <div className="example-dialog__image">
                            <img
                                src={chatApi.getExampleUrl(selected.slug)}
                                alt={`Fictional ${PLATFORM_LABELS[selected.platform]} chat: ${selected.title}`}
                            />
                        </div>
                        <div className="example-dialog__details">
                            <span className="eyebrow">Fictional example · {PLATFORM_LABELS[selected.platform]}</span>
                            <h2 id="example-dialog-title">{selected.title}</h2>
                            <p>{selected.scenario} · {selected.tone}</p>
                            <Link
                                className="action-button action-button--primary"
                                to={`/create?platform=${selected.platform}`}
                                onClick={() => setSelected(null)}
                            >
                                Make something like this <ArrowRight size={16} />
                            </Link>
                            <button
                                type="button"
                                className="text-link example-download"
                                onClick={downloadExample}
                                disabled={isDownloading}
                            >
                                <ArrowDownToLine size={15} />
                                {isDownloading ? "Preparing download…" : "Download example"}
                            </button>
                            {downloadError && <p className="download-error" role="alert">{downloadError}</p>}
                        </div>
                    </section>
                </div>
            )}
        </div>
    );
}
