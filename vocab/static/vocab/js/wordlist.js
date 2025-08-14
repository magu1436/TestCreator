
const wordlistSelector = document.getElementById("wordlist-selector");

/**
 * 単語帳を選択する際に表示するドロップダウンの要素を作成して返す関数.
 * @param {Number} id 単語帳のID
 * @param {String} name 単語帳の名前
 * @param {boolean} isCurrentWordlist 現在表示されている単語帳かどうか
 * @returns Select要素に追加する単語帳の情報を含むOption要素
 */
function createWordlistOption(id, name, isCurrentWordlist = false){
    const optionElem = Object.assign(document.createElement("option"), {
        value: name,
        textContent: name,
    });
    optionElem.dataset.id = id;

    if(isCurrentWordlist) optionElem.id = "current-wordlist";
    
    return optionElem;
}

/**
 * 単語帳選択のドロップダウンに単語帳の行を追加する関数.
 * @param {Number} id 単語帳のID
 * @param {String} name 単語帳の名前
 * @param {boolean} isCurrentWordlist 現在表示されている単語帳かどうか
 */
function appendWordlistToSelector(id, name, isCurrentWordlist = false){
    wordlistSelector.appendChild(createWordlistOption(id, name, isCurrentWordlist));
}


// 単語帳選択ドロップダウンを作成する初期化処理
if(data.target_wordlist === null){
    appendWordlistToSelector(-1, "null", true);
}else{
    appendWordlistToSelector(data.target_wordlist.id, data.target_wordlist.name, true);
}
for(let wordlist of data.wordlists){
    appendWordlistToSelector(wordlist.id, wordlist.name);
}


// 単語帳作成機能

/**
 * 入力された単語名の単語帳を作成して, 作成した単語帳の編集画面へ遷移する関数.
 * @param {ButtonElement} button 押下されたボタンの要素
 */
function createNewWordlist(){
    const wordlistName = document.getElementById("new-wordlist").value.trim();

    const formData = new FormData();
    formData.append("name", wordlistName);

    fetch(appUrls["wordbank:create"], {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken(),
        },
        body: formData,
    })
        .then(async (response) => {
            const data = await response.json().catch(() => ({}));

            if (!response.ok || data.ok === false){
                const errs = data.errs || data.errors;
                const messages = [];
                for (const [field, msgs] of Object.entries(errs || {})){
                    messages.push(`${field}: ${[].concat(msgs).join("")}`);
                }
                alert(messages.join("\n")) || "入力エラーが生じました";
                throw new Error("validation_failed");
            }
            return data;
        })
        .then((response) => {
            location.href = "?target_word_list=" + response.name;
        })
        .catch((err) => {
            if (err.messages !== "validation_failed"){
                console.log(err);
                alert("通信エラーが発生しました！");
            }
        })
}


// 単語帳削除機能
function deleteWordlist(){

    const targetWordlistName = document.getElementById("delete-target-wordlist").textContent.trim();
    const userInputWordlistName = document.getElementById("delete-target-wordlist-input").value.trim();

    if (targetWordlistName != userInputWordlistName){
        alert("入力された単語帳名が異なります。");
        return;
    }

    fetch(appUrls["wordbank:delete"], {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({"id": data.target_wordlist.id})
    })
    .then(async (response) => {
        const resData = await response.json().catch(() => ({}));

        if (!response.ok || resData.ok === false){
            const err = resData.error || resData.err;
            alert(err || "何らかのエラーが発生しました.");
            throw new Error("delete_failed");
        }
        return resData;
    })
    .then((response) => {
        alert(`「${data.target_wordlist.name}」を削除しました。`)
        location.href = appUrls["vocab:editor"];
    })
    .catch((err) => {
        if (err.messages !== "delete_failed"){
            console.log(err);
            alert("通信エラーが発生しました！");
        }
    })
}