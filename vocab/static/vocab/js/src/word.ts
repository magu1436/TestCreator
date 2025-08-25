import {SelectableItem} from "@shared/selectable-item.js";
import {appUrls, getCSRFToken, runPostMethod} from "./utils.js";

export class WordRow extends SelectableItem {

    static readonly uniqueClassName = "word-row";
    static readonly termClassName = "word-term";
    static readonly numberClassName = "word-number";
    static readonly meaningClassName = "word-meaning";
    static readonly editorClassName = "word-edited-by";
    static readonly contentClassNames = ["d-flex", "flex-row", "flex-shrink-0"];
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

    /**
     * contentを作成して返す関数. 主に初期化処理で使用する.  
     * @param num 単語番号
     * @param term 単語
     * @param meaning 意味
     * @param editor 最終更新者
     * @returns それぞれのHTML要素を保持する辞書
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

    /**
     * 可視化状態をセットするメソッド.  
     * @param visible 可視化するかどうか. Trueで見えるようにする.  
     * @returns 自身のインスタンス
     */
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

    /**
     * 単語テーブルを作成する初期化処理.
     */
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

    /**
     * 単語テーブルに単語を登録するメソッド.  
     * 追加する単語の番号を参照して, 昇順になるように挿入する.  
     * デフォルトではIDをもとに引数で受け取った `wordRow` がすでに登録されていないか判定し,  
     * 既に同じ単語行が登録されている場合はエラーを投げる.  
     * サーバーとのやり取りは行わない.  
     * @param wordRow 単語の行要素
     * @param checkDuplicate 同じ単語が登録されていないかチェックするかどうか.
     */
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

    /**
     * 単語を単語テーブルから削除するメソッド.
     * @param id 単語のid
     */
    removeWordRow(id: number): WordRow;
    /**
     * 単語行を単語テーブルから削除するメソッド.
     * @param wordRow 単語の行要素
     */
    removeWordRow(wordRow: WordRow): WordRow;
    removeWordRow(id_or_wordRow: number | WordRow){
        const id = (typeof id_or_wordRow == "number") ? id_or_wordRow : id_or_wordRow.id;
        const targetWordRow = this._words.find(wr => wr.id == id);
        if (targetWordRow == null) throw new Error(`No word have id: ${id}`);
        this._words = this._words.filter(wr => wr !== targetWordRow);
        const removedWordRow = this.tableDivElement.removeChild(targetWordRow.element);
        if (!removedWordRow) throw new Error("Removing wordRow from table was failed.");
        return targetWordRow;
    }

    removeAllSelectedWord(){
        this.selectedWords.forEach(wr => this.removeWordRow(wr));
    }

    get words(): ReadonlyArray<WordRow>{
        return this._words;
    }

    get selectedWords(): ReadonlyArray<WordRow>{
        return this._words.filter(wr => wr.isSelected);
    }

    /**
     * 指定の単語番号の範囲の単語行のみを可視化する関数.  
     * @param start 範囲の最初の数字
     * @param end 範囲の終端の数字(自身含む)
     * @returns {WordRow[]} 可視化されている `WordRow` オブジェクトの配列
     */
    setVisibleByNumber(start: number, end: number){
        const visibleWordRows: WordRow[] = [];
        this._words.forEach(wr => {
            const isIn = (start <= wr.id && wr.id <= end);
            wr.setVisible(isIn);
            if (isIn) visibleWordRows.push(wr);
        })
        return visibleWordRows;
    }

    /**
     * 特定のキーワードを含む単語のみを可視化させるメソッド.
     * @param keys 検索キーワード
     * @returns {WordRow[]} 可視化されている `WordRow` 配列
     */
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