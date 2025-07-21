sendButton.addEventListener("click", async () => {
  const question = userQuestion.value.trim();
  const fileId = fileSelector.value;

  if (!fileId || !question) {
    alert("Debes seleccionar un archivo y escribir una pregunta.");
    return;
  }

  sendButton.disabled = true;
  chatResponse.textContent = "Procesando...";

  try {
    const res = await fetch("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_id: fileId, question: question }),
    });

    const data = await res.json();

    if (data.result) {
      chatResponse.textContent = JSON.stringify(data.result, null, 2);
    } else if (data.error) {
      chatResponse.textContent = `❌ Error: ${data.error}`;
    } else {
      chatResponse.textContent = "⚠️ Sin respuesta.";
    }

  } catch (err) {
    chatResponse.textContent = "❌ Error de conexión.";
  }

  sendButton.disabled = false;
});
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const progressContainer = document.getElementById("progress-container");
const progressBar = document.getElementById("upload-progress");
const fileSelector = document.getElementById("file-selector");
const sendButton = document.getElementById("send-question");
const chatResponse = document.getElementById("chat-response");
const userQuestion = document.getElementById("user-question");

let currentFileId = null;

// Drag & Drop
dropZone.addEventListener("click", () => fileInput.click());

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("dragover");
  const file = e.dataTransfer.files[0];
  handleFileUpload(file);
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (file) handleFileUpload(file);
});

async function handleFileUpload(file) {
  disableUI(true);
  progressContainer.classList.remove("hidden");

  const formData = new FormData();
  formData.append("file", file);

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/upload", true);

  xhr.upload.addEventListener("progress", (e) => {
    if (e.lengthComputable) {
      const percent = Math.round((e.loaded / e.total) * 100);
      progressBar.value = percent;
    }
  });

  xhr.onload = () => {
    progressContainer.classList.add("hidden");
    disableUI(false);

    if (xhr.status === 200) {
      const res = JSON.parse(xhr.responseText);
      currentFileId = res.file_id;
      addFileToSelector(currentFileId);
      alert("Archivo cargado correctamente.");
    } else {
      alert("Error al subir el archivo.");
    }
  };

  xhr.onerror = () => {
    progressContainer.classList.add("hidden");
    disableUI(false);
    alert("Error en la conexión.");
  };

  xhr.send(formData);
}

function disableUI(disabled) {
  fileSelector.disabled = disabled;
  sendButton.disabled = disabled;
  userQuestion.disabled = disabled;
  dropZone.style.pointerEvents = disabled ? "none" : "auto";
}

function addFileToSelector(fileId) {
  const option = document.createElement("option");
  option.value = fileId;
  option.textContent = `Archivo ${fileId.slice(0, 8)}...`;
  fileSelector.appendChild(option);
  fileSelector.value = fileId;
}
