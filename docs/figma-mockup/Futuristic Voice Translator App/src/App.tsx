import { useEffect, useRef, useState } from "react";

type View = "ready" | "speaking" | "language" | "result" | "settings";

type Language = {
  name: string;
  native: string;
  code: string;
  color: string;
  symbol: "glyph" | "tree" | "sun" | "star" | "globe";
};

const languages: Language[] = [
  { name: "Amharic", native: "አማርኛ", code: "AM", color: "coral", symbol: "glyph" },
  { name: "Afaan Oromoo", native: "Afaan Oromoo", code: "OR", color: "green", symbol: "tree" },
  { name: "Tigrinya", native: "ትግርኛ", code: "TI", color: "gold", symbol: "sun" },
  { name: "Somali", native: "Soomaali", code: "SO", color: "blue", symbol: "star" },
  { name: "English", native: "English", code: "EN", color: "violet", symbol: "globe" },
];

const translations: Record<string, { source: string; output: string }> = {
  AM: { source: "ወደ ቦሌ እንዴት መሄድ እችላለሁ?", output: "How can I get to Bole?" },
  OR: { source: "Akkamitti gara Boolee deemuu danda'a?", output: "How can I get to Bole?" },
  TI: { source: "ናብ ቦሌ ብኸመይ ክኸይድ ይኽእል?", output: "How can I get to Bole?" },
  SO: { source: "Sideen ku tagi karaa Bole?", output: "How can I get to Bole?" },
  EN: { source: "How can I get to Bole?", output: "ወደ ቦሌ እንዴት መሄድ እችላለሁ?" },
};

const phraseByLanguage: Record<string, string> = {
  AM: "ወደ ቦሌ እንዴት መሄድ እችላለሁ?",
  OR: "Akkamitti gara Boolee deemuu danda'a?",
  TI: "ናብ ቦሌ ብኸመይ ክኸይድ ይኽእል?",
  SO: "Sideen ku tagi karaa Bole?",
  EN: "How can I get to Bole?",
};

function Icon({
  name,
  size = 24,
}: {
  name: "mic" | "spark" | "volume" | "close" | "check" | "arrow" | "shield" | "brain";
  size?: number;
}) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };
  const paths = {
    mic: (
      <>
        <rect x="9" y="3" width="6" height="11" rx="3" />
        <path d="M5.5 10.5a6.5 6.5 0 0 0 13 0M12 17v4M8.5 21h7" />
      </>
    ),
    spark: <path d="m12 2 1.5 5.1L18 9.7l-4.5 2.6L12 18l-1.5-5.7L6 9.7l4.5-2.6L12 2Zm6.5 13 .7 2.3 1.8 1-1.8 1.1-.7 2.3-.7-2.3-1.8-1.1 1.8-1 .7-2.3Z" />,
    volume: (
      <>
        <path d="M5 10v4h3l4 3V7l-4 3H5Z" />
        <path d="M15 9a4 4 0 0 1 0 6M17.5 6.5a7.5 7.5 0 0 1 0 11" />
      </>
    ),
    close: <path d="m6 6 12 12M18 6 6 18" />,
    check: <path d="m5 12 4.2 4.2L19 6.5" />,
    arrow: <path d="m9 18 6-6-6-6" />,
    shield: <path d="M12 3 5.5 5.6v5.7c0 4.3 2.7 7.8 6.5 9.7 3.8-1.9 6.5-5.4 6.5-9.7V5.6L12 3Zm-2.7 9 1.8 1.8 3.9-4" />,
    brain: <path d="M9.5 5.5A3 3 0 0 0 4.7 8a3 3 0 0 0 .2 5.8A3.2 3.2 0 0 0 10 17v-11.5m4.5 0A3 3 0 0 1 19.3 8a3 3 0 0 1-.2 5.8A3.2 3.2 0 0 1 14 17v-11.5M8 10h2m4 3h2m-6 4v2m4-2v2" />,
  };
  return <svg {...common}>{paths[name]}</svg>;
}

function LanguageSymbol({ type }: { type: Language["symbol"] }) {
  if (type === "glyph") return <span className="language-glyph">ሀ</span>;
  const content = {
    tree: <><path d="M12 4v16M7 18h10M12 6 7 11h10l-5-5Zm0 4-7 6h14l-7-6Z" /></>,
    sun: <><circle cx="12" cy="12" r="4" /><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1" /></>,
    star: <path d="m12 3 2.1 6.5H21l-5.5 4 2.1 6.5-5.6-4-5.6 4 2.1-6.5-5.5-4h6.9L12 3Z" />,
    globe: <><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" /></>,
  };
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">
      {content[type]}
    </svg>
  );
}

