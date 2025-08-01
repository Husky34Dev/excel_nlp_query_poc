// Drag & Drop para subir archivos

document.addEventListener("DOMContentLoaded", () => {
    // --- Elementos del DOM ---
    const fileInput = document.getElementById("file-input");
    const dropzone = document.getElementById('upload-dropzone');
    const uploadNewBtn = document.getElementById("upload-new-btn");
    const fileList = document.getElementById("file-list");
    const welcomeView = document.getElementById("welcome-view");
    const chatView = document.getElementById("chat-view");
    const currentFileName = document.getElementById("current-file-name");
    const responseContainer = document.querySelector(".response-container");
    const userQuestion = document.getElementById("user-question");
    const sendButton = document.getElementById("send-question");



    // --- Elementos del Modal de Subida ---
    const uploadModal = document.getElementById("upload-modal");
    const fileToUploadDiv = document.getElementById("file-to-upload");
    const fileNameInput = document.getElementById("file-name-input");
    const startUploadBtn = document.getElementById("start-upload");
    const cancelUploadBtn = document.getElementById("cancel-upload");
    const uploadProgressContainer = document.getElementById("upload-progress-container");
    const progressBar = document.getElementById("upload-progress");
    const progressLabel = document.getElementById("upload-progress-label");
    const processingView = document.getElementById("processing-view");

    // --- Estado de la Aplicación ---
    let fileToUpload = null;
    let currentFileId = null;
    let xhr = null;
    const chatHistories = {}; // Almacena historiales de chat: { file_id: [messages] }

    // --- Funciones del Chat ---

    const scrollToBottom = () => {
        responseContainer.scrollTop = responseContainer.scrollHeight;
    };

    const addMessage = (sender, text) => {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat-message", `${sender}-message`);
        const avatar = `<div class="avatar"><i class="fa-solid ${sender === 'user' ? 'fa-user' : 'fa-robot'}"></i></div>`;
        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');

        if (sender === 'assistant') {
            // Mostrar mensaje amigable si la respuesta es null (como string o valor JSON)
            let rendered = false;
            if (text === 'null' || text === null) {
                const p = document.createElement('p');
                p.textContent = 'Sin resultados para esta consulta.';
                contentDiv.appendChild(p);
                rendered = true;
            } else {
                try {
                    const parsed = JSON.parse(text);
                    if (parsed === null) {
                        const p = document.createElement('p');
                        p.textContent = 'Sin resultados para esta consulta.';
                        contentDiv.appendChild(p);
                        rendered = true;
                    } else {
                        // Renderizado recursivo universal
                        function renderAny(val) {
                            if (val === null) return document.createTextNode('null');
                            if (typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean') {
                                return document.createTextNode(val);
                            }
                            if (Array.isArray(val)) {
                                if (val.length === 0) return document.createTextNode('[]');
                                // Si es array de objetos, renderiza tabla
                                if (typeof val[0] === 'object' && val[0] !== null && !Array.isArray(val[0])) {
                                    const table = document.createElement('table');
                                    table.className = 'json-table';
                                    const thead = document.createElement('thead');
                                    const headerRow = document.createElement('tr');
                                    Object.keys(val[0]).forEach(key => {
                                        const th = document.createElement('th');
                                        th.textContent = key;
                                        headerRow.appendChild(th);
                                    });
                                    thead.appendChild(headerRow);
                                    table.appendChild(thead);
                                    const tbody = document.createElement('tbody');
                                    val.forEach(row => {
                                        const tr = document.createElement('tr');
                                        Object.keys(val[0]).forEach(key => {
                                            const td = document.createElement('td');
                                            td.appendChild(renderAny(row[key]));
                                            tr.appendChild(td);
                                        });
                                        tbody.appendChild(tr);
                                    });
                                    table.appendChild(tbody);
                                    return table;
                                } else {
                                    // Array simple o array de arrays
                                    const ul = document.createElement('ul');
                                    val.forEach(item => {
                                        const li = document.createElement('li');
                                        li.appendChild(renderAny(item));
                                        ul.appendChild(li);
                                    });
                                    return ul;
                                }
                            }
                            if (typeof val === 'object') {
                                const table = document.createElement('table');
                                table.className = 'json-table';
                                const thead = document.createElement('thead');
                                const headerRow = document.createElement('tr');
                                Object.keys(val).forEach(key => {
                                    const th = document.createElement('th');
                                    th.textContent = key;
                                    headerRow.appendChild(th);
                                });
                                thead.appendChild(headerRow);
                                table.appendChild(thead);
                                const tbody = document.createElement('tbody');
                                const tr = document.createElement('tr');
                                Object.keys(val).forEach(key => {
                                    const td = document.createElement('td');
                                    td.appendChild(renderAny(val[key]));
                                    tr.appendChild(td);
                                });
                                tbody.appendChild(tr);
                                table.appendChild(tbody);
                                return table;
                            }
                            // Fallback
                            return document.createTextNode(String(val));
                        }
                        contentDiv.appendChild(renderAny(parsed));
                        rendered = true;
                    }
                } catch (e) {}
            }
            if (!rendered) {
                const pre = document.createElement('pre');
                pre.textContent = text;
                contentDiv.appendChild(pre);
            }
        } else {
            const p = document.createElement('p');
            p.textContent = text;
            contentDiv.appendChild(p);
        }

        messageDiv.innerHTML = avatar;
        messageDiv.appendChild(contentDiv);
        responseContainer.appendChild(messageDiv);
        scrollToBottom();
    };
// --- Estilos para tablas generadas desde JSON ---
const style = document.createElement('style');
style.textContent = `
.json-table, .preview-table {
  border-collapse: collapse;
  width: 100%;
  margin: 0.5em 0;
  font-size: 1em;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.json-table th, .json-table td, .preview-table th, .preview-table td {
  border: 1px solid #e0e0e0;
  padding: 0.5em 0.8em;
  text-align: left;
}
.json-table th, .preview-table th {
  background: #f5f5f5;
  font-weight: bold;
}
.json-table tr:nth-child(even) td, .preview-table tr:nth-child(even) td {
  background: #fafbfc;
}
.wide-preview-table {
  min-width: 700px;
  table-layout: auto;
}
.col-name-input {
  min-width: 120px;
  max-width: 98%;
  font-size: 1em;
  border-radius: 4px;
  border: 1px solid #bbb;
  padding: 2px 6px;
  background: #f9f9f9;
}
.col-type-select {
  min-width: 90px;
  font-size: 1em;
  border-radius: 4px;
  border: 1px solid #bbb;
  background: #f9f9f9;
}
.col-enabled-label {
  font-size: 1em;
  margin-top: 2px;
  margin-bottom: 0;
  padding: 2px 0;
  border-radius: 3px;
  background: none;
}
.col-enabled-checkbox {
  accent-color: #b00;
  width: 18px;
  height: 18px;
  margin-right: 6px;
  vertical-align: middle;
}
#disable-warning {
  color: #b00;
  font-weight: bold;
  background: #fff3cd;
  border: 1px solid #ffeeba;
  padding: 0.5em 1em;
  border-radius: 4px;
  margin-bottom: 0.5em;
  display: none;
}
`;
document.head.appendChild(style);

    const renderChatHistory = (fileId) => {
        responseContainer.innerHTML = '';
        const history = chatHistories[fileId] || [];
        if (history.length === 0) {
            addMessage('assistant', `¡Hola! Estoy listo para responder tus preguntas sobre el archivo "${currentFileName.textContent}".`);
        } else {
            history.forEach(msg => addMessage(msg.role, msg.text));
        }
    };

    // --- Funciones de UI y Archivos ---

    const selectFileUI = (fileId, fileName) => {
        currentFileId = fileId;
        currentFileName.textContent = fileName;
        document.querySelectorAll('#file-list li').forEach(li => li.classList.remove('active'));
        const selectedLi = document.querySelector(`li[data-file-id="${fileId}"]`);
        if (selectedLi) selectedLi.classList.add('active');

        welcomeView.classList.add('hidden');
        chatView.classList.remove('hidden');
        userQuestion.value = "";
        renderChatHistory(fileId);
    };

    const renderFileList = (files) => {
        fileList.innerHTML = "";
        if (files.length === 0) {
            fileList.innerHTML = `<li class="empty-list">No hay archivos.</li>`;
            return;
        }
        files.forEach(file => {
            const li = document.createElement("li");
            li.dataset.fileId = file.file_id;
            li.dataset.fileName = file.name;
            li.innerHTML = `
                <span class="file-name">${file.name}</span>
                <div class="file-actions">
                    <button class="edit-btn" title="Editar y ver detalles"><i class="fa-solid fa-pencil"></i></button>
                </div>`;
            fileList.appendChild(li);
        });
    };

    const loadFiles = async () => {
        try {
            const res = await fetch("/files");
            const files = await res.json();
            renderFileList(files);
        } catch (err) {
            console.error("Error cargando archivos:", err);
            fileList.innerHTML = `<li class="empty-list error">Error al cargar.</li>`;
        }
    };
    
    // --- Drag & Drop para subir archivos ---
    if (dropzone && fileInput) {
        dropzone.addEventListener('click', () => {
            fileInput.click();
        });

        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });

        dropzone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                // Disparar el evento de cambio para procesar el archivo
                fileInput.dispatchEvent(new Event('change'));
            }
        });
    }
    // --- Lógica del Modal de Subida (sin cambios) ---
    const handleFileSelect = async (file) => {
        if (!file) return;
        fileToUpload = file;
        fileNameInput.value = file.name.split('.').slice(0, -1).join('.');
        fileToUploadDiv.textContent = `Archivo: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
        // Mostrar spinner de preview
        const previewContainer = document.getElementById("file-preview-container");
        previewContainer.innerHTML = '<div style="text-align:center;padding:1em;">Cargando preview...</div>';
        processingView.classList.add("hidden");
        uploadProgressContainer.classList.remove("hidden");
        progressBar.value = 0;
        progressLabel.textContent = '0%';
        startUploadBtn.disabled = false;
        cancelUploadBtn.disabled = false;
        uploadModal.classList.remove("hidden");

        // Llamar a /preview_file
        try {
            const formData = new FormData();
            formData.append("file", file);
            const res = await fetch("/preview_file", { method: "POST", body: formData });
            const data = await res.json();
            if (data.error) {
                previewContainer.innerHTML = `<div style='color:#b00;'>Error: ${data.error}</div>`;
                return;
            }
        // Renderizar tabla editable: nombres, tipos, habilitar/deshabilitar
        const allowedTypes = ["int", "float", "str", "bool", "datetime", "object"];
        let html = `<div style='margin-bottom:0.5em;'><b>Filas totales:</b> ${data.n_rows ?? 'N/A'}</div>`;
        html += `<div id='disable-warning' style='display:none;color:#b00;font-weight:bold;margin-bottom:0.5em;background:#fff3cd;border:1px solid #ffeeba;padding:0.5em 1em;border-radius:4px;'>⚠️ Cuidado: deshabilitar columnas en el procesamiento inicial eliminará esa columna <u>permanentemente</u> del archivo procesado.</div>`;
        html += `<table class='preview-table'><thead><tr>`;
        data.columns.forEach((col, idx) => {
            html += `<th>
                <input type='text' class='col-name-input' data-idx='${idx}' value='${col}' style='width:120px;'>
                <br>
                <select class='col-type-select' data-idx='${idx}' style='margin-top:2px;'>`;
            allowedTypes.forEach(t => {
                const sel = (data.dtypes[col].toLowerCase().includes(t)) ? 'selected' : '';
                html += `<option value='${t}' ${sel}>${t}</option>`;
            });
            html += `</select><br>
                <label class='col-enabled-label' style='font-size:0.95em;display:inline-flex;align-items:center;margin-top:4px;'>
                    <input type='checkbox' class='col-enabled-checkbox' data-idx='${idx}' checked style='accent-color:#b00;width:18px;height:18px;margin-right:6px;'>
                    <span>Incluir</span>
                </label>
            </th>`;
        });
        html += `</tr></thead><tbody>`;
            (data.preview || []).forEach(row => {
                html += `<tr>`;
                data.columns.forEach(col => {
                    let val = row[col];
                    if (val === null || val === undefined) val = '<span class="null-cell">null</span>';
                    html += `<td>${val}</td>`;
                });
                html += `</tr>`;
            });
            html += `</tbody></table>`;
        previewContainer.innerHTML = html;
        // Guardar info para el submit
        previewContainer.dataset.columns = JSON.stringify(data.columns);
        previewContainer.dataset.dtypes = JSON.stringify(data.dtypes);

        // Lógica de advertencia visual al deshabilitar columnas
        const warningDiv = document.getElementById('disable-warning');
        const checkboxes = previewContainer.querySelectorAll('.col-enabled-checkbox');
        checkboxes.forEach(cb => {
            cb.addEventListener('change', () => {
                const anyDisabled = Array.from(checkboxes).some(c => !c.checked);
                warningDiv.style.display = anyDisabled ? 'block' : 'none';
            });
        });
        } catch (e) {
            previewContainer.innerHTML = `<div style='color:#b00;'>Error al obtener preview</div>`;
        }
    };

    const handleFileUpload = () => {
        if (!fileToUpload) return;
        const newName = fileNameInput.value.trim();
        if (!newName) {
            alert("Por favor, asigna un nombre al archivo.");
            return;
        }
        // Construir configuración de columnas desde la tabla editable
        const previewContainer = document.getElementById("file-preview-container");
        const columns = JSON.parse(previewContainer.dataset.columns || "[]");
        const dtypes = JSON.parse(previewContainer.dataset.dtypes || "{}")
        const colConfigs = columns.map((col, idx) => {
            const nameInput = previewContainer.querySelector(`.col-name-input[data-idx='${idx}']`);
            const typeSelect = previewContainer.querySelector(`.col-type-select[data-idx='${idx}']`);
            const enabledCheckbox = previewContainer.querySelector(`.col-enabled-checkbox[data-idx='${idx}']`);
            return {
                name: col,
                new_name: nameInput.value.trim() || col,
                dtype: typeSelect.value,
                enabled: enabledCheckbox.checked
            };
        });
        startUploadBtn.disabled = true;
        cancelUploadBtn.disabled = true;
        const formData = new FormData();
        formData.append("file", fileToUpload);
        formData.append("columns", JSON.stringify(colConfigs));
        formData.append("name", newName); // <-- Enviar el nombre al backend
        // Enviar a /api/process_file
        fetch("/process_file", {
            method: "POST",
            body: formData
        }).then(async res => {
            if (res.ok) {
                const data = await res.json();
                if (data.success) {
                    // Actualizar nombre en la lista y selección
                    loadFiles().then(() => {
                        selectFileUI(data.file_id, newName);
                        // Actualizar nombre en la lista manualmente si ya está
                        const li = document.querySelector(`li[data-file-id='${data.file_id}']`);
                        if (li) {
                            li.querySelector('.file-name').textContent = newName;
                            li.dataset.fileName = newName;
                        }
                    });
                    resetModal();
                } else {
                    alert("Errores en el procesamiento: " + JSON.stringify(data.errors));
                    startUploadBtn.disabled = false;
                    cancelUploadBtn.disabled = false;
                }
            } else {
                alert("Error al procesar el archivo");
                startUploadBtn.disabled = false;
                cancelUploadBtn.disabled = false;
            }
        }).catch(() => {
            alert("Error de red al procesar el archivo");
            startUploadBtn.disabled = false;
            cancelUploadBtn.disabled = false;
        });
    };

    const resetModal = () => {
        startUploadBtn.disabled = false;
        cancelUploadBtn.disabled = false;
        uploadModal.classList.add("hidden");
    };

    // --- Lógica del Modal de Edición/Borrado (Fusionado) ---
    const createEditModal = () => {
        let editModal = document.getElementById("edit-file-modal");
        if (!editModal) {
            editModal = document.createElement("div");
            editModal.id = "edit-file-modal";
            editModal.className = "modal-overlay hidden";
            editModal.innerHTML = `
                <div class="modal-content">
                    <h3>Editar Archivo</h3>
                    <div id="edit-file-info" class="info-block"></div>
                    <div id="edit-table-container" class="table-container"></div>
                    <label for="edit-file-name" style="margin-top: 1rem;">Nuevo nombre:</label>
                    <input id="edit-file-name" type="text" placeholder="Nuevo nombre del archivo">
                    <label for="edit-file-prompt" style="margin-top: 1rem;">Prompt personalizado (opcional):</label>
                    <textarea id="edit-file-prompt" rows="3" style="width:100%;margin-bottom:1rem" placeholder="Ejemplo: 'La columna X representa el total de ventas en miles de euros.'"></textarea>
                    <div class="actions">
                        <button id="edit-delete-btn">Eliminar</button>
                        <button id="edit-cancel-btn">Cancelar</button>
                        <button id="edit-save-btn">Guardar</button>
                    </div>
                </div>`;
            document.body.appendChild(editModal);
        }
        return editModal;
    };
    const editModal = createEditModal();


    // --- Event Listeners ---
    fileInput.addEventListener("change", () => handleFileSelect(fileInput.files[0]));
    startUploadBtn.addEventListener("click", handleFileUpload);
    cancelUploadBtn.addEventListener("click", () => {
        if (xhr && xhr.readyState > 0 && xhr.readyState < 4) xhr.abort();
        resetModal();
    });

    // Listener de la Lista de Archivos (Fusionado)
    fileList.addEventListener("click", async e => {
        const li = e.target.closest('li[data-file-id]');
        if (!li) return;
        const fileId = li.dataset.fileId;
        const fileName = li.dataset.fileName;

        if (e.target.closest('.edit-btn')) {
            editModal.classList.remove("hidden");
            document.getElementById("edit-file-name").value = fileName;
            const infoDiv = document.getElementById("edit-file-info");
            const tableContainer = document.getElementById("edit-table-container");
            const promptInput = document.getElementById("edit-file-prompt");
            infoDiv.innerHTML = "Cargando metadatos...";
            tableContainer.innerHTML = "";
            try {
                const res = await fetch(`/files`);
                const files = await res.json();
                const meta = files.find(f => f.file_id === fileId);
                if (meta) {
                    infoDiv.innerHTML = `<b>Filas:</b> ${meta.n_rows}`;
                    let table = `<table><thead><tr><th>Columna</th><th>Tipo de Dato</th></tr></thead><tbody>`;
                    meta.columns.forEach(col => {
                        table += `<tr><td>${col}</td><td>${meta.dtypes ? meta.dtypes[col] : 'N/A'}</td></tr>`;
                    });
                    table += `</tbody></table>`;
                    tableContainer.innerHTML = table;
                    promptInput.value = meta.custom_prompt || "";
                } else {
                    infoDiv.innerHTML = "No se encontraron metadatos.";
                }
            } catch {
                infoDiv.innerHTML = "Error al cargar metadatos.";
            }

            document.getElementById("edit-save-btn").onclick = async () => {
                const newName = document.getElementById("edit-file-name").value.trim();
                const newPrompt = promptInput.value.trim();
                if (!newName) return;
                try {
                    const res = await fetch("/rename_file", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ file_id: fileId, name: newName, prompt: newPrompt })
                    });
                    const data = await res.json();
                    if (data.success) {
                        li.querySelector('.file-name').textContent = newName;
                        li.dataset.fileName = newName;
                        if (currentFileId === fileId) {
                            currentFileName.textContent = newName;
                        }
                        editModal.classList.add("hidden");
                    } else {
                        alert("Error al guardar: " + data.error);
                    }
                } catch {
                    alert("Error de conexión al guardar.");
                }
            };
            document.getElementById("edit-delete-btn").onclick = async () => {
                if (!confirm("¿Seguro que quieres eliminar este archivo?")) return;
                try {
                    const res = await fetch("/delete_file", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ file_id: fileId })
                    });
                    const data = await res.json();
                    if (data.success) {
                        li.remove();
                        if (currentFileId === fileId) {
                            welcomeView.classList.remove('hidden');
                            chatView.classList.add('hidden');
                        }
                        editModal.classList.add("hidden");
                    } else {
                        alert("Error al eliminar: " + data.error);
                    }
                } catch {
                    alert("Error de conexión al eliminar.");
                }
            };
            document.getElementById("edit-cancel-btn").onclick = () => editModal.classList.add("hidden");

        } else {
            selectFileUI(fileId, fileName);
        }
    });

    // Listener para enviar pregunta (Fusionado)
    const handleSendQuestion = async () => {
        const question = userQuestion.value.trim();
        if (!currentFileId || !question) return;

        if (!chatHistories[currentFileId]) chatHistories[currentFileId] = [];
        chatHistories[currentFileId].push({ role: 'user', text: question });
        addMessage('user', question);
        userQuestion.value = "";
        userQuestion.focus();
        sendButton.disabled = true;
        addMessage('assistant', 'Procesando...');

        try {
            const res = await fetch("/query", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ file_id: currentFileId, question: question }),
            });
            const data = await res.json();
            let responseText;
            const isTechnicalError = (val) => {
                if (!val) return false;
                if (typeof val === 'string') {
                    return val.startsWith('❌') || val.toLowerCase().includes('runtime error') || val.toLowerCase().includes('error de ejecución');
                }
                return false;
            };
            if (data.result && !isTechnicalError(data.result)) {
                responseText = JSON.stringify(data.result, null, 2);
            } else {
                responseText = "Lo siento, parece que algo salió mal al procesar tu consulta.";
            }
            chatHistories[currentFileId].push({ role: 'assistant', text: responseText });
            responseContainer.removeChild(responseContainer.lastChild); // Quita "Procesando..."
            addMessage('assistant', responseText);
        } catch (err) {
            const errorText = "Lo siento, parece que algo salió mal al procesar tu consulta.";
            chatHistories[currentFileId].push({ role: 'assistant', text: errorText });
            responseContainer.removeChild(responseContainer.lastChild);
            addMessage('assistant', errorText);
        } finally {
            sendButton.disabled = false;
        }
    };
    sendButton.addEventListener("click", handleSendQuestion);
    userQuestion.addEventListener("keydown", e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendQuestion();
        }
    });

    // --- Carga Inicial ---
    loadFiles();
});