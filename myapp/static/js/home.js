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

