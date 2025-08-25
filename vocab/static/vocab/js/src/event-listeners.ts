import {registerWord, setRegisterSuccessMessageVisible, showDeleteWordsModal, deleteWords} from "./edit.js";


// モーダル
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