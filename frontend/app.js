const form = document.querySelector("#speech-form");
const textInput = document.querySelector("#speech-text");
const characterCount = document.querySelector("#character-count");
const pasteTextButton = document.querySelector("#paste-text");
const clearTextButton = document.querySelector("#clear-text");
const engineSelect = document.querySelector("#engine");
const voiceSelect = document.querySelector("#voice");
const languageSelect = document.querySelector("#language");
const speedInput = document.querySelector("#speed");
const speedValue = document.querySelector("#speed-value");
const generateButton = document.querySelector("#generate");
const statusMessage = document.querySelector("#status");
const discoveryStatus = document.querySelector("#discovery-status");
const result = document.querySelector("#result");
const speechEngineDisclosure = document.querySelector("#speech-engine-disclosure");
const audioPlayer = document.querySelector("#audio-player");
const downloadLink = document.querySelector("#download");
const serviceStatus = document.querySelector("#service-status");
const speechTab = document.querySelector("#speech-tab");
const configurationTab = document.querySelector("#configuration-tab");
const speechPanel = document.querySelector("#speech-panel");
const configurationPanel = document.querySelector("#configuration-panel");
const targetSelect = document.querySelector("#target");

const supportedLanguages = new Set(["de-DE", "en-US", "en-GB"]);
const voiceDisplayNames = new Map([
  ["de-male", "Male (German)"],
  ["de-female", "Female (German)"],
  ["en-male", "Male (English)"],
  ["en-female", "Female (English)"],
]);
let availableEngines = [];
let audioUrl;
let endpointRevision = 0;
let speechRequestSequence = 0;
let currentSpeechRequest = 0;
let currentSpeechRevision = 0;

async function loadTargets() {
  const response = await fetch("/api/targets", { cache: "no-store" });
  if (!response.ok) throw new Error("Approved speech services are unavailable.");
  const payload = await response.json();
  targetSelect.replaceChildren(...payload.targets.map(({ id, label }) => {
    const option = document.createElement("option");
    option.value = id;
    option.textContent = label;
    return option;
  }));
  targetSelect.value = payload.selected;
  targetSelect.disabled = payload.targets.length < 2;
}

targetSelect.addEventListener("change", async () => {
  targetSelect.disabled = true;
  try {
    const response = await fetch("/api/target", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: targetSelect.value }),
    });
    if (!response.ok) throw new Error("That speech service is unavailable.");
    endpointRevision += 1;
    clearAudio();
    await Promise.all([checkService(), loadEngineCatalog()]);
  } catch (error) {
    statusMessage.textContent = error.message;
  } finally {
    targetSelect.disabled = false;
  }
});

function isNetworkError(error) {
  return error instanceof TypeError || error?.message === "Failed to fetch";
}

function showTab(tab) {
  const configuration = tab === "configuration";
  speechTab.classList.toggle("active", !configuration);
  configurationTab.classList.toggle("active", configuration);
  speechPanel.hidden = configuration;
  configurationPanel.hidden = !configuration;
}

speechTab.addEventListener("click", () => showTab("speech"));
configurationTab.addEventListener("click", () => showTab("configuration"));

function clearAudio() {
  audioPlayer.pause();
  audioPlayer.removeAttribute("src");
  downloadLink.removeAttribute("href");
  result.hidden = true;
  speechEngineDisclosure.textContent = "";
  if (audioUrl) {
    URL.revokeObjectURL(audioUrl);
    audioUrl = undefined;
  }
}

textInput.addEventListener("input", () => {
  characterCount.textContent = `${textInput.value.length.toLocaleString()} / 5,000`;
  clearTextButton.disabled = textInput.value.length === 0;
});

pasteTextButton.addEventListener("click", async () => {
  statusMessage.textContent = "";
  try {
    const clipboardText = await navigator.clipboard.readText();
    textInput.value = clipboardText.slice(0, 5000);
    textInput.dispatchEvent(new Event("input"));
    clearAudio();
    textInput.focus();
    if (clipboardText.length === 0) {
      statusMessage.textContent = "The clipboard does not contain any text.";
    } else if (clipboardText.length > 5000) {
      statusMessage.textContent =
        "Clipboard text was truncated to the 5,000-character limit.";
    }
  } catch {
    statusMessage.textContent =
      "Clipboard access is unavailable. Allow clipboard permission and try again.";
  }
});

clearTextButton.addEventListener("click", () => {
  textInput.value = "";
  textInput.dispatchEvent(new Event("input"));
  statusMessage.textContent = "";
  clearAudio();
  textInput.focus();
});

