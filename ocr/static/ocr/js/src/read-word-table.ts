import { WordRow, WordTable } from "@vocab/word.js";

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