// DDゾーンの作成

const dropzone = document.getElementById("dropzone") as HTMLElement | null;

if(dropzone){
    (['dragenter','dragover'] as const).forEach(ev => {
        dropzone.addEventListener(ev, (e: DragEvent) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });
    });
    (['dragleave','drop'] as const).forEach(ev => {
        dropzone.addEventListener(ev, (e: DragEvent) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
        });
    });
}