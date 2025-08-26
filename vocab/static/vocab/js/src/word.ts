import {SelectableItem} from "@shared/selectable-item.js";
import {appUrls, getCSRFToken, runPostMethod} from "./utils.js";

export class WordRow extends SelectableItem {

    static readonly uniqueClassName = "word-row";
    static readonly termClassName = "word-term";
    static readonly numberClassName = "word-number";
    static readonly meaningClassName = "word-meaning";
    static readonly editorClassName = "word-edited-by";
    static readonly editableDivClassName = "editable";
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

        this.element.dataset.id = String(this.id);
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
            v.classList.add(...WordRow.childrenClassNames, WordRow.editableDivClassName);
            content.appendChild(v);
        });
        wordEditor.classList.remove(WordRow.editableDivClassName);

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
    protected static _instance: WordTable;

    static readonly tableDivId = "word-table-content";
    readonly tableDivElement: HTMLDivElement;

    protected static currentEditorInput: HTMLInputElement | null = null;
    protected static originalEditorDiv: HTMLDivElement | null = null;
    protected static currentEditorWordRow: WordRow | null = null;

    protected _words: WordRow[] = [];
    readonly wordlistId: number;

    /**
     * コンストラクタ
     * @param runCreateTable 
     * 初期化処理として単語帳に掲載されている単語で単語テーブルを作成するかどうか.
     */
    constructor(runCreateTable: boolean = true){
        if (WordTable._instance) throw new Error("This class is a singleton");
        WordTable._instance = this;

        const elem = document.getElementById(WordTable.tableDivId) as HTMLDivElement | null;
        if(elem == null) throw new Error(`${WordTable.tableDivId} element does not exist.`);
        this.tableDivElement = elem;
        const wordlistId = document.getElementById("word-table")?.dataset.wordlistId;
        if (!wordlistId) throw new Error("wordtable element does not exist.");
        this.wordlistId = Number(wordlistId);
        if (runCreateTable) this.createWordTable();
        this.tableDivElement.addEventListener("dblclick", (e) => {
            this.onEditableElemDBClick(e);
        });
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
                    word.editor
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

    /**
     * 選択された全ての単語を削除するメソッド.
     */
    removeAllSelectedWord(){
        this.selectedWords.forEach(wr => this.removeWordRow(wr));
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
            const isIn = (start <= wr.number && wr.number <= end);
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

    /**
     * 編集状態を更新するメソッド.
     * @param input 編集input要素
     * @param origin 編集前のdiv要素
     * @param wordRow 情報を編集する単語行
     */
    protected setCurrentEditorState(input: HTMLInputElement | null, origin: HTMLDivElement | null, wordRow: WordRow | null){
        WordTable.currentEditorInput = input;
        WordTable.originalEditorDiv = origin;
        WordTable.currentEditorWordRow = wordRow;
    }

    /**
     * 編集状態を初期化する(全てnull)にするメソッド.
     */
    protected resetCurrentEditorState(){
       this.setCurrentEditorState(null, null, null);
    }

    /**
     * 編集するためのinput要素を作成して返すメソッド.  
     * 引数で受け取ったdiv要素のclass属性を全て継承したinput要素を作成する.  
     * @param div 編集するdiv要素
     * @returns 編集するためのinput要素
     */
    protected createEditInputElem(div: HTMLDivElement){
        const input = Object.assign(document.createElement("input"), {
            type: (div.classList.contains(WordRow.numberClassName)) ? "number": "text",
            value: div.textContent,
        })
        input.classList.add(...div.classList);
        input.addEventListener("keydown", (e) => {
            switch (e.key){
                case "Enter":
                    this.commitEdit();
                    break;
                case "Escape":
                    this.cancelEdit();
                    break;
            }
        });
        input.addEventListener("blur", () => {this.commitEdit()});
        return input
    }

    /**
     * 編集内容を参照し, サーバーのデータベースを更新してWordRowの値も更新するメソッド.  
     * 入力内容が空欄の場合はもとに戻す. ( `cancelEdit()` を実行する)
     */
    protected async commitEdit(){
        if (!WordTable.currentEditorInput) return;
        const inputValue = WordTable.currentEditorInput.value.trim();
        if (inputValue == "") return this.cancelEdit();

        const row = WordTable.currentEditorWordRow as WordRow;
        const input = WordTable.currentEditorInput as HTMLInputElement;
        if (input.classList.contains(WordRow.numberClassName)){
            row.number = Number(inputValue);
        } else if (input.classList.contains(WordRow.termClassName)){
            row.term = inputValue;
        } else if (input.classList.contains(WordRow.meaningClassName)){
            row.meaning = inputValue;
        } else {
            throw new Error("該当のエレメントがありません.");
        }
        
        const body = JSON.stringify({
            "id": row.id,
            "number": row.number,
            "term": row.term,
            "meaning": row.meaning,
        });
        const data = await runPostMethod(appUrls["vocab:update"]!, body, "update failed");

        row.editor = data.editor;
        this.cancelEdit();
    }

    /**
     * 編集内容を無効にして, 編集状態を初期化するメソッド.
     * @returns void
     */
    protected cancelEdit(){
        if (!WordTable.currentEditorInput) return;
        WordTable.currentEditorInput.replaceWith(WordTable.originalEditorDiv!);
        this.resetCurrentEditorState();
    }

    /**
     * ダブルクリック時のイベントリスナー関数.  
     * ダブルクリックされたのが編集可能div要素なら, それのdivを編集用のinput要素に置き換える.  
     * 置き換えたinput要素には, 入力によって単語情報を更新するなどのイベントリスナーが付与されている.  
     * @param event イベント
     * @returns void
     */
    onEditableElemDBClick(event: MouseEvent){
        // 既に編集状態ならスキップ
        if (WordTable.currentEditorInput) return;

        const target = event.target;

        // HTMLDivElementでない可能性を排除
        if (!(target instanceof HTMLDivElement)) return;

        // 編集可能Div要素でない可能性を排除
        if (!(target.classList.contains(WordRow.editableDivClassName))) return;

        const wordRowDiv = target.closest("." + WordRow.selectableElementClassName) as HTMLDivElement | null;
        if (!wordRowDiv) throw new Error("WordRow div was not found: on dbclick event.");
        const wordRow = this.getWordRowById(Number(wordRowDiv.dataset.id));

        if (!wordRow) throw new Error(`wordRow wasn't fount. id: ${wordRowDiv.dataset.id}, wordRow:${wordRow}`);

        const input = this.createEditInputElem(target);
        this.setCurrentEditorState(input, target, wordRow);
        target.replaceWith(input);
        input.focus();
        input.select();
    }

    /**
     * 単語テーブルにある引数で受け取ったIDを持つ単語行を返すメソッド.  
     * 指定のIDの単語がない場合, `undefined` を返す.
     * @param id 単語のID
     * @returns 単語行
     */
    getWordRowById(id: number){
        return this._words.find(w => w.id === id);
    }

    get words(): ReadonlyArray<WordRow>{
        return this._words;
    }

    /**
     * 選択状態の `WordRow` オブジェクトの配列を返す.  
     * 返された配列は読み取り専用.
     */
    get selectedWords(): ReadonlyArray<WordRow>{
        return this._words.filter(wr => wr.isSelected);
    }

    static get instance(){
        if (!WordTable._instance) WordTable._instance = new WordTable();
        return WordTable._instance;
    }
}