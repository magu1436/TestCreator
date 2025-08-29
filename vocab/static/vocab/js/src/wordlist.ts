import { appUrls } from "./utils.js"
import { runGetMethod } from "@shared/server-connect-helper.js"


export class Wordlist {
    static readonly currentWordlistId = "current-wordlist"

    readonly element: HTMLOptionElement;
    private _id: number;
    private _name: string;

    constructor(id: number, name: string, isCurrentWordlist: boolean = false){
        this._id = id;
        this._name = name;
        this.element = this.createWordlistOptionElement(id, name, isCurrentWordlist);
    }

    protected createWordlistOptionElement(id: number, name: string, selected: boolean): HTMLOptionElement{
        return Object.assign(document.createElement("option"), {
            value: name,
            textContent: name,
            selected: selected,
        });
    }

    get id(){
        return this._id;
    }

    get name(){
        return this._name;
    }
    set name(name: string){
        this._name = name;
        this.element.textContent = this._name;
    }

    get isCurrentWordlist(){
        return this.element.selected;
    }

    set isCurrentWordlist(isCurrentWordlist: boolean){
        this.element.selected = isCurrentWordlist;
    }
}

export class WordlistSelector{
    static readonly selectorId = "wordlist-selector";

    readonly selectorElement: HTMLSelectElement;
    readonly wordlists: Wordlist[] = [];

    constructor(){
        const elem = document.getElementById(WordlistSelector.selectorId) as HTMLSelectElement | null;
        if (elem == null){
            throw new Error(`${WordlistSelector.selectorId} object does not exist.`);
        } else {
            this.selectorElement = elem;
        }
        const currentWordlistId = Number(this.selectorElement.dataset.id);
        fetch(appUrls["wordbank:all_wordlist"]!, {
            method: "GET",
        })
        .then(async (response) => {
            const resData = await response.json().catch(() => ({}));
            if (!response.ok){
                const err = resData.error || resData.err;
                alert(err || "何らかのエラーが発生しました");
                throw new Error("read_failed");
            }
            return resData;
        })
        .then((response) => {
            for (let wlData of response.wordlists){
                const isCurrentWordlist = (wlData.id == currentWordlistId);
                const wl = new Wordlist(wlData.id, wlData.name, isCurrentWordlist);
                if (isCurrentWordlist){
                    this.pushWordlist(wl, 0);
                } else {
                    this.pushWordlist(wl);
                }
            }
        });
    }

    pushWordlist(wordlist: Wordlist, idx: number | null = null){
        if (idx == null || (this.wordlists.length == 0 && idx == 0)){
            this.selectorElement.appendChild(wordlist.element);
            this.wordlists.push(wordlist);
        } else {
            const afterWordlist = this.wordlists[idx];
            if (afterWordlist == null) {
                throw new Error(`out of index: ${idx}`);
            }
            afterWordlist.element.before(wordlist.element);
            this.wordlists.splice(idx, 0, wordlist);
        }
    }

    get currentWordlist(): Wordlist{
        const currentWordlists = this.wordlists.filter((wl) => {return wl.isCurrentWordlist});
        if (currentWordlists.length == 0) throw new Error("Current wordlist does not recognized.");
        if (currentWordlists.length != 1) throw new Error("Current wordlist are recognized more than 1.");
        return currentWordlists[0] as Wordlist;
    }
}


const newWordlistInputId = "new-wordlist"
const newWordlistInput = document.getElementById(newWordlistInputId) as HTMLInputElement;