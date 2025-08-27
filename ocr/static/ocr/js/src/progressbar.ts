

export class ProgressBar {
    static readonly wrapId = "overall-progress-wrap";
    static readonly overallPercentId = "overall-percent";
    static readonly overallProgressId = "overall-progress";

    protected static _instance: ProgressBar;

    readonly wrapElem: HTMLDivElement;
    readonly percentDisplayElem: HTMLSpanElement;
    readonly progressbarElem: HTMLDivElement;

    protected _percent = 0;

    constructor(){
        if (ProgressBar._instance) throw new Error("ProgressBar is singleton, but a ProgressBar instance has existed");

        this.wrapElem = document.getElementById(ProgressBar.wrapId) as HTMLDivElement;
        this.percentDisplayElem = document.getElementById(ProgressBar.overallPercentId) as HTMLSpanElement;
        this.progressbarElem = document.getElementById(ProgressBar.overallProgressId) as HTMLDivElement;
    }

    toggleVisible(visible: boolean){
        this.wrapElem.classList.toggle("d-none", !visible);
    }

    increase(progress: number){
        this.percent += progress;
    }

    decrease(progress: number){
        this.percent -= progress;
    }

    get percent(){
        return this._percent;
    }

    set percent(percent: number){
        this._percent = percent;
        this.percentDisplayElem.textContent = String(percent);
        this.progressbarElem.style.width = `${percent}%`;
    }

    get visible(){
        return !this.wrapElem.classList.contains("d-none");
    }

    set visible(visible: boolean){
        this.toggleVisible(visible);
    }

    static get instance(){
        if (!ProgressBar._instance) ProgressBar._instance = new ProgressBar();
        return ProgressBar._instance;
    }
}