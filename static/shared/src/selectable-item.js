export class SelectableElement extends HTMLDivElement {
    constructor(name, content, isSelected = false) {
        super();
        this.onCheck = (e) => {
            const checkbox = e.target;
            if (!(checkbox instanceof HTMLInputElement)) {
                throw new Error("onCheck method was called by except for checkbox on SelectableElement.");
            }
            this.toggleSelected(checkbox.checked);
        };
        this.name = name;
        this._isSelected = isSelected;
        this.content = content;
        this.addClassName(...[
            String(name),
            SelectableElement.selectableElementClassName,
            ...SelectableElement.selectedElementOtherClasses,
        ]);
        this.checkbox = this.createCheckbox();
        this.appendChild(this.checkbox);
        this.appendChild(content);
    }
    createCheckbox() {
        const checkbox = Object.assign(document.createElement("input"), {
            type: "checkbox",
            className: SelectableElement.checkboxClassName,
        });
        checkbox.classList.add(...SelectableElement.checkboxOtherClasses);
        checkbox.addEventListener("change", this.onCheck);
        return checkbox;
    }
    addClassName(...tokens) {
        this.classList.add(...tokens);
        return this;
    }
    toggleSelected(isSelected) {
        this._isSelected = isSelected;
        this.classList.toggle(SelectableElement.selectedElemClassName, isSelected);
        return this;
    }
    get isSelected() {
        return this._isSelected;
    }
    set isSelected(isSelected) {
        this.toggleSelected(isSelected);
    }
}
SelectableElement.selectableElementClassName = "selectable-element";
SelectableElement.selectedElemClassName = "selected";
SelectableElement.selectedElementOtherClasses = ["d-flex", "flex-row", "flex-shrink-0", "border"];
SelectableElement.checkboxClassName = "select-checkbox";
SelectableElement.checkboxOtherClasses = ["p-2", "border-end"];
//# sourceMappingURL=selectable-item.js.map