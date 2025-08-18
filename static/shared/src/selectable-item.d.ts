export declare class SelectableElement extends HTMLDivElement {
    static readonly selectableElementClassName = "selectable-element";
    static readonly selectedElemClassName = "selected";
    static readonly selectedElementOtherClasses: string[];
    static readonly checkboxClassName = "select-checkbox";
    static readonly checkboxOtherClasses: string[];
    name: String;
    readonly checkbox: HTMLInputElement;
    content: HTMLElement;
    private _isSelected;
    constructor(name: String, content: HTMLElement, isSelected?: boolean);
    protected createCheckbox(): HTMLInputElement;
    protected onCheck: (e: Event) => void;
    addClassName(...tokens: string[]): this;
    toggleSelected(isSelected: boolean): this;
    get isSelected(): boolean;
    set isSelected(isSelected: boolean);
}
//# sourceMappingURL=selectable-item.d.ts.map