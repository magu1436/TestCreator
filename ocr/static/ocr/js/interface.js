

document.getElementById("upload-form").addEventListener("submit", async(e) => {
    e.preventDefault();

    const files = document.getElementById("file-input").files;
    if(!files.length) return;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++){
        formData.append("files", files[i]);
    }

    fetch(appUrls["ocr:ocr"], {
        method: "POST",
        body: formData,
        headers: {"X-CSRFToken": getCSRFToken()},
    })
    .then(async (res) => {
        const resData = await res.json();

        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);

        console.log(resData.message);
    })
    .catch((err) => {
        console.log(err);
    })
})