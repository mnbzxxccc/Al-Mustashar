import os

file_path = r"e:\Kronos-master\webui\templates\index.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add Navigation Link in Header (if it was just a h1, we add a nav)
header_old = "<h1>Kronos Financial Hub</h1>"
header_new = """<div class="header-nav" style="display: flex; justify-content: space-between; align-items: center; width: 100%; max-width: 1200px; margin: 0 auto; padding: 10px 0;">
            <h1 style="margin:0;">Kronos Financial Hub</h1>
            <nav>
                <a href="/" style="color: white; margin-right: 20px; text-decoration: none; font-weight: bold; border-bottom: 2px solid white;">📊 Analysis Hub</a>
                <a href="/portfolio" style="color: rgba(255,255,255,0.7); text-decoration: none; font-weight: bold;">💼 Portfolio Lab</a>
            </nav>
        </div>"""

if "header-nav" not in content:
    content = content.replace(header_old, header_new)

# 2. Expand Stats Panel with Volatility and Sortino
stats_old = """                <!-- AI Intelligence Stats (Confidence, Sentiment, Sharpe) -->
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
                </div>"""

stats_new = """                <!-- AI Intelligence Stats (Expanded Phase 2) -->
                <div id="ai-stats-container" style="display: none; flex-direction: column; gap: 15px; margin-bottom: 20px;">
                    <div style="display: flex; gap: 15px;">
                        <div style="flex: 1; background: #1e293b; color: white; padding: 15px; border-radius: 8px; text-align: center; border-bottom: 4px solid #6366f1;">
                            <h4 style="margin: 0; color: #a5b4fc; font-size: 0.9em;">AI Confidence Score</h4>
                            <div id="confidence-score" style="font-size: 2em; font-weight: bold; margin-top: 5px;">--%</div>
                        </div>
                        <div style="flex: 1; background: #1e293b; color: white; padding: 15px; border-radius: 8px; text-align: center; border-bottom: 4px solid #10b981;">
                            <h4 style="margin: 0; color: #6ee7b7; font-size: 0.9em;">Market Sentiment</h4>
                            <div id="sentiment-icon" style="font-size: 1.3em; margin-top: 5px;">--</div>
                            <div id="sentiment-text" style="font-weight: bold; font-size: 0.9em;">--</div>
                        </div>
                    </div>
                    <div style="display: flex; gap: 15px;">
                        <div style="flex: 1; background: #1e293b; color: #f8fafc; padding: 12px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; border-left: 4px solid #f59e0b;">
                            <span style="opacity: 0.8;">Sharpe Ratio (Risk/Return)</span>
                            <span id="sharpe-ratio" style="font-weight: bold; font-size: 1.2em;">--</span>
                        </div>
                        <div style="flex: 1; background: #1e293b; color: #f8fafc; padding: 12px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; border-left: 4px solid #ec4899;">
                            <span style="opacity: 0.8;">GARCH Volatility (Institutional)</span>
                            <span id="garch-vol" style="font-weight: bold; font-size: 1.2em; color: #f472b6;">--%</span>
                        </div>
                        <div style="flex: 1; background: #1e293b; color: #f8fafc; padding: 12px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; border-left: 4px solid #3b82f6;">
                            <span style="opacity: 0.8;">Sortino Ratio (Downside)</span>
                            <span id="sortino-ratio" style="font-weight: bold; font-size: 1.2em; color: #60a5fa;">--</span>
                        </div>
                    </div>
                </div>"""

content = content.replace(stats_old, stats_new)

# 3. Update JS Logic to populate new fields
js_pop_old = """                                // Show AI Stats
                                document.getElementById('ai-stats-container').style.display = 'flex';
                                document.getElementById('confidence-score').innerText = response.data.confidence + "%";
                                document.getElementById('sentiment-icon').innerText = response.data.sentiment.icon;
                                document.getElementById('sentiment-text').innerText = response.data.sentiment.status + " | " + response.data.sentiment.desc;
                                document.getElementById('sharpe-ratio').innerText = response.data.sharpe;"""

js_pop_new = """                                // Show AI Stats
                                document.getElementById('ai-stats-container').style.display = 'flex';
                                document.getElementById('confidence-score').innerText = response.data.confidence + "%";
                                document.getElementById('sentiment-icon').innerText = response.data.sentiment.icon;
                                document.getElementById('sentiment-text').innerText = response.data.sentiment.status + " | " + response.data.sentiment.desc;
                                document.getElementById('sharpe-ratio').innerText = response.data.sharpe;
                                document.getElementById('garch-vol').innerText = response.data.garch_vol;
                                document.getElementById('sortino-ratio').innerText = response.data.sortino;"""

content = content.replace(js_pop_old, js_pop_new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("index.html successfully updated for Phase 2.")
