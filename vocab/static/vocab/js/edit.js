
const startRangeElement = document.getElementById("start-range")
const endRangeElement = document.getElementById("end-range")


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
            setVisible(row, (startNum <= wordNumber && wordNumber <= endNum))
        }
    }
}

startRangeElement.addEventListener("change", applyRangedNumberFilter);
endRangeElement.addEventListener("change", applyRangedNumberFilter);