function Waveform({ active = false }: { active?: boolean }) {
  const bars = [24, 40, 62, 34, 76, 52, 88, 60, 38, 70, 46, 82, 56, 34, 64, 44, 28];
  return (
    <div className={`waveform ${active ? "active" : ""}`} aria-hidden="true">
      {bars.map((height, index) => (
        <span key={index} style={{ "--bar-height": `${height}%`, "--bar-index": index } as React.CSSProperties} />
      ))}
    </div>
  );
}

export default function App() {
  const [view, setView] = useState<View>("ready");
  const [language, setLanguage] = useState<Language>(languages[0]);
  const [targetLanguage, setTargetLanguage] = useState<Language>(languages[4]);
  const [playing, setPlaying] = useState(true);
  const [defaultTarget, setDefaultTarget] = useState("English");
  const [autoPlay, setAutoPlay] = useState(true);
  const [smartDetect, setSmartDetect] = useState(true);
  const [haptics, setHaptics] = useState(true);
  const [conversationMode, setConversationMode] = useState(false);
  const [firstLanguage, setFirstLanguage] = useState<Language>(languages[0]);
  const [secondLanguage, setSecondLanguage] = useState<Language>(languages[4]);
  const [conversationTurn, setConversationTurn] = useState(0);
  const holdTimer = useRef<number | null>(null);
  const finishingRef = useRef(false);

  const beginSpeaking = () => {
    if (view !== "ready" && !(view === "result" && conversationMode)) return;
    finishingRef.current = false;
    setView("speaking");
    holdTimer.current = window.setTimeout(() => {}, 250);
  };

  const finishSpeaking = () => {
    if (view !== "speaking" || finishingRef.current) return;
    finishingRef.current = true;
    if (holdTimer.current) window.clearTimeout(holdTimer.current);
    window.setTimeout(() => {
      if (conversationMode) {
        const source = conversationTurn % 2 === 0 ? firstLanguage : secondLanguage;
        const target = conversationTurn % 2 === 0 ? secondLanguage : firstLanguage;
        setLanguage(source);
        setTargetLanguage(target);
        setConversationTurn((turn) => turn + 1);
        setPlaying(autoPlay);
        setView("result");
      } else {
        setView("language");
      }
      finishingRef.current = false;
    }, 240);
  };

  const chooseLanguage = (chosen: Language) => {
    const preferred = languages.find((item) => item.name === defaultTarget) ?? languages[4];
    const fallback = chosen.code === "EN" ? languages[0] : languages[4];
    setLanguage(chosen);
    setTargetLanguage(preferred.code === chosen.code ? fallback : preferred);
    setPlaying(autoPlay);
    setView("result");
  };

  const reset = () => {
    setView("ready");
    setPlaying(false);
  };

  useEffect(() => {
    if (view !== "result" || !playing) return;
    const timer = window.setTimeout(() => setPlaying(false), 4200);
    return () => window.clearTimeout(timer);
  }, [view, playing]);

  useEffect(() => {
    if (view !== "speaking") return;
    const finishOnRelease = () => finishSpeaking();
    window.addEventListener("pointerup", finishOnRelease);
    window.addEventListener("pointercancel", finishOnRelease);
    return () => {
      window.removeEventListener("pointerup", finishOnRelease);
      window.removeEventListener("pointercancel", finishOnRelease);
    };
  }, [view]);

  return (
    <main className={`app-shell view-${view}`}>
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <section className="phone-frame" aria-label="Lisan voice translator">
        <header className="topbar">
          <button className="wordmark" onClick={reset} aria-label="Return to home">
            <span className="logo-mark"><Icon name="spark" size={16} /></span>
            <span>Lisan</span>
          </button>
          <button className="settings-link" onClick={() => setView("settings")}>
            <span>Advanced settings</span>
            <Icon name="arrow" size={14} />
          </button>
        </header>

        {(view === "ready" || view === "speaking") && (
          <div className="voice-view">
            <div className="intro">
              <div className="eyebrow">
                <span className="eyebrow-line" />
                <span>{view === "speaking" ? "Listening now" : "Voice translator"}</span>
              </div>
              <p className="hero-title">
                {view === "speaking" ? "I’m listening…" : <>Speak freely.<br /><span>Be understood.</span></>}
              </p>
              <p className="hero-copy">
                {view === "speaking"
                  ? "Keep holding while you speak"
                  : "Instant translation across the languages of Ethiopia and the Horn."}
              </p>
              {conversationMode && (
                <div className="conversation-active">
                  <span className={`pair-dot tone-${firstLanguage.color}`} />
                  <span>{firstLanguage.name}</span>
                  <Icon name="arrow" size={13} />
                  <span>{secondLanguage.name}</span>
                  <span className={`pair-dot tone-${secondLanguage.color}`} />
                </div>
              )}
            </div>

            <div className={`orb-stage ${view === "speaking" ? "is-speaking" : ""}`}>
              <div className="sound-orbit orbit-one" />
              <div className="sound-orbit orbit-two" />
              <div className="sound-orbit orbit-three" />
              {view === "speaking" && <Waveform active />}
              <button
                className="mic-button"
                onPointerDown={beginSpeaking}
                onPointerUp={finishSpeaking}
                onPointerCancel={finishSpeaking}
                onPointerLeave={(event) => {
                  if (event.buttons === 1) finishSpeaking();
                }}
                aria-label={view === "speaking" ? "Release to translate" : "Hold to speak"}
              >
                <span className="mic-inner"><Icon name="mic" size={34} /></span>
              </button>
            </div>

          </div>
        )}

        {view === "language" && (
          <div className="language-view">
            <div className="sheet-header">
              <div>
                <div className="eyebrow">
                  <span className="eyebrow-line" />
                  <span>We heard you</span>
                </div>
                <p className="sheet-title">Which language<br />did you speak?</p>
              </div>
              <button className="icon-button" onClick={reset} aria-label="Close language picker">
                <Icon name="close" size={20} />
              </button>
            </div>
            <p className="sheet-copy">Choose by color or symbol</p>
            <div className="language-grid">
              {languages.map((item) => (
                <button
                  key={item.code}
                  className={`language-card tone-${item.color}`}
                  onClick={() => chooseLanguage(item)}
                  aria-label={`Choose ${item.name}`}
                >
                  <span className="language-icon"><LanguageSymbol type={item.symbol} /></span>
                  <span className="language-label">
                    <strong>{item.native}</strong>
                    <small>{item.name}</small>
                  </span>
                  <span className="language-arrow"><Icon name="arrow" size={18} /></span>
                </button>
              ))}
            </div>
          </div>
        )}

        {view === "result" && (
          <div className="result-view">
            <div className="result-heading">
              <div className="eyebrow">
                <span className="eyebrow-line" />
                <span>Translation ready</span>
              </div>
              <p className="result-title">You’re understood.</p>
              <button className="icon-button" onClick={reset} aria-label="Close translation">
                <Icon name="close" size={20} />
              </button>
            </div>

            <div className="translation-card">
              <div className="translation-section source">
                <div className="language-meta">
                  <span className={`mini-swatch tone-${language.color}`}><LanguageSymbol type={language.symbol} /></span>
                  <span>{language.name}</span>
                  <span className="detected">Detected</span>
                </div>
                <p className="source-text">{translations[language.code].source}</p>
              </div>

              <div className="translation-divider">
                <span />
                <div><Icon name="spark" size={15} /></div>
                <span />
              </div>

              <div className="translation-section output">
                <div className="language-meta">
                  <span className={`mini-swatch tone-${targetLanguage.color}`}><LanguageSymbol type={targetLanguage.symbol} /></span>
                  <span>{targetLanguage.name}</span>
                </div>
                <p className="output-text">{phraseByLanguage[targetLanguage.code]}</p>
                <div className="audio-row">
                  <button
                    className={`play-button ${playing ? "playing" : ""}`}
                    onClick={() => setPlaying((current) => !current)}
                    aria-label={playing ? "Pause translation audio" : "Play translation audio"}
                  >
                    <Icon name="volume" size={19} />
                  </button>
                  <Waveform active={playing} />
                  <span className="audio-time">0:04</span>
                </div>
              </div>
            </div>

            <div className="trust-row">
              <span className="trust-badge"><Icon name="brain" size={15} /> Verified Memory</span>
              <span className="trust-badge"><Icon name="shield" size={15} /> AI Guard</span>
            </div>

            {conversationMode ? (
              <div className="conversation-continue">
                <div className="next-speaker">
                  <span className={`pair-dot tone-${targetLanguage.color}`} />
                  <span>
                    <strong>{targetLanguage.name}</strong>
                    <small>Next speaker</small>
                  </span>
                </div>
                <button
                  className="conversation-mic"
                  onPointerDown={beginSpeaking}
                  onPointerUp={finishSpeaking}
                  onPointerCancel={finishSpeaking}
                  aria-label="Hold for the next speaker"
                >
                  <Icon name="mic" size={23} />
                </button>
                <span className="continue-hint">Hold to reply</span>
              </div>
            ) : (
              <button className="speak-again" onClick={reset}>
                <span className="small-mic"><Icon name="mic" size={19} /></span>
                <span>Speak again</span>
                <Icon name="arrow" size={18} />
              </button>
            )}
          </div>
        )}

        {view === "settings" && (
          <div className="settings-view">
            <div className="settings-heading">
              <div>
                <div className="eyebrow">
                  <span className="eyebrow-line" />
                  <span>Personalize Lisan</span>
                </div>
                <p className="settings-title">Advanced<br />settings</p>
              </div>
              <button className="icon-button" onClick={reset} aria-label="Close advanced settings">
                <Icon name="close" size={20} />
              </button>
            </div>

            <div className="settings-group">
              <div className="settings-group-label">
                <span>Translation</span>
                <span>01</span>
              </div>
              <div className="setting-card target-setting">
                <div className="setting-copy">
                  <strong>Translate into</strong>
                  <small>Your default output language</small>
                </div>
                <div className="target-options">
                  {["English", "Amharic", "Somali"].map((target) => (
                    <button
                      key={target}
                      className={`target-option ${defaultTarget === target ? "selected" : ""}`}
                      onClick={() => setDefaultTarget(target)}
                    >
                      <span>{target}</span>
                      {defaultTarget === target && <Icon name="check" size={15} />}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="settings-group">
              <div className="settings-group-label">
                <span>Conversation mode</span>
                <span>02</span>
              </div>
              <div className={`conversation-setting ${conversationMode ? "enabled" : ""}`}>
                <button
                  className="conversation-switch"
                  onClick={() => setConversationMode((value) => !value)}
                  aria-pressed={conversationMode}
                >
                  <span className="conversation-symbol">
                    <Icon name="volume" size={18} />
                  </span>
                  <span className="setting-copy">
                    <strong>Automatic two-way translation</strong>
                    <small>Hear either language and translate to the other</small>
                  </span>
                  <span className={`toggle ${conversationMode ? "enabled" : ""}`} aria-hidden="true">
                    <span />
                  </span>
                </button>

                <div className="conversation-languages">
                  <LanguageChoice
                    label="First language"
                    selected={firstLanguage}
                    blockedCode={secondLanguage.code}
                    onSelect={setFirstLanguage}
                  />
                  <div className="conversation-flow">
                    <span />
                    <Icon name="arrow" size={16} />
                    <span />
                  </div>
                  <LanguageChoice
                    label="Second language"
                    selected={secondLanguage}
                    blockedCode={firstLanguage.code}
                    onSelect={setSecondLanguage}
                  />
                </div>

                <div className="conversation-explainer">
                  <Icon name="spark" size={14} />
                  <span>Lisan detects who is speaking and switches direction automatically.</span>
                </div>
              </div>
            </div>

            <div className="settings-group">
              <div className="settings-group-label">
                <span>Experience</span>
                <span>03</span>
              </div>
              <div className="settings-list">
                <SettingToggle
                  title="Smart language detection"
                  description="Recognize the language you speak"
                  enabled={smartDetect}
                  onChange={() => setSmartDetect((value) => !value)}
                />
                <SettingToggle
                  title="Auto-play translation"
                  description="Speak results aloud automatically"
                  enabled={autoPlay}
                  onChange={() => setAutoPlay((value) => !value)}
                />
                <SettingToggle
                  title="Touch feedback"
                  description="Gentle vibration when recording"
                  enabled={haptics}
                  onChange={() => setHaptics((value) => !value)}
                />
              </div>
            </div>

            <div className="privacy-note">
              <Icon name="shield" size={17} />
              <p>Your voice preferences stay private on this device.</p>
            </div>

            <button className="save-settings" onClick={reset}>
              <span>Save preferences</span>
              <Icon name="check" size={18} />
            </button>
          </div>
        )}

        <footer className="home-indicator"><span /></footer>
      </section>
    </main>
  );
}

function SettingToggle({
  title,
  description,
  enabled,
  onChange,
}: {
  title: string;
  description: string;
  enabled: boolean;
  onChange: () => void;
}) {
  return (
    <button className="setting-row" onClick={onChange} aria-pressed={enabled}>
      <span className="setting-copy">
        <strong>{title}</strong>
        <small>{description}</small>
      </span>
      <span className={`toggle ${enabled ? "enabled" : ""}`} aria-hidden="true">
        <span />
      </span>
    </button>
  );
}

function LanguageChoice({
  label,
  selected,
  blockedCode,
  onSelect,
}: {
  label: string;
  selected: Language;
  blockedCode: string;
  onSelect: (language: Language) => void;
}) {
  return (
    <div className="language-choice">
      <span className="choice-label">{label}</span>
      <div className="choice-options">
        {languages.map((item) => (
          <button
            key={item.code}
            className={`choice-option tone-${item.color} ${selected.code === item.code ? "selected" : ""}`}
            onClick={() => onSelect(item)}
            disabled={item.code === blockedCode}
            aria-label={`${label}: ${item.name}`}
          >
            <LanguageSymbol type={item.symbol} />
            <span>{item.code}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
