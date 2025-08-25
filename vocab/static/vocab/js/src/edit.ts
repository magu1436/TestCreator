
import { appUrls, getCSRFToken } from "./utils.js";
import {WordRow, WordTable} from "./word.js";
import {WordlistSelector} from "./wordlist.js"


const wordlistSelector = new WordlistSelector();
const wordTable = new WordTable();


const startRangeElementId = "start-range";
const endRangeElementId = "end-range";
const searchBoxElementId = "search_box";

const startRangeElement = document.getElementById(startRangeElementId) as HTMLInputElement;
const endRangeElement = document.getElementById(endRangeElementId) as HTMLInputElement;
const searchBoxElement = document.getElementById(searchBoxElementId) as HTMLInputElement;

([
    [startRangeElementId, startRangeElement],
    [endRangeElementId, endRangeElement],
    [searchBoxElementId, searchBoxElement],
]).forEach(s => {
    const id: string = s[0] as string;
    const elem = s[1];
    if (elem == null) throw new Error(`${id} element does not exist`);

})

/**
 * 検索ボックスの値が含まれる単語のみを表示させる関数.  
 * 空白区切りでand検索が可能.  
 * 検索ボックスが空の場合は全て表示する.    
 * 選択状態の単語行要素が検索対象外となったとき, 選択状態を解除する.
 */
const onSearch = () => {
    const searchWords = searchBoxElement?.value
        .trim()
        .split(/\s+/)
        .filter(Boolean)
        .map(w => w.toLowerCase()) ?? [];
    if (searchWords.length == 0){
        wordTable.words.forEach(wr => {wr.setVisible(true)});
        return;
    };
    wordTable.setVisibleByKeywords(...searchWords);
}

/**
 * 単語番号が指定されている場合に, その範囲内の番号の単語のみを表示する.  
 * startの入力がない場合は0, endの入力がない場合は正の無限大として処理を行う.  
 * 選択状態の単語行要素が範囲外となったとき, 選択状態を解除する.  
 */
const onRangedByNumber = () => {
    let start = Number(startRangeElement.value) ?? 0;
    let end = Number(endRangeElement.value) ?? Infinity;
    wordTable.setVisibleByNumber(start, end);
}

startRangeElement.addEventListener("change", onRangedByNumber);
endRangeElement.addEventListener("change", onRangedByNumber);


// 単語追加機能

const addedNumberElem = document.getElementById("added-word-number") as HTMLInputElement;
const addedTermElem = document.getElementById("added-word-term") as HTMLInputElement;
const addedMeaningElem = document.getElementById("added-word-meaning") as HTMLInputElement;

const registerSuccessMessageElem = document.getElementById("register-word-success-message");
/**
 * 単語登録が成功時のメッセージを更新する関数.
 * @param {number} number 単語番号
 * @param {string} term 単語
 */
function setRegisterWordSuccessMessage(number: number, term: string){
    registerSuccessMessageElem!.textContent = `"${number}: ${term}" を登録しました！`;
    setRegisterSuccessMessageVisible(true);
}

/**
 * 単語登録成功時に表示されるdiv要素の表示状態を変更する関数.
 * @param {boolean} 表示するかどうか.
 */
export function setRegisterSuccessMessageVisible(visible: boolean){
    registerSuccessMessageElem!.classList.toggle("d-none", !visible);
}

export function registerWord(){

    const formData = new FormData();
    formData.append("number", addedNumberElem.value.trim())
    formData.append("term", addedTermElem.value.trim())
    formData.append("meaning", addedMeaningElem.value.trim())
    formData.append("wordlist", String(wordlistSelector.currentWordlist.id));

    fetch(appUrls["vocab:register"]!, {
        method: "POST",
        headers: {"X-CSRFToken": getCSRFToken()},
        body: formData,
    })
    .then(async (res) => {
        const data = await res.json().catch(() => ({}));

        if (!res.ok || data.ok === false){
            const errs = data.error || data.errors;
            console.log(errs);
            setRegisterSuccessMessageVisible(false);
            alert(errs || "入力エラーが生じました.");
            throw new Error("validation_failed");
        }
        return data;
    })
    .then((res) => {
        const newWordRow = new WordRow(
            res.id,
            res.number,
            res.term,
            res.meaning,
            res.editor
        );
        wordTable.registerWordRow(newWordRow);
        setRegisterWordSuccessMessage(newWordRow.number, newWordRow.term);

        addedNumberElem.value = String(Number(addedNumberElem.value) + 1);
        addedTermElem.value = "";
        addedMeaningElem.value = "";
    })
    .catch((err) => {
        if (err.message !== "validation_failed"){
            console.error(err);
            alert("想定外のエラーが生じました. 管理者に報告してください.");
        }
    })
}