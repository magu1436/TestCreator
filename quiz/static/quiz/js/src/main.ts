import { runPostMethod, getCSRFToken } from "@shared/server-connect-helper.js";
import { getUrl } from "@shared/utils.js"
import { NumberRangeConfigure, getNumQuestions, RadioConfigure } from "./configures.js";
import { wordlistSelector } from "./wordlist_configure.js";

const ns = NumberRangeConfigure.insatance;
const formatRadio = new RadioConfigure("quiz-format-radio");
const seqRadio = new RadioConfigure("question-sequence-radio");


document.getElementById("create-btn")?.addEventListener("click", async () => {
    showLoadingOverlay();
    const res = await fetch(getUrl("quiz:create"), {
        method: "POST",
        headers: {"X-CSRFToken": getCSRFToken()},
        body: get_config(),
    });

    hideLoadingOverlay();

    if (!res.ok) {
        alert("PDF生成時にエラーが発生しました。開発者に連絡してください。");
        return;
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
})

document.getElementById("preview-btn")?.addEventListener("click", async() => {
    const data = await runPostMethod(getUrl("quiz:preview"), JSON.stringify({
        ranges: ns.getRanges(),
        wordlistId: wordlistSelector.currentWordlist.id,
        numQuestion: getNumQuestions(),
        format: formatRadio.getCheckedButton().id,
        sequence: seqRadio.getCheckedButton().id,
    }));
    location.href = data.redirect_url;
})

const get_config = () => {
    return JSON.stringify({
        ranges: ns.getRanges(),
        wordlistId: wordlistSelector.currentWordlist.id,
        numQuestion: getNumQuestions(),
        format: formatRadio.getCheckedButton().id,
        sequence: seqRadio.getCheckedButton().id,
    })
}

const loadingOverlay = document.getElementById("loading") as HTMLDivElement;
const showLoadingOverlay = () => { loadingOverlay.classList.toggle("d-none", false); };
const hideLoadingOverlay = () => { loadingOverlay.classList.toggle("d-none", true); };