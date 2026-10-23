

# 🔬 ExpAgent: AI Copilot for A/B Experiment Audit

ExpAgent — автономный агент для ретроспективного аудита и математической валидации программы A/B-тестирования.

## 🚀 Ключевые возможности

- **SRM Detection:** автоматическая проверка Sample Ratio Mismatch ($\chi^2$-тест).
- **Sequential Testing & Peeking:** защита от преждевременной остановки (mSPRT / GOR).
- **Ratio Metrics:** корректный расчёт дисперсии через Delta Method.
- **Variance Reduction:** CUPED с автоматической проверкой предпосылок.
- **Outlier Robustness:** автоматическая винсоризация и расчёт бизнес-эффекта в деньгах.
- **Trap Suite:** бенчмарк на 20 синтетических тестах с заложенными ошибками планирования и анализа.

## 👥 Команда

- **Participant A:** Stats & Data Modeling (Tools, Trap Suite, Math validation)
- **Participant B:** LLM & Infra Engineering (Agent Harness, DB Connectors, UI)

## 🛠️ Быстрый старт

```bash
# 1. Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Скопировать конфиг
cp .env.example .env
```
