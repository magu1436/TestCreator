import { runPostMethod } from "@shared/server-connect-helper.js";
import {appUrls} from "./utils.js";
import { DropZone } from "./dropzone.js";
import { ResultWordRow, ResultWordTable, registerAllWordsToDatabase } from "./read-word-table.js";

const dropzone = new DropZone();
const submitBtn = document.getElementById("upload-btn") as HTMLButtonElement;
const deleteBtn = document.getElementById("delete-btn") as HTMLButtonElement;
const registerBtn = document.getElementById("register-btn") as HTMLButtonElement;

const onSubmit = async () => {
    submitBtn.disabled = true;
    submitBtn.textContent = "アップロード中"

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
    }

    submitBtn.textContent = "アップロード開始"
    submitBtn.disabled = false;
}

const table = ResultWordTable.instance;
submitBtn.addEventListener("click", onSubmit);

deleteBtn.addEventListener("click", () => {
    table.removeAllSelectedWord();
});
registerBtn.addEventListener("click", registerAllWordsToDatabase);