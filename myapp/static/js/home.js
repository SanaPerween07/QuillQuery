function showFiles(event) {
  const input = event.target;
  let files = Array.from(input.files);
  const preview = document.getElementById("file-preview");
  preview.innerHTML = "";

  files.forEach((file, index) => {
    const chip = document.createElement("div");
    chip.className = "file-chip";

    const icon = document.createElement("i");
    icon.className = "bi bi-file-pdf-fill file-pdf";

    const name = document.createElement("span");
    name.textContent = `${file.name} (${Math.round(file.size / 1024)} KB)`;

    const removeBtn = document.createElement("div");
    removeBtn.className = "file-remove";
    removeBtn.innerHTML = "X";
    removeBtn.style.cursor = "pointer";
    removeBtn.onclick = () => {
      files.splice(index, 1);
      updateInputFiles(input, files);
      showFiles({ target: input });
    };

    chip.append(icon, name, removeBtn);
    preview.appendChild(chip);
  });
}

function updateInputFiles(input, files) {
  const dt = new DataTransfer();
  files.forEach(file => dt.items.add(file));
  input.files = dt.files;
}

function autoResize(textarea) {
  textarea.style.height = "auto";             
  textarea.style.height = textarea.scrollHeight + "px";  
}

document.getElementById("chat-form").addEventListener("submit", async function(e) {
    e.preventDefault();

    let formData = new FormData(this);

    let response = await fetch("", {  
        method: "POST",
        body: formData,
        headers: {"X-Requested-With": "XMLHttpRequest"}
    });

    let data = await response.json();

    let chatContainer = document.getElementById("chat-container");

    let questionBlock = `
      <div class="d-flex flex-column align-items-end mb-2 mt-3">
        ${data.files.length ? `
          <div class="d-flex flex-wrap gap-2 mb-1">
            ${data.files.map(file => `
              <span class="file-chip" style="background-color: #ffe4c6; border-radius: 1rem; padding: 0.4rem 0.6rem;">
                <i class="bi bi-file-pdf-fill file-pdf" style="color: #f71d16;"></i> ${file}
              </span>
            `).join('')}
          </div>` : ''}
        <div class="p-3 rounded-4 text-white shadow-sm chat-question">
          ${data.question}
        </div>
      </div>
    `;

    let answerBlock = `
      <div class="d-flex justify-content-start mb-2">
        <div class="p-3 rounded-4 text-white shadow-sm chat-answer">
          ${data.answer}
        </div>
      </div>
    `;

    chatContainer.insertAdjacentHTML("beforeend", questionBlock + answerBlock);

    chatContainer.scrollTop = chatContainer.scrollHeight;

    this.reset();
});





