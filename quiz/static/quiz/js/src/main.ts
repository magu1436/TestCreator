import { runPostMethod } from "@shared/server-connect-helper.js";
import { appUrls } from "./utils.js";
import { WordlistSelector } from "@vocab/wordlist.js";
import { NumberRangeConfigure, getNumQuestions, RadioConfigure } from "./configures.js";

const ns = NumberRangeConfigure.insatance;
const formatRadio = new RadioConfigure("quiz-format-radio");
const seqRadio = new RadioConfigure("question-sequence-radio");
const sl = new WordlistSelector();


document.getElementById("create-btn")?.addEventListener("click", () => {
    runPostMethod(appUrls["quiz:create"]!, JSON.stringify({
        ranges: ns.getRanges(),
        wordlistId: sl.currentWordlist.id,
        numQuestion: getNumQuestions(),
        sequence: seqRadio.getCheckedButton().id,
    }))
})