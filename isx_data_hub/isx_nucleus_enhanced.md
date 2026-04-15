# تصميم قاعدة البيانات المحسنة: ISX Nucleus Enhanced 🗄️

لتوفير طبقة بيانات قوية لمحرك الذكاء الاصطناعي (Kronos) ونظام التحليل، قمنا بتوسيع قاعدة البيانات لتشمل 10 جداول رئيسية مترابطة.

## 1. جدول `companies` (الشركات)
يحتوي على البيانات الأساسية للشركة.
- `id`: المعرف الفريد.
- `symbol`: رمز الشركة في السوق.
- `name`: اسم الشركة.
- `sector`: القطاع.

## 2. جدول `prices` (الأسعار اليومية)
البيانات لتغذية نماذج التنبوء وتحليل الشارت.
- `date`, `open`, `high`, `low`, `close`, `volume`, `amount`
**التحسين:** وضع Indexes على `company_id` و `date` لتسريع البحث الزمني.

## 3. جدول `macro_factors` (العوامل الاقتصادية الكلية)
لأن السوق العراقي يتأثر بالعوامل الكلية.
- `date`: التاريخ.
- `oil_price_bbl`: سعر برميل النفط.
- `usd_iqd_parallel`: سعر صرف الدولار الموازي.
- `cbi_rate`: سعر مزاد البنك المركزي.

## 4. جدول `financial_statements` (البيانات المالية)
أساس التحليل الأساسي (Fundamental Analysis).
- `company_id`, `year`, `quarter`
- `revenue`, `net_income`, `total_assets`, `total_liabilities`, `total_equity`, `operating_cash_flow`, `free_cash_flow`
- `shares_outstanding`

## 5. جدول `financial_ratios` (النسب المالية - محسوبة تلقائياً)
- `company_id`, `year`, `quarter`
- `pe_ratio` (مكرر الربحية), `pb_ratio` (مضاعف القيمة الدفترية)
- `roe` (العائد على حقوق الملكية), `roa` (العائد على الأصول)
- `debt_to_equity`, `current_ratio`

## 6. جدول `technical_indicators` (المؤشرات الفنية)
لحساب إشارات التداول لجميع الأسهم يومياً.
- `company_id`, `date`
- `rsi_14`, `macd_line`, `macd_signal`, `macd_hist`
- `bollinger_upper`, `bollinger_lower`
- `sma_50`, `sma_200`

## 7. جدول `dividends` (التوزيعات النقدية)
العوائد التي يحصل عليها المستثمر لتحديد ربحية السهم الحقيقية.
- `company_id`, `ex_dividend_date`, `payment_date`
- `amount_per_share`: التوزيع لكل سهم.
- `dividend_yield`: عائد التوزيع.

## 8. جدول `news` و `company_status` (الأخبار والحالة)
مصادر البيانات لنموذج (RAG / AI Sentiment analysis).

## 9. جدول `stakeholders` (كبار الملاك)
لتتبع حركة ملكية كبار المستثمرين وعمليات الشراء الداخلي (Insider trading).

## 10. جدول `ai_predictions` (توقعات الذكاء الاصطناعي)
لتسجيل توقعات Kronos ومقارنتها بالواقع لاحقاً (Backtesting) للتدريب المستمر للنموذج.
- `company_id`, `prediction_date`, `target_date`, `predicted_close`, `confidence_score`
