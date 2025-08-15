

// 検索機能

const startRangeElement = document.getElementById("start-range");
const endRangeElement = document.getElementById("end-range");

const searchBoxElement = document.getElementById("search_box");

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
                toggleWordRowSelected(row, false);
                break;
            }
        }
    }
}

/**
 * 単語番号が指定されている場合に, その範囲内の番号の単語のみを表示する.  
 * startの入力がない場合は0, endの入力がない場合は正の無限大として処理を行う.  
 * 選択状態の単語行要素が範囲外となったとき, 選択状態を解除する.  
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
            const wordNumber = Number(row.dataset.number);
            const isInRange = (startNum <= wordNumber && wordNumber <= endNum)
            setVisible(row, isInRange);
            if (!isInRange) toggleWordRowSelected(row, false);
        }
    }
}

startRangeElement.addEventListener("change", applyRangedNumberFilter);
endRangeElement.addEventListener("change", applyRangedNumberFilter);
