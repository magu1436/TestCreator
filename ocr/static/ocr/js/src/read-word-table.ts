import { WordRow } from "@vocab/word.js";

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