
const appUrlsElementId = "app-urls";
const appUrlsElem = document.getElementById(appUrlsElementId) as HTMLScriptElement;
if (!appUrlsElem) throw new Error(`script${appUrlsElementId} not found`);
const appUrls = JSON.parse(appUrlsElem.textContent) as Record<string, string>;

/**
 * ビューのURLを取得するメソッド.  
 * `base.html` のスクリプトに記載された連想配列の値を参照して, 対応するURLを文字列として返す.  
 * 連想配列にないビューの名前が指定された場合はエラーを投げる.  
 * @param appName ビューの名前
 * @returns ビューのURL
 */
export const getUrl = (appName: string) => {
    const url = appUrls[appName];
    if (!url) throw new Error(`${appName} is not registered. Add ${appName} in 'base.html'.`);
    return url;
}