// 単語一覧の読込後、閲覧・編集の各画面でこのスクリプトを実行する。
// 検証用の単語はブラウザ内だけに追加し、終了時に元の表示・選択状態へ戻す。
(async () => {
    const { WordRow, WordTable } = await import('/static/vocab/js/dist/word.js');
    const table = WordTable.instance;
    const input = document.getElementById('search_box');
    const button = input.nextElementSibling;
    const startRange = document.getElementById('start-range');
    const endRange = document.getElementById('end-range');
    const originalRange = [startRange.value, endRange.value];
    const original = table.words.map(row => [row, row.isVisible, row.isSelected]);
    const originalInput = input.value;
    const fixtures = [
        new WordRow(-301, 90001, 'searchprobe-apple', '検証用果物', 'editorprobe-a'),
        new WordRow(-302, 90002, 'searchprobe-apricot', '検証用果物', 'editorprobe-b'),
        new WordRow(-303, 90003, 'searchprobe-car', '検証用乗物', 'editorprobe-a'),
    ];
    const results = [];
    const verifyVisibleRows = (expected, label) => {
        const actual = table.words.filter(row => row.isVisible).map(row => row.id);
        if (JSON.stringify(actual) !== JSON.stringify(expected)) {
            throw new Error(`${label}: 期待=${JSON.stringify(expected)}, 実際=${JSON.stringify(actual)}`);
        }
        for (const row of table.words) {
            const expectedVisible = expected.includes(row.id);
            const displayed = getComputedStyle(row.element).display !== 'none';
            if (displayed !== expectedVisible) {
                throw new Error(`${label}: 単語ID ${row.id} のDOM表示状態が一致しない`);
            }
        }
        results.push(label);
    };
    const verify = (query, expected, label) => {
        input.value = query;
        button.click();
        verifyVisibleRows(expected, label);
    };
    try {
        fixtures.forEach(row => table.registerWordRow(row));
        fixtures[2].isSelected = true;
        verify('searchprobe-apple', [-301], '検索ボタンによる単語の単一検索');
        if (fixtures[2].isSelected || !fixtures[2].element.classList.contains('d-none')) {
            throw new Error('検索対象外行の非表示・選択解除が行われない');
        }
        verify('検証用果物', [-301, -302], '意味の検索');
        verify('editorprobe-a', [-301, -303], '最終編集者の検索');
        verify('  searchprobe- \t 検証用果物　 editorprobe-a  ', [-301], '空白区切りのフィールド横断AND検索');
        verify('searchprobe-該当なし', [], '該当なしの検索');
        const allIds = table.words.map(row => row.id);
        verify('', allIds, '空欄検索で全件復帰');
        verify(' \t　 ', allIds, '空白のみの検索で全件復帰');
        startRange.value = '90002';
        endRange.value = '90003';
        startRange.dispatchEvent(new Event('change'));
        endRange.dispatchEvent(new Event('change'));
        const rangedIds = table.words.filter(row => row.number >= 90002 && row.number <= 90003)
            .map(row => row.id);
        verifyVisibleRows(rangedIds, '検索後も番号範囲の変更で絞り込める');
        return { passed: results };
    } finally {
        fixtures.forEach(row => table.removeWordRow(row));
        original.forEach(([row, visible, selected]) => {
            row.setVisible(visible);
            row.isSelected = selected;
        });
        input.value = originalInput;
        [startRange.value, endRange.value] = originalRange;
    }
})()
