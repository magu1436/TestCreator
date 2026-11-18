import type { WordTable } from "./word.js";

/** 空白区切りのキーワードで絞り込み、空欄の場合は全単語を表示する。 */
export const searchWordTable = (wordTable: WordTable, query: string): void => {
    const keywords = query.trim().split(/\s+/).filter(Boolean);
    wordTable.setVisibleByKeywords(...keywords);
};
