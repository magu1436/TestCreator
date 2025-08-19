
import {WordTable} from "./word.js";
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