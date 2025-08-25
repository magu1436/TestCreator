import {WordTable, WordRow} from "./word.js";


// 削除用モーダル関連
/**
 * 削除用モーダルに表示する選択された単語の一覧表を保持するクラス.  
 */
export class SelectedModalTable{
    static readonly tableElementId = "delete-words-table-body"
    readonly tableElem: HTMLElement;
    readonly referenceWordTable: WordTable;

    constructor(wordTable: WordTable){
        const tableElem = document.getElementById(SelectedModalTable.tableElementId);
        if (!tableElem) throw new Error(`${SelectedModalTable.tableElementId} element does not exist.`);
        this.tableElem = tableElem;
        this.referenceWordTable = wordTable;
    }

    /**
     * 表の要素を全て削除するメソッド.  
     */
    resetTable(){
        while(this.tableElem.firstChild){
            this.tableElem.removeChild(this.tableElem.firstChild);
        }
    }

    /**
     * 表の行を作成して返すメソッド.  
     * @param wordRow 単語行
     * @returns {HTMLTableRowElement} 表の行要素
     */
    protected createRow(wordRow: WordRow){
        const tr = document.createElement("tr");
        [
            Object.assign(document.createElement("th"), {
                scope: "row",
                textContent: wordRow.number,
            }),
            Object.assign(document.createElement("td"), {
                textContent: wordRow.term,
            }),
            Object.assign(document.createElement("td"), {
                textContent: wordRow.meaning,
            })
        ].forEach(v => tr.appendChild(v));
        return tr;
    }

    /**
     * テーブルを作成するメソッド.  
     * 最初にテーブルの行要素を全て削除し, 参照する単語テーブルから選択されている  
     * 単語を取得してテーブルを作成する.  
     */
    drawTable(){
        this.resetTable();
        this.referenceWordTable.selectedWords.forEach(wr => {
            this.tableElem.appendChild(this.createRow(wr));
        });
    }
}