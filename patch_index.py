import os

file_path = r"e:\Kronos-master\webui\templates\index.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Inject HTML2PDF library
head_injection = """    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
"""
if "html2pdf.bundle.min.js" not in content:
    content = content.replace("</style>", "</style>\n" + head_injection)

# 2. Add Export PDF Button in chart-header (if it exists, if not we create it)
# Actually, the user's template doesn't explicitly show chart-header around line 588. Let's look at the h2 chart title.
h2_old = "<h2>📈 Prediction Results & Analytics</h2>"
h2_new = """<div style="display: flex; justify-content: space-between; align-items: center;">
                    <h2>📈 Prediction Results & Analytics</h2>
                    <button class="btn btn-secondary" onclick="exportToPDF()" style="background-color: #3b82f6; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer;">
                        📑 Export PDF Report
                    </button>
                </div>"""
content = content.replace(h2_old, h2_new)

# 3. Add Confidence and Sentiment Panel above Rationale
rationale_old = "<!-- Financial Rationale Panel -->"
rationale_new = """<!-- AI Intelligence Stats (Confidence, Sentiment, Sharpe) -->
                <div id="ai-stats-container" style="display: none; display: flex; gap: 20px; margin-bottom: 20px;">
                    <div style="flex: 1; background: #1e293b; color: white; padding: 15px; border-radius: 8px; text-align: center; border-bottom: 4px solid #6366f1;">
                        <h4 style="margin: 0; color: #a5b4fc; font-size: 0.9em;">AI Confidence Score</h4>
                        <div id="confidence-score" style="font-size: 2em; font-weight: bold; margin-top: 10px;">--%</div>
                    </div>
                    <div style="flex: 1; background: #1e293b; color: white; padding: 15px; border-radius: 8px; text-align: center; border-bottom: 4px solid #10b981;">
                        <h4 style="margin: 0; color: #6ee7b7; font-size: 0.9em;">Market Sentiment</h4>
                        <div id="sentiment-icon" style="font-size: 1.5em; margin-top: 5px;">--</div>
                        <div id="sentiment-text" style="font-weight: bold; margin-top: 5px;">--</div>
                    </div>
                    <div style="flex: 1; background: #1e293b; color: white; padding: 15px; border-radius: 8px; text-align: center; border-bottom: 4px solid #f59e0b;">
                        <h4 style="margin: 0; color: #fcd34d; font-size: 0.9em;">Sharpe Ratio</h4>
                        <div id="sharpe-ratio" style="font-size: 2em; font-weight: bold; margin-top: 10px;">--</div>
                    </div>
                </div>
                
                <!-- Financial Rationale Panel -->"""
content = content.replace(rationale_old, rationale_new, 1)

# 4. Bind the javascript updates in startPrediction handler
js_old = """                            if (response.data.rationale) {
                                document.getElementById('rationale-container').style.display = 'block';
                                document.getElementById('rationale-content').innerHTML = response.data.rationale;
                            } else {
                                document.getElementById('rationale-container').style.display = 'none';
                            }"""

js_new = """                            if (response.data.rationale) {
                                document.getElementById('rationale-container').style.display = 'block';
                                document.getElementById('rationale-content').innerHTML = response.data.rationale;
                                
                                // Show AI Stats
                                document.getElementById('ai-stats-container').style.display = 'flex';
                                document.getElementById('confidence-score').innerText = response.data.confidence + "%";
                                document.getElementById('sentiment-icon').innerText = response.data.sentiment.icon;
                                document.getElementById('sentiment-text').innerText = response.data.sentiment.status + " | " + response.data.sentiment.desc;
                                document.getElementById('sharpe-ratio').innerText = response.data.sharpe;
                            } else {
                                document.getElementById('rationale-container').style.display = 'none';
                                document.getElementById('ai-stats-container').style.display = 'none';
                            }"""
content = content.replace(js_old, js_new)

# 5. Add Export to PDF function at the end
pdf_script = """        function exportToPDF() {
            const element = document.querySelector('.chart-container');
            const opt = {
              margin:       10,
              filename:     'ISX_Kronos_Report_' + (currentDataFile || 'report') + '.pdf',
              image:        { type: 'jpeg', quality: 0.98 },
              html2canvas:  { scale: 2 },
              jsPDF:        { unit: 'mm', format: 'a4', orientation: 'landscape' }
            };
            
            showStatus('info', 'Generating PDF report...');
            html2pdf().from(element).set(opt).save().then(() => showStatus('success', 'PDF Downloaded!'));
        }
    </script>
</body>"""

# First, replace "</body>" if it has the script tag directly above
content = content.replace("    </script>\n</body>", pdf_script)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("index.html successfully updated.")
