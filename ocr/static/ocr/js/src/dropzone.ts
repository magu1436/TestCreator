export class DropZone{
    
    static readonly id = "dropzone";
    static readonly initBodyId = "init-dropzone-body";
    static readonly bodyUploadedId = "body-uploaded";
    static readonly counterId = "file-count";
    static readonly fileInputId = "file-input";
    static readonly maxFileAmount = 20;
    readonly element: HTMLDivElement;
    readonly initBody: HTMLDivElement;
    readonly bodyUploaded: HTMLDivElement;
    protected _droppedFiles: ImageFile[] = [];
    protected readonly counter: HTMLSpanElement;
    protected readonly fileInput: HTMLInputElement;
    
    constructor(){
        const elem = document.getElementById(DropZone.id)
        const initBody = document.getElementById(DropZone.initBodyId);
        const bodyUploaded = document.getElementById(DropZone.bodyUploadedId);
        const counter = document.getElementById(DropZone.counterId);
        const fileInput = document.getElementById(DropZone.fileInputId);

        if((initBody instanceof HTMLDivElement) && (bodyUploaded instanceof HTMLDivElement)){
            this.initBody = initBody;
            this.bodyUploaded = bodyUploaded;
        } else {
            throw new Error(`${DropZone.initBodyId} or ${DropZone.bodyUploadedId} does not exist.`);
        }

        if(!counter){
            throw new Error(`The ${DropZone.counterId} object does not exist.`);
        } else if (!(counter instanceof HTMLSpanElement)){
            throw new Error(`The ${DropZone.counterId} object is not Span Element.`);
        } else {
            this.counter = counter;
        }
        
        if(!fileInput){
            throw new Error(`The ${DropZone.fileInputId} object does not exist.`);
        } else if (!(fileInput instanceof HTMLInputElement)){
            throw new Error(`The ${DropZone.fileInputId} object is not Input Element.`);
        } else {
            this.fileInput = fileInput;
        }

        if(elem instanceof HTMLDivElement){
            this.element = elem;
        } else {
            throw new Error(`The ${DropZone.id} element does not exist.`);
        }

        (['dragenter','dragover'] as const).forEach(ev => {
            this.element.addEventListener(ev, (e: DragEvent) => {
                e.preventDefault();
                this.initBody.classList.add('dragover');
            });
        });
        (['dragleave','drop'] as const).forEach(ev => {
            this.element.addEventListener(ev, (e: DragEvent) => {
                e.preventDefault();
                this.initBody.classList.remove('dragover');
            });
        });
        this.element.addEventListener("drop", this.onDrop);
        this.fileInput.addEventListener("change", this.onInput);
        this.toggleDisplayingBody();
    }

    /**
     * ファイルを `ImageFile` オブジェクトに変換して `droppedFiles` プロパティに追加するメソッド.
     * @param file 追加する画像ファイル
     */
    protected addFileAsImageFile(file: File){
        if (this.droppedFiles.length >= DropZone.maxFileAmount){
            return alert("追加できる画像は最大20枚です.");
        }

        const img = new ImageFile(file);
        this._droppedFiles.push(img);
        this.bodyUploaded.appendChild(img.element);
        this.toggleDisplayingBody();
        this.counterUpdate();
        console.log(`${img.name} was uploaded.`);
    }

    removeImageFile(file: ImageFile){
        const removedArray = this._droppedFiles.filter(f => f !== file);
        if (removedArray.length === this._droppedFiles.length) throw new Error("this file haven't been dropped yet.");
        this._droppedFiles = removedArray;
        this.bodyUploaded.removeChild(file.element);
        this.toggleDisplayingBody();
        this.counterUpdate();
    }

    protected onInput = () => {
        const files = this.fileInput.files
        if (files == null) return;
        for (let f of files){
            this.addFileAsImageFile(f);
        }
    }

    protected onDrop = (e: DragEvent) => {
        const tf = e.dataTransfer;
        if(tf != null){
            for (let f of tf.files){
                this.addFileAsImageFile(f);
            }
        }
    }

    /**
     * アップロード済みの画像枚数表示を更新するメソッド.
     */
    protected counterUpdate(){
        this.counter.textContent = `${this.droppedFiles.length} 枚`;
    }

    /**
     * アップロード済みの画像の枚数から, 表示するボディを変更するメソッド.
     */
    toggleDisplayingBody(){
        const isDisplayInitBody = (this.droppedFiles.length == 0);
        this.initBody.classList.toggle("d-none", !isDisplayInitBody);
        this.bodyUploaded.classList.toggle("d-none", isDisplayInitBody);
    }

    get droppedFiles(): ReadonlyArray<ImageFile>{
        return this._droppedFiles;
    }
}


class ImageFile{

    static readonly classList = ["image-file", "border"]
    readonly name: String;
    readonly file: File;
    readonly element: HTMLDivElement;

    constructor(file: File){
        this.name = file.name;
        this.file = file;
        this.element = this.createDivElement();

    }

    private createDivElement(): HTMLDivElement{
        const textContent: HTMLHeadElement = Object.assign(
            document.createElement("h6"),
            {
                textContent: this.name,
            }
        );
        const divElement: HTMLDivElement = document.createElement("div");
        ImageFile.classList.forEach(c => {
            divElement.classList.add(c);
        })
        divElement.appendChild(textContent);
        return divElement;
    }
}