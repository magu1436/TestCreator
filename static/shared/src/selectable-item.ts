
export class SelectableItem {

    static readonly selectableElementClassName = "selectable-element";
    static readonly selectedElemClassName = "selected";
    static readonly selectedElementOtherClasses = ["d-flex", "flex-row", "flex-shrink-0", "border"];
    static readonly contentClassName = "selectable-element-content";
    static readonly checkboxClassName = "select-checkbox";
    static readonly checkboxDivName = "checkbox-div";
    static readonly checkboxOtherClasses = ["p-2", "border-end"];
    readonly element: HTMLDivElement;
    readonly checkbox: HTMLDivElement;
    private _content: HTMLElement | null = null;
    private _isSelected: boolean;

    constructor(content: HTMLElement | null = null, isSelected: boolean = false){
        this._isSelected = isSelected;
        this.content = content;
        this.checkbox = this.createCheckbox();
        this.element = this.createSelectableDivElement();
    }

    protected createSelectableDivElement(){
        const divElem = document.createElement("div");
        divElem.classList.add(
            SelectableItem.selectableElementClassName,
            ...SelectableItem.selectedElementOtherClasses,
        );
        divElem.appendChild(this.checkbox);
        if (this._content) {
            divElem.appendChild(this._content);
        }
        return divElem;
    }
    
    protected createCheckbox(): HTMLDivElement{
        const checkboxDiv = Object.assign(document.createElement("div"), {
            className: SelectableItem.checkboxDivName
        });
        checkboxDiv.classList.add(...SelectableItem.checkboxOtherClasses);
        const checkbox = Object.assign(document.createElement("input"), {
            type: "checkbox",
            className: SelectableItem.checkboxClassName,
        });
        checkbox.addEventListener("change", this.onCheck);
        checkboxDiv.appendChild(checkbox);
        return checkboxDiv;
    }

    protected onCheck = (e: Event) => {
        const checkbox = e.target
        if (!(checkbox instanceof HTMLInputElement)){
            throw new Error("onCheck method was called by except for checkbox on SelectableElement.");
        }
        this.toggleSelected(checkbox.checked);
    }

    addClassName(...tokens: string[]): this {
        this.element.classList.add(...tokens);
        return this;
    }

    toggleSelected(isSelected: boolean): this{
        this._isSelected = isSelected
        this.element.classList.toggle(SelectableItem.selectedElemClassName, isSelected);
        (this.checkbox.firstChild as HTMLInputElement).checked = isSelected;
        return this;
    }

    get isSelected(): boolean{
        return this._isSelected;
    }

    set isSelected(isSelected: boolean){
        this.toggleSelected(isSelected);
    }

    get content(){
        return this._content;
    }

    set content(content: HTMLElement | null){
        if (this._content != null)this.element.removeChild(this._content);
        if (content != null)content.classList.add(SelectableItem.contentClassName);
        this._content = content;
    }
}