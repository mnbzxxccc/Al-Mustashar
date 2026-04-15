# 💎 Valdis Intelligence Dashboard (ISX Edition)

![Valdis Dashboard](https://img.shields.io/badge/Status-Active-brightgreen) ![License-MIT](https://img.shields.io/badge/License-MIT-blue) ![Python](https://img.shields.io/badge/Python-3.10+-yellow)

### [English Description Below](#english) | [الوصف العربي بالأسفل](#arabic)

---

<a name="arabic"></a>
## 🇮🇶 الوصف المالي (باللغة العربية)

**مشروع Valdis ISX:** هو منصة ذكاء اصطناعي متطورة مخصصة لتحليل سوق العراق للأوراق المالية. يعتمد النظام على محرك Kronos المطور لتقديم توصيات استثمارية مبنية على دمج التحليل الفني، الأساسي، وعوامل الاقتصاد الكلي كالنفط وسعر صرف الدولار. يوفر المشروع مساعداً ذكياً (RAG Copilot) وواجهة عصرية لإدارة المحافظ، مع الالتزام الكامل بحقوق المصدر المفتوح للمطورين الأصليين.

### المميزات الرئيسية:
*   **🤖 مساعد ذكي (Copilot):** دردشة تفاعلية تفهم بيانات السوق وترد على استفسارات المستثمرين.
*   **📊 محرك تحليل مؤسسي:** تقييم شامل للأسهم (شراء/بيع) بناءً على الميزانيات والتحليل الفني.
*   **🗄️ قاعدة بيانات Nucleus:** تحتوي على أكثر من 60,000 سجل حقيقي للشركات العراقية.
*   **🔗 ربط العوامل الخارجية:** مراقبة تأثير أسعار النفط العالمية وسعر صرف الدينار على الأسهم.

---

<a name="english"></a>
## 🌐 English Description

**Valdis ISX Project:** An institutional-grade financial intelligence platform specifically engineered for the **Iraq Stock Exchange (ISX)**. The system utilizes an enhanced Kronos-based engine to provide investment recommendations by merging Technical and Fundamental analysis with Macro-economic factors like global Oil prices and USD/IQD parallel market rates. It features a context-aware AI Copilot and a modern Portfolio management interface, while fully adhering to the open-source credits of the original developers.

### Key Features:
*   **🤖 AI Copilot (RAG-Enabled):** A chat assistant that understands market data and provides deep insights.
*   **📊 Institutional Scored Engine:** Comprehensive stock scoring (BUY/SELL) based on balance sheets and technical setups.
*   **🗄️ Enhanced Nucleus DB:** Pre-populated with 60,000+ real records from Iraqi listed companies.
*   **🔗 Macro Integration:** Real-time correlation tracking between Global Oil, Currency rates, and stock performance.

---

## 🛠️ Project Structure
```text
Kronos-master/
├── isx_data_hub/          # Database Core & Analysis Engine
├── webui/                 # Flask Backend & UI
│   ├── core_analytics/    # Quantitative logic (Risk, Indicators, Optimizer)
│   ├── static/            # CSS & JavaScript
│   └── templates/         # UI Components
└── model/                 # LLM Logic
```

---

## 🚦 Getting Started
1. **Install Dependencies:** `pip install -r webui/requirements.txt`
2. **Run Server:** `cd webui; python run.py`
3. **Access UI:** `http://localhost:7070`

---

## 📝 Ethical Credits
This project is an enhanced branch of the original **[Kronos AI Framework](https://github.com/NeoQuasar/Kronos)** by **NeoQuasar**. We have heavily customized it for the Iraqi market, adding the Analysis Engine, Macro Factor integration, and an Iraqi-specific database structure.

---

## ⚖️ License
Licensed under the **MIT License**.

**Developed with ❤️ for the Iraqi Investor.**
