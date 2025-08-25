import {SelectableItem} from "@shared/selectable-item.js";
import {Wordlist} from "./wordlist.js";
import {appUrls, getCSRFToken} from "./utils.js";

export class WordRow extends SelectableItem {

    static readonly uniqueClassName = "word-row";
    static readonly termClassName = "word-term";
    static readonly numberClassName = "word-number";
    static readonly meaningClassName = "word-meaning";
    static readonly editorClassName = "word-edited-by";
    static readonly contentClassNames = ["word-info", "d-flex", "flex-row", "flex-shrink-0"];
    static readonly childrenClassNames = ["p-2", "border", "overflow-auto"];

    readonly id: number;
    readonly numberElement: HTMLDivElement;
    readonly termElement: HTMLDivElement;
    readonly meaningElement: HTMLDivElement;
    readonly editorElement: HTMLDivElement;

    protected _visible = true;

    constructor(id: number, wordNum: number, term: string, meaning: string, latestEditedBy: string){
        const contents = WordRow.createContent(wordNum, term, meaning, latestEditedBy);
        super(contents["content"]);
        this.id = id;
        this.numberElement = contents["number"];
        this.termElement = contents["term"];
        this.meaningElement = contents["meaning"];
        this.editorElement = contents["editor"];
    }

    protected static createContent(num: number | String, term: String, meaning: String, editor: String){
        const content = document.createElement("div");
        content.classList.add(...WordRow.contentClassNames);
        
        const wordNumber = Object.assign(document.createElement("div"), {
            className: WordRow.numberClassName,
            textContent: String(num),
        });

        const wordTerm = Object.assign(document.createElement("div"), {
            className: WordRow.termClassName,
            textContent: term,
        });

        const wordMeaning = Object.assign(document.createElement("div"), {
            className: WordRow.meaningClassName,
            textContent: meaning,
        });

        const wordEditor = Object.assign(document.createElement("div"), {
            className: WordRow.editorClassName,
            textContent: editor,
        });

        const values = [wordNumber, wordTerm, wordMeaning, wordEditor];
        values.forEach(v => {
            v.classList.add(...WordRow.childrenClassNames);
            content.appendChild(v);
        });

        return {
            "content": content,
            "number": wordNumber,
            "term": wordTerm,
            "meaning": wordMeaning,
            "editor": wordEditor,
        };
    }

    get number(){
        return Number(this.numberElement.textContent);
    }
    set number(num: number){
        this.numberElement.textContent = String(num).trim();
    }

    get term(){
        return this.termElement.textContent;
    }
    set term(term: string){
        this.termElement.textContent = term.trim();
    }

    get meaning(){
        return this.meaningElement.textContent;
    }
    set meaning(meaning: string){
        this.meaningElement.textContent = meaning.trim();
    }

    get editor(){
        return this.editorElement.textContent;
    }
    set editor(editor: string){
        this.editorElement.textContent = editor.trim();
    }

    get isVisible(){
        return this._visible;
    }
    set isVisible(visible: boolean){
        this.setVisible(visible);
    }

    setVisible(visible: boolean): this{
        this.element.classList.toggle("d-none", !visible);
        this.element.classList.toggle("d-flex", visible);
        this._visible = visible
        if (!visible) this.toggleSelected(false);
        return this;
    }
}


export class WordTable {
    static readonly tableDivId = "word-table-content";
    readonly tableDivElement: HTMLDivElement;

    protected _words: WordRow[] = [];
    readonly wordlistId: number;

    constructor(){
        const elem = document.getElementById(WordTable.tableDivId) as HTMLDivElement | null;
        if(elem == null) throw new Error(`${WordTable.tableDivId} element does not exist.`);
        this.tableDivElement = elem;
        const wordlistId = document.getElementById("wordlist-selector")?.dataset.id;
        if (!wordlistId) throw new Error("wordlist-selector element does not exist.");
        this.wordlistId = Number(wordlistId);
        this.createWordTable();
    }

    protected createWordTable(){
        const urlName = "wordbank:read"
        const url = appUrls[urlName];
        if(!url) throw new Error(`${urlName} app doesn't registered.`);
        fetch(url, {
            method: "POST",
            headers: {"X-CSRFToken": getCSRFToken()},
            body: JSON.stringify({"id": this.wordlistId})
        })
        .then(async (res) => {
            const data = await res.json().catch(() => ({}));

            if (!res.ok){
                const err = data.error || data.err;
                alert(err || "何らかのエラーが発生しました.");
                throw new Error("read_failed");
            }

            return data;
        })
        .then((res) => {
            for (const word of res.words){
                const wordRow = new WordRow(
                    word.id,
                    word.number,
                    word.term,
                    word.meaning,
                    word.latest_edited_by
                );
                this.registerWordRow(wordRow);
            }
        })
        .catch((err) => {
            if (err.message !== "read_failed"){
                console.error(err);
                alert("想定外のエラーが生じました!");
            }
        })
    }

    registerWordRow(wordRow: WordRow, checkDuplicate: boolean = true): void{
        if (checkDuplicate && this._words.includes(wordRow)) {
            throw new Error("Word must not be registered in duplicate")
        }

        for (let i = 0; i < this._words.length; i++){
            const compared = this._words[i]!    // 中身がないときはfor文が回らないため, undefinedになることはない
            if (wordRow.id < compared.id){
                this._words.splice(i, 0, wordRow);
                compared.element.before(wordRow.element);
                break;
            }
        }
        if (!this._words.includes(wordRow)){
            this._words.push(wordRow);
            this.tableDivElement.appendChild(wordRow.element);
        }
    }

    get words(): WordRow[]{
        return this._words;
    }

    setVisibleByNumber(start: number, end: number){
        const visibleWordRows: WordRow[] = [];
        this._words.forEach(wr => {
            const isIn = (start <= wr.id && wr.id <= end);
            wr.setVisible(isIn);
            if (isIn) visibleWordRows.push(wr);
        })
        return visibleWordRows;
    }

    setVisibleByKeywords(...keys: string[]){
        this._words.forEach(wr => {
            wr.setVisible(true);
            for (const k of keys){
                if (!wr.term.includes(k) && !wr.meaning.includes(k) && !wr.editor.includes(k)){
                    wr.setVisible(false);
                    wr.toggleSelected(false);
                    break;
                }
            }
        })
        return this._words.filter(wr => {wr.isVisible});
    }
}