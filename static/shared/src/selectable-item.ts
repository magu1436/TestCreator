

export class SelectableElement extends HTMLDivElement {

    static readonly selectableElementClassName = "selectable-element";
    static readonly selectedElemClassName = "selected";
    static readonly selectedElementOtherClasses = ["d-flex", "flex-row", "flex-shrink-0", "border"];
    static readonly checkboxClassName = "select-checkbox";
    static readonly checkboxOtherClasses = ["p-2", "border-end"];
    name: String;
    readonly checkbox: HTMLInputElement;
    content: HTMLElement;
    private _isSelected: boolean;

    constructor(name: String, content: HTMLElement, isSelected: boolean = false){
        super();
        this.name = name;
        this._isSelected = isSelected;
        this.content = content
        this.addClassName(...[
            String(name),
            SelectableElement.selectableElementClassName,
            ...SelectableElement.selectedElementOtherClasses,
        ])

        this.checkbox = this.createCheckbox();
        this.appendChild(this.checkbox);
        this.appendChild(content);
    }

    protected createCheckbox(): HTMLInputElement{
        const checkbox = Object.assign(document.createElement("input"), {
            type: "checkbox",
            className: SelectableElement.checkboxClassName,
        })
        checkbox.classList.add(...SelectableElement.checkboxOtherClasses);
        checkbox.addEventListener("change", this.onCheck);
        return checkbox;
    }

    protected onCheck = (e: Event) => {
        const checkbox = e.target
        if (!(checkbox instanceof HTMLInputElement)){
            throw new Error("onCheck method was called by except for checkbox on SelectableElement.");
        }
        this.toggleSelected(checkbox.checked);
    }

    addClassName(...tokens: string[]): this{
        this.classList.add(...tokens);
        return this;
    }

    toggleSelected(isSelected: boolean): this{
        this._isSelected = isSelected
        this.classList.toggle(SelectableElement.selectedElemClassName, isSelected);
        return this;
    }

    get isSelected(): boolean{
        return this._isSelected;
    }

    set isSelected(isSelected: boolean){
        this.toggleSelected(isSelected);
    }
}