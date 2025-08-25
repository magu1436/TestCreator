import Cookies from 'js-cookie'

function readJsonFromScript<T>(id: string): T {
  const el = document.getElementById(id) as HTMLScriptElement | null;
  if (!el?.textContent) throw new Error(`script#${id} not found`);
  return JSON.parse(el.textContent) as T;
}

export const appUrls = readJsonFromScript<Record<string, string>>("app-urls")

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
  errMesssage?: string) => {
    if (!url) throw new Error(`url is incorrect: ${url}`);
    const response = await fetch(url, {
      method: method,
      headers: {"X-CSRFToken": getCSRFToken()},
      body: body,
    }).catch((err) => {
      console.log(err);
      alert("想定外のエラーが生じました. 開発者に連絡してください. \n" + err);
    });

    if (response == null){
      return;
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok){
      const err = data.err || data.errs;
      alert(err || errMesssage || "何らかサーバーエラーが生じました.");
      throw new Error(errMesssage || "sever proccess error");
    }

    return data;
  }

export const runPostMethod = async (url: string, body: FormData | string, errMessage?: string): Promise<Record<string, any>> => {
  return connectServer(url, "POST", body, errMessage) as Record<string, any>;
}

export const runGetMethod = async (url: string, errMessage?: string): Promise<Record<string, any>> => {
  return connectServer(url, "GET", errMessage);
}