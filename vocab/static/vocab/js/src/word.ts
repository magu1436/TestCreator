import {SelectableElement} from "@shared/selectable-item.js";

export class WordRow extends SelectableElement{

    static readonly uniqueClassName = "word-row";
    static readonly termClassName = "word-term";
    static readonly numberClassName = "word-number";
    static readonly meaningClassName = "word-meaning";
    static readonly editorClassName = "word-edited-by";
    static readonly contentClassNames = ["d-flex", "flex-row", "flex-shrink-0"];
    static readonly childrenClassNames = ["p-2", "border", "overflow-auto"];

    readonly wordId: number;
    readonly numberElement: HTMLDivElement;
    readonly termElement: HTMLDivElement;
    readonly meaningElement: HTMLDivElement;
    readonly editorElement: HTMLDivElement;

    protected _visible = true;

    /**
     * コンストラクタ
     * @param id 単語のID
     * @param wordNum 単語番号
     * @param term 単語
     * @param meaning 意味
     * @param latestEditedBy 最終編集者
     */
    constructor(id: number, wordNum: number, term: string, meaning: string, latestEditedBy: string){
        const contents = WordRow.createContent(wordNum, term, meaning, latestEditedBy);
        super(WordRow.uniqueClassName, contents["content"]);
        this.wordId = id;
        this.numberElement = contents["number"];
        this.termElement = contents["term"];
        this.meaningElement = contents["meaning"];
        this.editorElement = contents["editor"];
    }

    /**
     * 単語の値を保持する要素を作成するメソッド.
     * @param num 単語番号
     * @param term 単語
     * @param meaning 意味
     * @param editor 最終編集者
     * @returns 作成した各要素を保持する辞書
     */
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
            classname: WordRow.meaningClassName,
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
        this.numberElement.textContent = String(num);
    }

    get term(){
        return this.termElement.textContent;
    }
    set term(term: string){
        this.termElement.textContent = term;
    }

    get meaning(){
        return this.meaningElement.textContent;
    }
    set meaning(meaning: string){
        this.meaningElement.textContent = meaning;
    }

    get editor(){
        return this.editorElement.textContent;
    }
    set editor(editor: string){
        this.editorElement.textContent = editor;
    }

    get isVisible(){
        return this._visible;
    }
    set isVisible(visible: boolean){
        this.setVisible(visible);
    }

    setVisible(visible: boolean): this{
        this.classList.toggle("d-none", !visible);
        this.classList.toggle("d-flex", visible);
        this._visible = visible
        if (!visible) this.toggleSelected(false);
        return this;
    }
    
}

export class WordTable{

    static readonly tableDivId = "word-table-content";
    readonly tableDivElement: HTMLDivElement;
    
    protected _words: WordRow[] = [];

    constructor(...words: WordRow[]){
        const elem = document.getElementById(WordTable.tableDivId) as HTMLDivElement | null;
        if(elem == null) throw new Error(`${WordTable.tableDivId} element does not exist.`);
        this.tableDivElement = elem;
        this._words = this._words.concat(words);
    }

    registerWordRow(wordRow: WordRow): void;
    registerWordRow(id: number, num: number, term: string, meaning: string, editor: string): void;
    registerWordRow(wordRowOrId: WordRow | number, num?: number, term?:string, meaning?: string, editor?: string){
        let wordRow: WordRow;
        if (
            !(wordRowOrId instanceof WordRow) && (
                (num != null) && (term != null) && (meaning != null) && (editor != null)
            )){
            wordRow = new WordRow(wordRowOrId, num, term, meaning, editor);
        } else {
            wordRow = wordRowOrId as WordRow;
        }

        for (let i = 0; i < this._words.length; i++){
            const comparedWordRow = this._words[i];
            if (comparedWordRow == null || wordRow.wordId < comparedWordRow.wordId){
                this._words.splice(i, 0, wordRow);
                comparedWordRow?.before(wordRow);
                break;
            }
        }
        if (!this._words.includes(wordRow)){
            this._words.push(wordRow);
            this.tableDivElement.appendChild(wordRow);
        }
    }

    getWordRowByWordId(id: number): WordRow | null{
        this._words.forEach(wr => {
            if (wr.wordId == id) return wr;
        });
        return null;
    }

    get words(): WordRow[]{
        return this._words.concat()
    }

    setVisibleByNumber(start: number, end: number){
        const visibleWordRows: WordRow[] = [];
        this._words.forEach(wr => {
            const isIn = (start <= wr.wordId && wr.wordId <= end)
            wr.setVisible(isIn)
            if (isIn) visibleWordRows.push(wr);
        })
        return visibleWordRows;
    }

    setVisibleByKeywords(...keys: string[]){
        this._words.forEach(wr => {
            wr.setVisible(true);
            for (const k of keys){
                if (!(wr.term.includes(k) || wr.meaning.includes(k) || wr.editor.includes(k))){
                    wr.setVisible(false);
                    wr.toggleSelected(false);
                    break;
                }
            }
        })
        return this._words.filter(wr => {wr.isVisible});
    }

}