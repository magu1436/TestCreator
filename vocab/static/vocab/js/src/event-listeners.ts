import {registerWord, setRegisterSuccessMessageVisible} from "./edit.js";


// モーダル
document.getElementById("registerModalClose")!.addEventListener(
    "click", 
    () => {setRegisterSuccessMessageVisible(false)}
)
document.getElementById("registerModalSubmit")!.addEventListener(
    "click",
    registerWord
)