import { runPostMethod } from "@shared/server-connect-helper.js";
import { WordlistSelector } from "@vocab/wordlist.js";
import { appUrls } from "./utils.js";
import { DropZone } from "./dropzone.js";
import { ProgressBar } from "./progressbar.js";
import { ResultWordRow, ResultWordTable, registerAllWordsToDatabase } from "./read-word-table.js";

const dropzone = new DropZone();
const submitBtn = document.getElementById("upload-btn") as HTMLButtonElement;
const deleteBtn = document.getElementById("delete-btn") as HTMLButtonElement;
const registerBtn = document.getElementById("register-btn") as HTMLButtonElement;
const allCheckbox = document.getElementById("all-word-checkbox") as HTMLInputElement;
const progressbar = ProgressBar.instance;
const wordlistSelector = new WordlistSelector();

const onSubmit = async () => {
    submitBtn.disabled = true;
    submitBtn.textContent = "アップロード中";
    progressbar.toggleVisible(true);

    const proceedFilesAmount = dropzone.droppedFiles.length;
    const increaseProgress = () => {
        progressbar.increase(Math.round(1 / proceedFilesAmount * 100));
    }
    for (const f of dropzone.droppedFiles){
        const fd = new FormData();
        fd.append("files", f.file);
        const data = await runPostMethod(appUrls["ocr:ocr"]!, fd);
        console.log(data.message);
        data.words.forEach((w: { number: number; term: string; meaning: string; }) => {
            const wr = new ResultWordRow(w.number, w.term, w.meaning);
            table.registerWordRow(wr);
        })
        dropzone.removeImageFile(f);
        increaseProgress();
    }

    submitBtn.textContent = "アップロード開始"
    submitBtn.disabled = false;
    progressbar.percent = 0;
    progressbar.toggleVisible(false);
}

const table = ResultWordTable.instance;
submitBtn.addEventListener("click", onSubmit);

deleteBtn.addEventListener("click", () => {
    table.removeAllSelectedWord();
});
registerBtn.addEventListener("click", registerAllWordsToDatabase);

allCheckbox.addEventListener("change", () => {
    table.words.forEach(w => {
        w.toggleSelected(allCheckbox.checked);
    })
});

wordlistSelector.selectorElement.addEventListener("change", () => {
    for (const wl of wordlistSelector.wordlists){
        if (wl.element.selected){
            table.wordlistId = wl.id;
            return;
        }
    }
})