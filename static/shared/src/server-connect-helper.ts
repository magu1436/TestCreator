import Cookies from 'js-cookie'

export function getCSRFToken(): string{
    const token = Cookies.get("csrftoken")
    if (token){
      return token;
    } else {
      throw new Error("CSRFToken wasn't given.")
    }
}

export const connectServer = async (
  url: string,
  method: "POST" | "GET",
  body: FormData | string | null = null,
  errMessage?: string) => {
    if (!url) throw new Error(`url is incorrect: ${url}`);
    let response: void | Response;
    if (method == "POST"){
      response = await fetch(url, {
        method: method,
        headers: {"X-CSRFToken": getCSRFToken()},
        body: body,
      }).catch((err) => {
        console.log(err);
        alert("想定外のエラーが生じました. 開発者に連絡してください. \n" + err);
      });
    } else {
      response = await fetch(url, {
        method: method,
        headers: {"X-CSRFToken": getCSRFToken()},
      }).catch((err) => {
        console.log(err);
        alert("想定外のエラーが生じました. 開発者に連絡してください. \n" + err);
      });
    }

    if (response == null){
      return;
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok){
      const err = data.err || data.errs;
      alert(err || errMessage || "何らかサーバーエラーが生じました.");
      throw new Error(errMessage || "sever proccess error");
    }

    return data;
  }

export const runPostMethod = async (url: string, body: FormData | string, errMessage?: string): Promise<Record<string, any>> => {
  return connectServer(url, "POST", body, errMessage) as Record<string, any>;
}

export const runGetMethod = async (url: string, errMessage?: string): Promise<Record<string, any>> => {
  return connectServer(url, "GET", errMessage);
}