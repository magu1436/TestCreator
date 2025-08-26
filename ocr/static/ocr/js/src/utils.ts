import Cookies from 'js-cookie'

function readJsonFromScript<T>(id: string): T {
  const el = document.getElementById(id) as HTMLScriptElement | null;
  if (!el?.textContent) throw new Error(`script#${id} not found`);
  return JSON.parse(el.textContent) as T;
}

export const appUrls = readJsonFromScript<Record<string, string>>("app-urls")