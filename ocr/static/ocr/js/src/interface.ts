import { runPostMethod } from "@shared/server-connect-helper.js";
import { getUrl } from "@shared/utils.js";
import { WordlistSelector } from "@vocab/wordlist.js";
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
    // エラー(利用上限・OCR失敗・通信失敗)が起きたら残りのファイルは処理せず、追加済みの行は残す。
    // エラー内容は共通処理(runPostMethod)が alert で通知済み。
    try {
        for (const f of dropzone.droppedFiles){
            const fd = new FormData();
            fd.append("files", f.file);
            const data = await runPostMethod(getUrl("ocr:ocr"), fd);
            // 通信失敗時は例外ではなくundefinedが返る。
            if (!data) break;
            console.log(data.message);
            data.words.forEach((w: { number: number; term: string; meaning: string; }) => {
                const wr = new ResultWordRow(w.number, w.term, w.meaning);
                table.registerWordRow(wr);
            })
            dropzone.removeImageFile(f);
            increaseProgress();
        }
    } catch (err) {
        // サーバーがエラーを返した場合(429・502など)。通知済みのため記録だけ残して打ち切る。
        console.error(err);
    } finally {
        submitBtn.textContent = "アップロード開始"
        submitBtn.disabled = false;
        progressbar.percent = 0;
        progressbar.toggleVisible(false);
    }
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