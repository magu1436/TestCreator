import { WordlistSelector, Wordlist } from "@vocab/wordlist.js";
import { runPostMethod } from "@shared/server-connect-helper.js";
import { appUrls } from "./utils.js";
import { RangeBox, NumberRangeConfigure } from "./configures.js"


export const wordlistSelector = new WordlistSelector()

/**
 * 単語帳に最小の番号と最大の番号をセットする
 */
const setWordlistData = async () => {
    for (const wl of wordlistSelector.wordlists){
        const data = await runPostMethod(appUrls["wordbank:read"]!, JSON.stringify({id: wl.id}));
        const nums = data.words.map((w: {"number": number}) => w.number);
        wl.element.dataset.min = String(Math.min(...nums));
        wl.element.dataset.max = String(Math.max(...nums));
        setInitRange(wordlistSelector.currentWordlist);
    }
}

/**
 * 一番上にある番号指定範囲に単語帳に登録された単語のうち, 最小の単語番号と最大の単語番号を入れる
 * @param wordlist 選択中の単語帳
 */
const setInitRange = (wordlist: Wordlist) => {
    const ob = RangeBox.originalRangeBox;
    const minNum = Number(wordlist.element.dataset.min);
    const maxNum = Number(wordlist.element.dataset.max);
    RangeBox.wordlistMinNumber = minNum;
    RangeBox.wordlistMaxNumber = maxNum;
    ob.start = minNum;
    ob.end = maxNum;
}

wordlistSelector.selectorElement.addEventListener("change", async () => {
    NumberRangeConfigure.insatance.initRangeConfigure();
    setInitRange(wordlistSelector.currentWordlist);
})

wordlistSelector.ready.then(() => setWordlistData());