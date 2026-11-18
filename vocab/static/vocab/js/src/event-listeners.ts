import {registerWord, setRegisterSuccessMessageVisible, showDeleteWordsModal, deleteWords, createNewWordlist, deleteWordlist, onAllWordCheckbox, onSearch} from "./edit.js";
import { onEnterKey } from "./search.js";

// キーワード検索
document.getElementById("search-button")!.addEventListener("click", onSearch);
document.getElementById("search_box")!.addEventListener("keydown", onEnterKey(onSearch));

// 全選択チェックボックス
document.getElementById("all-word-checkbox")!.addEventListener(
    "click",
    onAllWordCheckbox
)


// モーダル
document.getElementById("create-wordlist-submit")!.addEventListener(
    "click",
    createNewWordlist,
)

document.getElementById("delete-wordlist-submit")!.addEventListener(
    "click",
    deleteWordlist
)

document.getElementById("registerModalClose")!.addEventListener(
    "click", 
    () => {setRegisterSuccessMessageVisible(false)}
)
document.getElementById("registerModalSubmit")!.addEventListener(
    "click",
    registerWord
)

document.getElementById("show-delete-modal-btn")!.addEventListener(
    "click",
    showDeleteWordsModal,
)
document.getElementById("delete-confirm-modal-submit")!.addEventListener(
    "click",
    deleteWords,
)
