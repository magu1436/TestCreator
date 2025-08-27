import { WordRow, WordTable } from "@vocab/word.js";
import { runPostMethod } from "@shared/server-connect-helper.js";
import { appUrls } from "./utils.js";

let temp_next_id = 0;

const createTempId = () => {
    return temp_next_id++;
}

export class ResultWordRow extends WordRow{
    constructor(wordNum: number, term: string, meaning: string){
        super(createTempId(), wordNum, term, meaning, "");
        this.editorElement.classList.add("d-none");
    }
}

export class ResultWordTable extends WordTable{

    constructor(){
        super(false);
    }

    protected override commitEdit(): Promise<void> {
        return super.commitEdit(false);
    }

    static override get instance(){
        if (!ResultWordTable._instance) ResultWordTable._instance = new ResultWordTable();
        return ResultWordTable._instance as ResultWordTable
    }
}

export const registerAllWordsToDatabase = async () => {
    const table = ResultWordTable.instance;
    for (const w of table.words){
        const fd = new FormData();
        fd.append("number", String(w.number));
        fd.append("term", w.term);
        fd.append("meaning", w.meaning);
        fd.append("wordlist", String(table.wordlistId));
        const data = await runPostMethod(appUrls["vocab:register"]!, fd);
        if (data.ok) table.removeWordRow(w);
    }
}