speedInput.addEventListener("input", () => {
  speedValue.value = `${Number(speedInput.value).toFixed(1)}×`;
});

async function checkService() {
  const revision = endpointRevision;
  try {
    const response = await fetch("/api/healthz", { cache: "no-store" });
    if (revision !== endpointRevision) return;
    if (!response.ok) throw new Error("Service unavailable");
    serviceStatus.dataset.state = "online";
    serviceStatus.lastChild.textContent = " SERVICE CONNECTED";
  } catch {
    if (revision !== endpointRevision) return;
    serviceStatus.dataset.state = "offline";
    serviceStatus.lastChild.textContent = " SERVICE UNAVAILABLE";
  }
}

function normalizeCatalog(catalog) {
  if (!catalog || typeof catalog !== "object" || !Array.isArray(catalog.engines)) {
    throw new Error("The speech service returned an invalid catalog.");
  }
  return catalog.engines.flatMap((engine) => {
    if (
      !engine ||
      engine.available !== true ||
      typeof engine.id !== "string" ||
      !engine.id.trim()
    ) {
      return [];
    }
    const languages = Array.isArray(engine.languages)
      ? [
          ...new Set(
            engine.languages.filter((language) =>
              supportedLanguages.has(language),
            ),
          ),
        ]
      : [];
    if (
      languages.length === 0 ||
      !engine.voices ||
      typeof engine.voices !== "object"
    )
      return [];

    const voices = Object.fromEntries(
      languages.map((language) => [
        language,
        Array.isArray(engine.voices[language])
          ? [
              ...new Set(
                engine.voices[language].filter(
                  (voice) => typeof voice === "string" && voice.trim(),
                ),
              ),
            ]
          : [],
      ]),
    );
    return [{ id: engine.id, languages, voices }];
  });
}

function setOptions(
  select,
  values,
  preferredValue,
  labelForValue = (value) => value || "Engine default",
) {
  select.replaceChildren(
    ...values.map((value) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = labelForValue(value);
      return option;
    }),
  );
  if (values.includes(preferredValue)) select.value = preferredValue;
  else if (values.length > 0) select.value = values[0];
}

function renderVoices(engine, preferredVoice = voiceSelect.value) {
  const language = languageSelect.value;
  if (!language) {
    setOptions(voiceSelect, [""], "");
    voiceSelect.disabled = true;
    return;
  }
  const voices = [...new Set(engine.voices[language] || [])];
  setOptions(
    voiceSelect,
    ["", ...voices],
    preferredVoice,
    (voice) => voiceDisplayNames.get(voice) || voice || "Engine default",
  );
  voiceSelect.disabled = voices.length === 0;
}

function renderEngines(preferredEngine = engineSelect.value) {
  engineSelect.hidden = false;
  voiceSelect.hidden = false;
  const language = languageSelect.value;
  const engines = availableEngines.filter(
    (engine) => !language || engine.languages.includes(language),
  );
  setOptions(
    engineSelect,
    engines.map((engine) => engine.id),
    preferredEngine,
  );
  engineSelect.disabled = engines.length === 0;

  const selectedEngine = engines.find(
    (engine) => engine.id === engineSelect.value,
  );
  if (!selectedEngine) {
    setOptions(voiceSelect, [], "");
    voiceSelect.disabled = true;
    generateButton.disabled = true;
    discoveryStatus.textContent =
      availableEngines.length === 0
        ? "No speech engines are currently available."
        : "No available speech engines support the selected language.";
    return;
  }

  renderVoices(selectedEngine);
  generateButton.disabled = false;
  discoveryStatus.textContent = "Speech options are ready.";
}

async function loadEngineCatalog() {
  const revision = endpointRevision;
  try {
    const response = await fetch("/api/v1/audio/engines", {
      cache: "no-store",
    });
    if (response.status === 404 || response.status === 501) {
      if (revision !== endpointRevision) return;
      availableEngines = [];
      engineSelect.hidden = true;
      voiceSelect.hidden = true;
      generateButton.disabled = false;
      discoveryStatus.textContent = "This service does not support discovery. Service defaults will be used.";
      return;
    }
    if (!response.ok) {
      const message =
        response.status === 401 || response.status === 403
          ? "Discovery authorization failed."
          : response.status >= 500
            ? "Speech options are unavailable. Check the service connection and try again."
            : "The speech service returned an invalid discovery response.";
      throw new Error(message);
    }
    let catalog;
    try {
      catalog = await response.json();
    } catch {
      throw new Error("The speech service returned a malformed catalog.");
    }
    const normalized = normalizeCatalog(catalog);
    if (revision !== endpointRevision) return;
    availableEngines = normalized;
    if (availableEngines.length === 0) {
      renderEngines("");
      return;
    }
    renderEngines(
      engineSelect.value ||
        (availableEngines.some((engine) => engine.id === "macos-say")
          ? "macos-say"
          : availableEngines[0].id),
    );
  } catch (error) {
    if (revision !== endpointRevision) return;
    availableEngines = [];
    setOptions(engineSelect, [], "");
    setOptions(voiceSelect, [], "");
    engineSelect.disabled = true;
    voiceSelect.disabled = true;
    generateButton.disabled = true;
    discoveryStatus.textContent = isNetworkError(error)
      ? "Could not reach the speech service. Check the service connection and try again."
      : error.message;
  }
}

