const form = document.getElementById("search-form");
const submitButton = document.getElementById("submit-button");
const input = document.getElementById("question");
const formStatus = document.getElementById("form-status");
const answerCopy = document.getElementById("answer-copy");
const answerEmpty = document.getElementById("answer-empty");
const sourcePill = document.getElementById("source-pill");
const imageGrid = document.getElementById("image-grid");
const galleryEmpty = document.getElementById("gallery-empty");
const galleryEmptyCopy = document.getElementById("gallery-empty-copy");

let activeController = null;

function setStreamingState(isStreaming) {
    submitButton.disabled = isStreaming;
    submitButton.textContent = isStreaming ? "Streaming..." : "Explore";
    answerCopy.classList.toggle("is-streaming", isStreaming);
}

function renderImages(images) {
    imageGrid.innerHTML = "";

    if (!images.length) {
        imageGrid.classList.add("is-hidden");
        galleryEmpty.classList.remove("is-hidden");
        galleryEmptyCopy.textContent = "No related images were found for this question.";
        return;
    }

    for (const image of images) {
        const card = document.createElement("a");
        card.className = "image-card";
        card.href = image.url || "#";
        card.target = "_blank";
        card.rel = "noreferrer";

        const frame = document.createElement("div");
        frame.className = "image-frame";

        const img = document.createElement("img");
        img.src = image.url || "";
        img.alt = image.title || "Related festival image";
        frame.appendChild(img);

        const caption = document.createElement("p");
        caption.textContent = image.title || "Open image";

        card.appendChild(frame);
        card.appendChild(caption);
        imageGrid.appendChild(card);
    }

    galleryEmpty.classList.add("is-hidden");
    imageGrid.classList.remove("is-hidden");
}

function resetForStream() {
    answerCopy.textContent = "";
    answerCopy.classList.remove("is-hidden");
    answerEmpty.classList.add("is-hidden");
    sourcePill.textContent = "";
    sourcePill.classList.add("is-hidden");
    imageGrid.innerHTML = "";
    imageGrid.classList.add("is-hidden");
    galleryEmpty.classList.remove("is-hidden");
    galleryEmptyCopy.textContent = "Collecting related images...";
    formStatus.textContent = "Streaming answer...";
    setStreamingState(true);
}

function finishStream() {
    setStreamingState(false);
    if (!answerCopy.textContent.trim()) {
        answerCopy.classList.add("is-hidden");
        answerEmpty.classList.remove("is-hidden");
    }
}

async function streamAnswer() {
    if (activeController) {
        activeController.abort();
    }

    const controller = new AbortController();
    activeController = controller;
    const formData = new FormData(form);
    resetForStream();

    try {
        const response = await fetch("/stream", {
            method: "POST",
            body: formData,
            signal: controller.signal,
            headers: {
                Accept: "application/x-ndjson",
            },
        });

        if (!response.ok || !response.body) {
            throw new Error("Unable to start streaming response.");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) {
                break;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
                if (!line.trim()) {
                    continue;
                }

                const payload = JSON.parse(line);

                if (payload.type === "start") {
                    if (payload.source) {
                        sourcePill.textContent = payload.source;
                        sourcePill.classList.remove("is-hidden");
                    }
                }

                if (payload.type === "chunk") {
                    answerCopy.textContent += payload.content;
                }

                if (payload.type === "error") {
                    answerCopy.textContent = payload.message;
                    if (payload.source) {
                        sourcePill.textContent = payload.source;
                        sourcePill.classList.remove("is-hidden");
                    }
                    galleryEmptyCopy.textContent = "Image search was skipped because the answer did not complete.";
                    formStatus.textContent = "Streaming stopped with an error.";
                    finishStream();
                    return;
                }

                if (payload.type === "done") {
                    if (payload.source) {
                        sourcePill.textContent = payload.source;
                        sourcePill.classList.remove("is-hidden");
                    }
                    renderImages(payload.images || []);
                    formStatus.textContent = "Answer complete.";
                }
            }
        }
    } catch (error) {
        if (error.name === "AbortError") {
            if (activeController === controller) {
                formStatus.textContent = "Starting a new search...";
            }
            return;
        }

        answerCopy.textContent = "Streaming failed. Please try again.";
        answerCopy.classList.remove("is-hidden");
        answerEmpty.classList.add("is-hidden");
        galleryEmpty.classList.remove("is-hidden");
        galleryEmptyCopy.textContent = "Image results are unavailable right now.";
        formStatus.textContent = "Streaming failed.";
    } finally {
        if (activeController === controller) {
            finishStream();
            activeController = null;
        }
    }
}

if (form) {
    form.addEventListener("submit", (event) => {
        event.preventDefault();
        streamAnswer();
    });
}
