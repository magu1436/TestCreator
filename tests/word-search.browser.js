// 単語一覧の読込後、閲覧・編集の各画面でこのスクリプトを実行する。
// 検証用の単語はブラウザ内だけに追加し、終了時に元の表示・選択状態へ戻す。
(async () => {
    const { WordRow, WordTable } = await import('/static/vocab/js/dist/word.js');
    const table = WordTable.instance;
    const input = document.getElementById('search_box');
    const button = document.getElementById('search-button');
    if (!input || !button) throw new Error('検索ボックスまたは検索ボタン(#search-button)が見つからない');
    const startRange = document.getElementById('start-range');
    const endRange = document.getElementById('end-range');
    const originalRange = [startRange.value, endRange.value];
    const original = table.words.map(row => [row, row.isVisible, row.isSelected]);
    const originalInput = input.value;
    const allWordCheckbox = document.getElementById('all-word-checkbox');
    const originalAllChecked = allWordCheckbox?.checked;
    const fixtures = [
        new WordRow(-301, 90001, 'searchprobe-apple', '検証用果物', 'editorprobe-a'),
        new WordRow(-302, 90002, 'searchprobe-apricot', '検証用果物', 'editorprobe-b'),
        new WordRow(-303, 90003, 'SearchProbe-Car', '検証用乗物', 'EditorProbe-A'),
    ];
    const registered = [];
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
        fixtures.forEach(row => {
            table.registerWordRow(row);
            registered.push(row);
        });
        fixtures[2].isSelected = true;
        verify('searchprobe-apple', [-301], '検索ボタンによる単語の単一検索');
        if (fixtures[2].isSelected || !fixtures[2].element.classList.contains('d-none')) {
            throw new Error('検索対象外行の非表示・選択解除が行われない');
        }
        verify('検証用果物', [-301, -302], '意味の検索');
        verify('editorprobe-a', [-301, -303], '最終編集者の検索');
        verify('  searchprobe- \t 検証用果物　 editorprobe-a  ', [-301], '空白区切りのフィールド横断AND検索');
        verify('searchprobe-car', [-303], '大文字を含む単語を小文字で検索');
        verify('SEARCHPROBE-APPLE', [-301], '小文字の単語を大文字で検索');
        verify('searchprobe-該当なし', [], '該当なしの検索');
        input.value = '検証用乗物';
        input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', isComposing: true }));
        verifyVisibleRows([], '日本語入力の変換確定中のEnterでは検索しない');
        input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
        verifyVisibleRows([-303], 'Enterキーによる検索');
        if (location.pathname.includes('/editor/') && allWordCheckbox) {
            verify('検証用果物', [-301, -302], '全選択前の絞り込み');
            const selectedIds = () => table.words.filter(row => row.isSelected).map(row => row.id);
            allWordCheckbox.checked = false;
            allWordCheckbox.click(); // 未チェック→チェックにして全選択する
            if (JSON.stringify(selectedIds()) !== JSON.stringify([-301, -302])) {
                throw new Error(`全選択は表示中の単語だけを選択する: 実際=${JSON.stringify(selectedIds())}`);
            }
            allWordCheckbox.click();
            if (allWordCheckbox.checked || selectedIds().length !== 0) {
                throw new Error('全選択の解除で選択が残っている');
            }
            results.push('全選択は検索で表示中の単語だけを選択する');
        }
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
        registered.forEach(row => table.removeWordRow(row));
        original.forEach(([row, visible, selected]) => {
            row.setVisible(visible);
            row.isSelected = selected;
        });
        input.value = originalInput;
        if (allWordCheckbox) allWordCheckbox.checked = originalAllChecked;
        [startRange.value, endRange.value] = originalRange;
    }
})()
