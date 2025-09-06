

export class RangeBox {
    
    static readonly originalElemClassName = "range-box";
    static readonly originalLeftBoxClassName = "range-box-left";
    static readonly originalRightBoxClassName = "range-box-right";

    protected static _originalRangeBoxDiv: HTMLDivElement | null;
    protected static _originalRangeBox: RangeBox | null;

    static wordlistMinNumber: number;
    static wordlistMaxNumber: number;

    readonly elem: HTMLDivElement;
    readonly startBoxElem: HTMLInputElement;
    readonly endBoxElem: HTMLInputElement;
    protected _start?: number;
    protected _end?: number;

    constructor(){
        if (!RangeBox._originalRangeBoxDiv){
            RangeBox._originalRangeBoxDiv = document.getElementsByClassName(RangeBox.originalElemClassName)![0] as HTMLDivElement;
            if (!RangeBox) throw new Error(`${RangeBox.originalElemClassName} element have not been found.`);
            this.elem = RangeBox._originalRangeBoxDiv;
            RangeBox._originalRangeBox = this;
        } else {
            this.elem = RangeBox._originalRangeBoxDiv.cloneNode(true) as HTMLDivElement;
        }
        this.startBoxElem = this.elem.getElementsByClassName(RangeBox.originalLeftBoxClassName)![0] as HTMLInputElement;
        this.startBoxElem.addEventListener("change", () => {this.onStartBoxChange()});
        this.startBoxElem.value = "";
        this.endBoxElem = this.elem.getElementsByClassName(RangeBox.originalRightBoxClassName)![0] as HTMLInputElement;
        this.endBoxElem.addEventListener("change", () => {this.onEndBoxChange()});
        this.endBoxElem.value = "";
    }

    /**
     * スタートの入力ボックスの変更があった場合に実行される関数.  
     * スタートの入力ボックスの値を取得して自身のスタートの値として扱う.  
     * 入力ボックスの値が空欄などの数値にできない値の場合, 代わりに0として扱われる.  
     */
    protected onStartBoxChange(){
        let num = Number(this.startBoxElem.value);
        if (Number.isNaN(num)) num = 0;
        this._start = num;
    }

    /**
     * エンドの入力ボックスの変更があった場合に実行される関数.  
     * エンドの入力ボックスの値を取得して自身のエンドの値として扱う.  
     * 入力ボックスの値が空欄などの数値にできない値の場合, 代わりに正の無限大として扱われる.  
     */
    protected onEndBoxChange(){
        let num = Number(this.endBoxElem.value);
        if (Number.isNaN(num)) num = Infinity;
        this._end = num;
    }

    get start(){
        return Number(this._start);
    }

    set start(s: number){
        this.startBoxElem.value = String(s);
        this._start = s;
    }

    get end(){
        return Number(this._end);
    }

    set end(e: number){
        this.endBoxElem.value = String(e);
        this._end = e;
    }

    static get originalRangeBox(){
        if (!RangeBox._originalRangeBox) throw new Error("OriginalRangeBox does not exist");
        return RangeBox._originalRangeBox;
    }

    /**
     * 保持している `start` と `end` の関係性が正しいかどうか判別するメソッド.  
     * `start` <= `end` の場合に `true` を返す.  
     * @returns 正しい範囲を保持しているかどうか
     */
    isCorrectRange(){
        if (Number.isNaN(this.start) || Number.isNaN(this.end)) return false;
        return this.start <= this.end;
    }

    /**
     * 自身が保持している開始番号と終了番号が正しい値であるか判定するメソッド.  
     * 正しい値: 数値  
     * 不正な値: NaN, undefined, ...  
     * @returns 正しい値を保持しているかどうか
     */
    hasCorrectValues(){
        if (!Number.isNaN(this.start) && !Number.isNaN(this.end) && this._start && this._end) return true;
        return false;
    }
}


/**
 * 単語番号指定の設定を保持するクラス.  
 * シングルトン.  
 */
export class NumberRangeConfigure {

    static readonly rangeBoxesId = "range-boxes";
    static readonly addRangeButtonId = "add-range-btn";

    protected static _instance?: NumberRangeConfigure;

    protected _boxes: RangeBox[];
    protected rangeBoxesElem: HTMLDivElement;
    protected addRangeButtonElem: HTMLButtonElement;

    constructor(){
        if (NumberRangeConfigure._instance) throw new Error("numberRangeConfigure is singleton.");
        this._boxes = [new RangeBox()];
        this.rangeBoxesElem = document.getElementById(NumberRangeConfigure.rangeBoxesId) as HTMLDivElement;
        this.addRangeButtonElem = document.getElementById(NumberRangeConfigure.addRangeButtonId) as HTMLButtonElement;
        this.addRangeButtonElem.addEventListener("click", () => {this.addRangeBox()});
    }

    /**
     * 単語番号指定ボックスを追加するメソッド.
     */
    protected addRangeBox(){
        const newBox = new RangeBox();
        this._boxes = [...this._boxes, newBox];
        this.rangeBoxesElem.appendChild(newBox.elem);
    }

    /**
     * 指定された複数の範囲を取得するためのメソッド.  
     * 数値を入力するinput要素に不正な値(空欄など)が入力されている場合は, その範囲を飛ばした  
     * 範囲のリストを返す.  
     * input要素に適切な値が入力されているにも関わらず指定が間違っている場合には, アラートを  
     * 表示してエラーを投げる.  
     * @returns 範囲を示す連想配列のリスト
     */
    getRanges(){
        const ranges = [];
        for (const box of this._boxes){
            if (!box.hasCorrectValues()){
                continue;
            }
            if (!box.isCorrectRange()){
                alert("不適切な単語番号指定があります.");
                throw new Error("incorrect range error");
            }
            ranges.push({"start": box.start, "end": box.end});
        }
        return ranges;
    }

    initRangeConfigure(){
        this._boxes.slice(1).forEach(rb => {this.rangeBoxesElem.removeChild(rb.elem);});
        this._boxes = [RangeBox.originalRangeBox]
    }

    static get insatance(){
        if (!NumberRangeConfigure._instance) NumberRangeConfigure._instance = new NumberRangeConfigure;
        return NumberRangeConfigure._instance;
    }

    get boxes(): ReadonlyArray<RangeBox>{
        return this._boxes;
    }
}


/**
 * 入力された問題数を取得して返す関数.  
 * 入力内容が不正な値(0未満など)だった場合にはエラーを投げる.  
 * @returns 問題数
 */
export const getNumQuestions = () => {
    const inp = document.getElementById("num-questions-input") as HTMLInputElement;
    const num = Number(inp.value);
    if (Number.isNaN(num) || num <= 0) throw new Error("Incorrect number of questions is input");
    return num
}


export class RadioConfigure {

    readonly referenceRadioButtonName: string;
    protected buttons: HTMLInputElement[] = [];

    constructor(name: string){
        this.referenceRadioButtonName = name;
        const buttons = document.getElementsByName(name) as NodeListOf<HTMLInputElement>;
        if (buttons.length === 0) throw new Error(`no buttons have the name: ${name}`);
        buttons.forEach((b) => this.buttons.push(b));
    }

    getCheckedButton(){
        const checked = this.buttons.find(b => b.checked);
        if (!checked) throw new Error("Checked Radio Button do not exist.");
        return checked;
    }
}