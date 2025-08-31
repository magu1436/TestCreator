import { WordRow, WordTable } from "./word.js";
import { WordlistSelector } from "./wordlist.js";
import { appUrls } from "./utils.js";


class ReadonlyWordTable extends WordTable{
    override registerWordRow(wordRow: WordRow, checkDuplicate?: boolean): void {
        console.log("aaaaaaa")
        const values = [wordRow.numberElement, wordRow.termElement, wordRow.meaningElement]
        values.forEach(v => { v.classList.toggle(WordRow.editableDivClassName, false) });
        super.registerWordRow(wordRow, checkDuplicate);
    }
}

const wordTable = new ReadonlyWordTable()
const ws = new WordlistSelector()

const startRangeElementId = "start-range";
const endRangeElementId = "end-range";
const searchBoxElementId = "search_box";

const startRangeElement = document.getElementById(startRangeElementId) as HTMLInputElement;
const endRangeElement = document.getElementById(endRangeElementId) as HTMLInputElement;
const searchBoxElement = document.getElementById(searchBoxElementId) as HTMLInputElement;

const onRangedByNumber = () => {
    let start = startRangeElement.valueAsNumber;
    if (Number.isNaN(start)) start = 0;
    let end = endRangeElement.valueAsNumber;
    if (Number.isNaN(end)) end = Infinity;
    wordTable.setVisibleByNumber(start, end);
}


startRangeElement.addEventListener("change", onRangedByNumber);
endRangeElement.addEventListener("change", onRangedByNumber);


ws.selectorElement.addEventListener("change", () => {
    location.href = appUrls["vocab:reference"] + `?wordlist=${ws.currentWordlist.id}`
})