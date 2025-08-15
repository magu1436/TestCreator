/**
 * CSRFトークンを作成して返す関数.
 * @returns CSRFトークン文字列
 */
function getCSRFToken(){
    return Cookies.get("csrftoken");
}