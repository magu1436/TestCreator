
const wordRowClassNames = ["word-row", "d-flex", "flex-row", "flex-shrink-0"];
const wordRowChildrenClassNames = ["p-2", "border", "overflow-auto"];

const startRangeElement = document.getElementById("start-range");
const endRangeElement = document.getElementById("end-range");

const searchBoxElement = document.getElementById("search_box");

const wordTableContentElement = document.getElementById("word-table-content");


/**
 * 単語の表示・非表示を設定する関数.
 * @param {HTMLElement} element - 行要素(.word-row)
 * @param {boolean} visible - 表示するかどうか
 */
function setVisible(element, visible){
    element.classList.toggle("d-none", !visible);
    element.classList.toggle("d-flex", visible);
}

/**
 * 検索ボックスの値が含まれる単語のみを表示させる関数.  
 * 空白区切りでand検索が可能.  
 */
function searchWord(){
    const searchWords = searchBoxElement.value
        .trim()
        .split(/\s+/)
        .filter(Boolean)        // 空配列を削除
        .map(w => w.toLowerCase())
    const rows = document.getElementsByClassName("word-row");

    for (let row of rows) setVisible(row, true);

    for(let row of rows){
        for(let word of searchWords){
            const term = row.querySelector(".word-term").textContent.toLowerCase();
            const meaning = row.querySelector(".word-meaning").textContent.toLowerCase();
            if(!term.includes(word) && !meaning.includes(word)){
                setVisible(row, false);
                break;
            }
        }
    }
}

/**
 * 単語番号が指定されている場合に, その範囲内の番号の単語のみを表示する.  
 * startの入力がない場合は0, endの入力がない場合は正の無限大として処理を行う.
 * @returns {void}
 */
function applyRangedNumberFilter(){
    let startNum = startRangeElement.valueAsNumber;
    let endNum = endRangeElement.valueAsNumber;
    const rows = document.getElementsByClassName("word-row")

    if (Number.isNaN(startNum)) startNum = 0;
    if (Number.isNaN(endNum)) endNum = Infinity;

    if (startNum <= endNum){
        for(let row of rows){
            let wordNumber = Number(row.dataset.number);
            setVisible(row, (startNum <= wordNumber && wordNumber <= endNum));
        }
    }
}

startRangeElement.addEventListener("change", applyRangedNumberFilter);
endRangeElement.addEventListener("change", applyRangedNumberFilter);


/**
 * 単語帳テーブルの行のHTML要素を作成して返す関数.
 * 
 * @param {Number} id 
 * @param {String} number 単語番号
 * @param {String} term 単語
 * @param {String} meaning 意味
 * @param {String} editor 最終更新者
 * @returns {HTMLDivElement}
 */
function createWordRowElement(id, number, term, meaning, editor){
    let wordRow = document.createElement("div");
    wordRowClassNames.forEach(className => {
        wordRow.classList.add(className);
    });
    wordRow.dataset.id = id;
    wordRow.dataset.number = number;

    let wordNumber = Object.assign(document.createElement("div"), {
        className: "word-number",
        textContent: number,
    })

    let wordTerm = Object.assign(document.createElement("div"), {
        className: "word-term",
        textContent: term,
    })

    let wordMeaning = Object.assign(document.createElement("div"), {
        className: "word-meaning",
        textContent: meaning,
    })

    let wordEditedBy = Object.assign(document.createElement("div"), {
        className: "word-edited-by",
        textContent: editor,
    })

    let rowChildren = [wordNumber, wordTerm, wordMeaning, wordEditedBy];
    rowChildren.forEach(child => {
        wordRowChildrenClassNames.forEach(className => {
            child.classList.add(className);
        });
        wordRow.appendChild(child);
    });

    return wordRow
}

/**
 * 単語帳のテーブルに単語を追加して表示する関数.  
 * 追加する単語の番号を参照して, 昇順になるように挿入する.  
 * 追加後は単語番号フィルターと単語検索を実行して, フィルターがある場合に追加されても  
 * フィルターが機能するようにしている.  
 * @param {Number} id 単語のデータベース上のID
 * @param {String} number 単語番号
 * @param {String} term 単語
 * @param {String} meaning 意味
 * @param {String} editor 最終更新者
 */
function insertWordRow(id, number, term, meaning, editor){
    let wordRow = createWordRowElement(id, number, term, meaning, editor);
    let is_insert = false;
    for(let row of wordTableContentElement.getElementsByClassName("word-row")){
        console.log(Number(row.dataset.number))
        if(Number(number) < Number(row.dataset.number)){
            row.before(wordRow);
            is_insert = true;
            break;
        }
    }
    if(!is_insert) wordTableContentElement.appendChild(wordRow);

    applyRangedNumberFilter();
    searchWord();
}

/**
 * 単語追加モーダルから値を取得してテーブルに追加する関数.  
 * TODO: 取得した値をデータベースに登録し, IDと編集者を受け取ってそれらを登録する.
 */
function addWord(){
    const number = document.getElementById("added-word-number").value;
    const term = document.getElementById("added-word-term").value;
    const meaning = document.getElementById("added-word-meaning").value;
    insertWordRow(7, number, term, meaning, "test admin");
}