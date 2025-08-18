import { getCSRFToken, appUrls } from "./utils.js"



class Wordlist extends HTMLOptionElement{

    static readonly currentWordlistId = "current-wordlist"

    private _wordlistId: number;
    private _name: string;
    private _isCurrentWordlist;

    constructor(id: number, name: string, isCurrentWordlist: boolean = false){
        super();
        this._wordlistId = id;
        this._name = name;
        this._isCurrentWordlist = isCurrentWordlist;
        this.value = this._name;
        this.textContent = this._name;
        if (this._isCurrentWordlist) this.id = Wordlist.currentWordlistId;
    }

    get wordlistId(){
        return this._wordlistId;
    }

    get name(){
        return this._name;
    }
    set name(name: string){
        this._name = name;
        this.textContent = this._name;
    }

    get isCurrentWordlist(){
        return this._isCurrentWordlist;
    }
}

export class WordlistSelector{
    static readonly selectorId = "wordlist-selector";

    readonly selectorElement: HTMLSelectElement;
    readonly wordlists: Wordlist[] = []

    constructor(){
        const elem = document.getElementById(WordlistSelector.selectorId) as HTMLSelectElement | null;
        if (elem == null){
            throw new Error(`${WordlistSelector.selectorId} object does not exist.`);
        } else {
            this.selectorElement = elem;
        }
        const currentWordlistId = Number(this.selectorElement.dataset.id);
        fetch(appUrls["wordbank:all_wordlist"]!, {
            method: "POST",
            headers: {"X-CSRFToken": getCSRFToken()},
        })
        .then(async (response) => {
            const resData = await response.json().catch(() => ({}));
            if (!resData.ok || resData.ok === false){
                const err = resData.error || resData.err;
                alert(err || "何らかのエラーが発生しました");
                throw new Error("read_failed");
            }
            return resData;
        })
        .then((response) => {
            for (let wl of response.wordlists){
                if (wl.id == currentWordlistId){
                    this.pushWordlist(wl, 0);
                } else {
                    this.pushWordlist(wl);
                }
            }
        });
    }

    pushWordlist(wordlist: Wordlist, idx: number | null = null){
        if (idx == null || (this.wordlists.length == 0 && idx == 0)){
            this.selectorElement.appendChild(wordlist);
            this.wordlists.push(wordlist);
        } else {
            const afterWordlist = this.wordlists[idx];
            if (afterWordlist == null) {
                throw new Error(`out of index: ${idx}`);
            }
            afterWordlist.before(wordlist);
            this.wordlists.splice(idx, 0, wordlist);
        }
    }

    getCurrentWordList(){
        return this.wordlists[0]
    }
}


const newWordlistInputId = "new-wordlist"
const newWordlistInput = document.getElementById(newWordlistInputId) as HTMLInputElement;