import {registerWord, setRegisterSuccessMessageVisible, showDeleteWordsModal, deleteWords, createNewWordlist} from "./edit.js";


// モーダル
document.getElementById("create-wordlist-submit")!.addEventListener(
    "click",
    createNewWordlist,
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