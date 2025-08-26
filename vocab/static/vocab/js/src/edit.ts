
import { appUrls } from "./utils.js";
import { runPostMethod } from "@shared/server-connect-helper.js";
import {WordRow, WordTable} from "./word.js";
import {WordlistSelector} from "./wordlist.js"
import {SelectedModalTable} from "./modal.js";
import {Modal} from "bootstrap";


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
    let start = startRangeElement.valueAsNumber;
    if (Number.isNaN(start)) start = 0;
    let end = endRangeElement.valueAsNumber;
    if (Number.isNaN(end)) end = Infinity;
    wordTable.setVisibleByNumber(start, end);
}

startRangeElement.addEventListener("change", onRangedByNumber);
endRangeElement.addEventListener("change", onRangedByNumber);

// 全選択チェックボックス機能
export const onAllWordCheckbox = () => {
    const checkbox = document.getElementById("all-word-checkbox") as HTMLInputElement;
    wordTable.words.forEach(w => {w.isSelected = checkbox.checked});
}

// 単語帳追加機能
export const createNewWordlist = async () => {
    const wordlistName = (document.getElementById("new-wordlist") as HTMLInputElement).value.trim();
    if (!wordlistName) {
        alert("単語帳の名前を入力してください");
        return;
    }
    const formData = new FormData();
    formData.append("name", wordlistName);

    const data = await runPostMethod(appUrls["wordbank:create"]!, formData);
    location.href = "?target_word_list=" + data.name;
}

// 単語帳削除機能
export const deleteWordlist = async () => {
    const userInputWordlistName = (document.getElementById("delete-target-wordlist-input") as HTMLInputElement).value.trim();
    const currentWordlist = wordlistSelector.currentWordlist;
    if (userInputWordlistName != currentWordlist.name){
        alert("入力された単語帳名が正しくありません.");
        return;
    }

    const data = await runPostMethod(
        appUrls["wordbank:delete"]!,
        JSON.stringify({"id": currentWordlist.id}),
        "delete wordlist failed"
    );
    alert(`「${currentWordlist.name}」を削除しました.`);
    location.href = appUrls["vocab:editor"]!;
}


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

export async function registerWord(){

    const formData = new FormData();
    formData.append("number", addedNumberElem.value.trim())
    formData.append("term", addedTermElem.value.trim())
    formData.append("meaning", addedMeaningElem.value.trim())
    formData.append("wordlist", String(wordlistSelector.currentWordlist.id));

    const data = await runPostMethod(appUrls["vocab:register"]!, formData, "register failed");
    const newWordRow = new WordRow(
        data.id,
        data.number,
        data.term,
        data.meaning,
        data.editor,
    );
    wordTable.registerWordRow(newWordRow);
    setRegisterWordSuccessMessage(newWordRow.number, newWordRow.term);

    addedNumberElem.value = String(Number(addedNumberElem.value) + 1);
    addedTermElem.value = "";
    addedMeaningElem.value = "";
}


// 削除機能関連
const selectedModalTable = new SelectedModalTable(wordTable);

/**
 * 単語削除用のモーダルを表示する関数 
 */
export const showDeleteWordsModal = () => {
    selectedModalTable.drawTable();
    const elem = document.getElementById("delete-words-modal");
    if (!elem) throw new Error("モーダル要素が見つかりません.");
    (new Modal(elem).show());
}

/**
 * 選択された単語の削除を実行する関数.  
 * データベースから削除し, 単語テーブルから表示を削除する.  
 */
export const deleteWords = async () => {
    const ids: number[] = wordTable.selectedWords.map(wr => wr.id);
    const data = await runPostMethod(appUrls["vocab:delete"]!, JSON.stringify({"ids": ids}));
    wordTable.removeAllSelectedWord();
    alert("選択された単語を削除しました.");
}