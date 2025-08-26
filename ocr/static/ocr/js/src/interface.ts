import { runPostMethod } from "@shared/server-connect-helper.js";
import {appUrls} from "./utils.js";
import { DropZone } from "./dropzone.js";
import { ResultWordRow, ResultWordTable } from "./read-word-table.js";

const dropzone = new DropZone();
const submitBtn = document.getElementById("upload-btn") as HTMLButtonElement;

const onSubmit = async () => {
    submitBtn.disabled = true;
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
    submitBtn.disabled = false;
}

const table = ResultWordTable.instance;
submitBtn.addEventListener("click", onSubmit);