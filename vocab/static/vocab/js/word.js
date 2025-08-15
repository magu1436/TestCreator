const wordRowClassNames = ["word-row", "d-flex", "flex-row", "flex-shrink-0"];
const wordRowChildrenClassNames = ["p-2", "border", "overflow-auto"];

const wordTableContentElement = document.getElementById("word-table-content");


/**
 * 単語帳テーブルの行のHTML要素を作成して返す関数.
 * 
 * @param {Number} id 
 * @param {String} number 単語番号
 * @param {String} term 単語
 * @param {String} meaning 意味
 * @param {String} editor 最終更新者
 * @returns {HTMLDivElement} 単語テーブルの行要素
 */
function createWordRowElement(id, number, term, meaning, editor){
    let wordRow = document.createElement("div");
    wordRowClassNames.forEach(className => {
        wordRow.classList.add(className);
    });
    wordRow.dataset.id = id;
    wordRow.dataset.number = number;

    let wordCheckboxDiv = Object.assign(document.createElement("div"), {
        className: "word-checkbox-div"
    })
    let wordCheckbox = Object.assign(document.createElement("input"), {
        type: "checkbox",
        className: "word-checkbox",
    });
    wordCheckbox.dataset.id = id;
    wordCheckbox.addEventListener("change", function(){
        let wr = getWordRowFromId(this.dataset.id);
        toggleWordRowSelected(wr, this.checked);
    })
    wordCheckboxDiv.appendChild(wordCheckbox);

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

    let rowChildren = [wordCheckboxDiv, wordNumber, wordTerm, wordMeaning, wordEditedBy];
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
 * デフォルトでは, 追加後は単語番号フィルターと単語検索を実行して, フィルターがある場合  
 * に追加されてもフィルターが機能するようにしている.  
 * @param {Number} id 単語のデータベース上のID
 * @param {String} number 単語番号
 * @param {String} term 単語
 * @param {String} meaning 意味
 * @param {String} editor 最終更新者
 * @param {boolean} apply_search 挿入後に単語検索を行うかどうか
 */
function insertWordRow(id, number, term, meaning, editor, apply_search = true){
    let wordRow = createWordRowElement(id, number, term, meaning, editor);
    let was_inserted = false;
    for(let row of wordTableContentElement.getElementsByClassName("word-row")){
        if(Number(number) < Number(row.dataset.number)){
            row.before(wordRow);
            was_inserted = true;
            break;
        }
    }
    if(!was_inserted) wordTableContentElement.appendChild(wordRow);

    if(apply_search){
        applyRangedNumberFilter();
        searchWord();
    }
}

function getWordRowFromId(id){
    let id_str = String(id)
    for(let row of document.getElementsByClassName("word-row")){
        if(id_str == row.dataset.id) return row;
    }
    return null;
}


// 単語テーブルに単語を追加する初期化処理
data.words.forEach(word => {
    insertWordRow(
        word.id,
        String(word.number),
        word.term,
        word.meaning,
        word.latest_edited_by,
        false
    );
})


// 単語追加機能

const addedNumberElem = document.getElementById("added-word-number");
const addedTermElem = document.getElementById("added-word-term");
const addedMeaningElem = document.getElementById("added-word-meaning");

const registerSuccessMessageElem = document.getElementById("register-word-success-message");

/**
 * 単語登録が成功時のメッセージを更新する関数.
 * @param {String} number 単語番号
 * @param {String} term 単語
 */
function setRegisterWordSuccessMessage(number, term){
    registerSuccessMessageElem.textContent = `"${number}: ${term}" を登録しました！`
}

/**
 * 単語登録成功時に表示されるdiv要素を隠す関数.
 */
function hideRegisterWordSuccessMessage(){
    setVisible(registerSuccessMessageElem, false);
}

/**
 * 単語追加モーダルから値を取得してデータベースに登録し, テーブルに追加する関数.  
 */
function registerWord(){
    const wordlistId = document.getElementById("current-wordlist").dataset.id;

    const formData = new FormData();
    formData.append("number", addedNumberElem.value.trim())
    formData.append("term", addedTermElem.value.trim())
    formData.append("meaning", addedMeaningElem.value.trim())
    formData.append("wordlist", wordlistId)

    fetch(appUrls["vocab:register"], {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken(),
        },
        body: formData
    })
        .then(async (response) => {
            // JSONでない応答でも落ちないようにする
            const data = await response.json().catch(() => ({}));

            // HTTPとして失敗 or サーバー側で {ok: false}
            if (!response.ok || data.ok === false){
                const errs = data.error || data.errors;
                const messages = [];
                for (const [field, msgs] of Object.entries(errs || {})){
                    messages.push(`${field}: ${[].concat(msgs).join("")}`);
                }
                hideRegisterWordSuccessMessage();
                alert(messages.join("\n") || "入力エラーが生じました.");
                throw new Error("validation_failed");
            }
            return data
        })
        .then((response) => {
            const number = addedNumberElem.value.trim();
            const term = addedTermElem.value.trim();
            const meaning = addedMeaningElem.value.trim();
            insertWordRow(
                response.id,
                number,
                term,
                meaning,
                response.editor
            );

            setRegisterWordSuccessMessage(number, term);
            setVisible(registerSuccessMessageElem, true);

            addedTermElem.value = "";
            addedMeaningElem.value = "";
        })
        .catch((err) => {
            if (err.message !== "validation_failed"){
                console.error(err);
                alert("通信エラーが発生しました!");
            }
        })
}


// 単語削除機能関連

document.getElementById("all-word-checkbox").addEventListener("change", function(){
    for(let checkbox of document.getElementsByClassName("word-checkbox")){
        checkbox.checked = this.checked;
        checkbox.dispatchEvent(new Event("change"));
    }
})

/**
 * 単語行要素の選択状態を変更する関数.
 * @param {HTMLDivElement} wordRow 単語テーブルの行要素
 * @param {boolean} isSelected 選択状態かどうか
 */
function toggleWordRowSelected(wordRow, isSelected){
    wordRow.classList.toggle("selected-word-row", isSelected);
}