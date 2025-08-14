/**
 * `d-flex` 属性を持つ指定の要素の表示・非表示を設定する関数.
 * @param {HTMLElement} element - 行要素(.word-row)
 * @param {boolean} visible - 表示するかどうか
 */
function setVisible(element, visible){
    element.classList.toggle("d-none", !visible);
    element.classList.toggle("d-flex", visible);
}

/**
 * CSRFトークンを作成して返す関数.
 * @returns CSRFトークン文字列
 */
function getCSRFToken(){
    return Cookies.get("csrftoken");
}