languageSelect.addEventListener("change", () => renderEngines());
engineSelect.addEventListener("change", () => {
  const selectedEngine = availableEngines.find(
    (engine) => engine.id === engineSelect.value,
  );
  if (selectedEngine) renderVoices(selectedEngine, "");
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const selectedEngine = availableEngines.find(
    (engine) => engine.id === engineSelect.value,
  );
  if ((!selectedEngine && availableEngines.length > 0) || generateButton.disabled) return;
  statusMessage.textContent = "";
  clearAudio();
  generateButton.disabled = true;
  const speechRevision = endpointRevision;
  const speechRequest = ++speechRequestSequence;
  currentSpeechRequest = speechRequest;
  currentSpeechRevision = speechRevision;
  generateButton.firstElementChild.textContent = "Generating…";

  const request = {
    input: textInput.value,
    response_format: document.querySelector("#format").value,
    speed: Number(speedInput.value),
  };
  if (selectedEngine) request.model = selectedEngine.id;
  const language = languageSelect.value;
  if (language) request.language = language;
  if (voiceSelect.value) request.voice = voiceSelect.value;

  try {
    const response = await fetch("/api/v1/audio/speech", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      cache: "no-store",
    });
    if (!response.ok) {
      let message = `Speech generation failed (HTTP ${response.status}).`;
      try {
        const error = await response.json();
        if (typeof error.detail === "string") message = error.detail;
      } catch {
        // Keep the status-only message when the service does not return JSON.
      }
      throw new Error(message);
    }
    const audio = await response.blob();
    if (speechRevision !== endpointRevision || currentSpeechRequest !== speechRequest) return;
    if (audio.size === 0)
      throw new Error("The service returned an empty audio file.");

    audioUrl = URL.createObjectURL(audio);
    audioPlayer.src = audioUrl;
    const format = document.querySelector("#format").value;
    downloadLink.href = audioUrl;
    downloadLink.download = `speech.${format}`;
    const backend = response.headers.get("X-Speech-Backend");
    const fallback = response.headers.get("X-Speech-Fallback");
    const reason = response.headers.get("X-Speech-Fallback-Reason");
    const actualEngine = /^[a-z0-9-]{1,40}$/.test(backend ?? "") ? backend : "not reported";
    const fallbackReason = /^fish_[a-z_]{1,40}$/.test(reason ?? "")
      ? reason
      : "reason not reported";
    speechEngineDisclosure.textContent =
      `Actual engine: ${actualEngine}. ` +
      (fallback === "true"
        ? `Fallback used (${fallbackReason}).`
        : fallback === "false"
          ? "No fallback."
          : "Fallback status not reported.");
    result.hidden = false;
    serviceStatus.dataset.state = "online";
    serviceStatus.lastChild.textContent = " SERVICE CONNECTED";
    try {
      await audioPlayer.play();
    } catch {
      if (speechRevision !== endpointRevision || currentSpeechRequest !== speechRequest) return;
      statusMessage.textContent =
        "Audio is ready, but your browser blocked automatic playback. Select play to listen.";
    }
  } catch (error) {
    if (speechRevision !== endpointRevision || currentSpeechRequest !== speechRequest) return;
    statusMessage.textContent =
      isNetworkError(error)
        ? "Could not reach the speech service. Check the service connection and try again."
        : error.message;
    serviceStatus.dataset.state = "offline";
    serviceStatus.lastChild.textContent = " SERVICE UNAVAILABLE";
  } finally {
    if (currentSpeechRequest === speechRequest) {
      currentSpeechRequest = 0;
      currentSpeechRevision = 0;
      generateButton.disabled = false;
      generateButton.firstElementChild.textContent = "Generate speech";
    }
  }
});

checkService();
loadTargets().catch((error) => { statusMessage.textContent = error.message; });
loadEngineCatalog();
