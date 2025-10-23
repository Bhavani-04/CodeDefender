window.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.getElementById('fileInput');
  const resultSection = document.getElementById('result');
  let lastResult = null;

  fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    if (!file) {
      resultSection.innerHTML = '<p>Please select a file to analyze.</p>';
      return;
    }
    
    const formData = new FormData();
    formData.append('codefile',file);

    resultSection.innerHTML = '<p>Analyzing file...</p>';

    fetch('/analyze', {
      method: 'POST',
      body: formData
    })
      .then(res => res.json())
      .then(data => {
        console.log("📦 Received results:", data.results);
        lastResult = data;
        renderResult(data);
        showDownloadButton();
      })
      .catch(async err => {
        const errorText = await err.text?.();
        resultSection.innerHTML = `<p>❌ Analysis failed.</p><pre>${errorText || 'No error details'}</pre>`;
        console.error('Analysis error:', err);
      });
  });
  function renderResult(data) {
  const { filename, language, summary, results } = data;

  let html = `
    <div class="result-header">
      <h3>📄 Analysis Result for <code>${filename}</code></h3>
      <p>🗂 Language: <strong>${language}</strong></p>
      <p>🔴 High: <strong>${summary.high}</strong> | 🟠 Medium: <strong>${summary.medium}</strong> | 🟢 Low: <strong>${summary.low}</strong></p>
      <p>🕒 Time Taken: <strong>${summary.time}</strong></p>
    </div>
  `;

  if (!results || results.length === 0) {
    html += `<p>No issues found 🎉</p>`;
  } else {
    html += `<h4>📌 Security & Code Quality Issues:</h4>`;
    html += results.map((issue, index) => `
      <div class="issue-card ${issue.severity.toLowerCase()}">
        <p><strong>#${index + 1} ${issue.ruleId}</strong> — <span class="severity">${issue.severity}</span></p>
        <p><strong>Description:</strong> ${issue.message}</p>
        <p><strong>Line:</strong> ${issue.line}</p>
        <pre class="code-block">${issue.code}</pre>
      </div>
    `).join('');
  }

  document.getElementById('result').innerHTML = html;
}

  function showDownloadButton() {
    let existingBtn = document.getElementById('download-button');
    if (!existingBtn) {
      const btn = document.createElement('button');
      btn.id = 'download-button';
      btn.textContent = 'Download Result';
      btn.className = 'download-btn';
      btn.addEventListener('click', () => {
        if (!lastResult) return;
        const blob = new Blob([JSON.stringify(lastResult, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${lastResult.filename || 'result'}.json`;
        a.click();
        URL.revokeObjectURL(url);
      });
      resultSection.appendChild(btn);
    }
  }
});
const uploadedFile = document.getElementById("fileInput").files[0];
const formData = new FormData();
formData.append("file", uploadedFile); // ✅ Key must be "file"

fetch("/analyze", {
  method: "POST",
  body: formData
})
.then(res => res.json())
.then(data => {
  console.log("📦 ESLint results:", data.results);
  renderResult(data);
})
.catch(err => {
  console.error("❌ Upload failed:", err);
});