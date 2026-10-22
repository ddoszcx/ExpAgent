# 🛠️ ExpAgent: План реализации и разделение задач

> **Документ:** Детальный план разработки проекта ExpAgent с разбивкой на спринты, конкретные задачи и распределение между двумя участниками.
>
> **Связанный документ:** [AB_Testing_Platform_Specification.md](file:///Users/zelzel/Desktop/AB_Testing_Platform_Specification.md) — полная спецификация продукта.

---

## 1. Роли участников

### 👤 Участник A — «Stats & Data Engineer» (Аналитик)
**Профиль:** Сильная статистика, SQL, Python (pandas, scipy, numpy).
**Зона ответственности:**
- Все статистические инструменты (Tools).
- Генератор синтетических данных и Trap Suite (20 ловушек).
- SQL-шаблоны для извлечения user-level данных.
- Юнит-тесты математической корректности.

### 👤 Участник B — «LLM & Infra Engineer» (Инженер)
**Профиль:** Python, API, работа с LLM, базами данных, интерфейсами.
**Зона ответственности:**
- Харнесс агента (оркестрация, Tool Calling, системный промпт).
- Коннекторы к базам данных (DuckDB, ClickHouse).
- Streamlit-интерфейс (чат, дашборд аудита, SQL-лог).
- Интеграционные тесты (агент + Tools + данные).

---

## 2. Обзор спринтов

```
┌─────────────────────────────────────────────────────────────────────┐
│  Спринт 0 (1 день)     Настройка проекта и окружения               │
│  Спринт 1 (3–4 дня)    Статистические Tools + Генератор данных      │
│  Спринт 2 (3–4 дня)    LLM-харнесс + Коннекторы к данным           │
│  Спринт 3 (3–4 дня)    Trap Suite + Интеграция агента с Tools       │
│  Спринт 4 (2–3 дня)    Streamlit UI + Audit Dashboard              │
│  Спринт 5 (2–3 дня)    Полировка, README, деплой                   │
└─────────────────────────────────────────────────────────────────────┘
  Общая оценка: 14–18 рабочих дней (≈ 3–4 недели при неполной загрузке)
```

---

## 3. Спринт 0: Настройка проекта (1 день)

**Выполняется совместно.**

### Задачи:

| # | Задача | Кто | Результат |
|:--|:---|:--:|:---|
| 0.1 | Создать репозиторий на GitHub, настроить `.gitignore`, `README.md` (заглушка), ветки `main` / `dev` | B | Готовый пустой репозиторий |
| 0.2 | Создать структуру папок по спецификации (`tools/`, `harness/`, `db/`, `trap_suite/`, `tests/`) | B | Каркас директорий с `__init__.py` |
| 0.3 | Составить `requirements.txt` | A+B | Зафиксированные версии зависимостей |
| 0.4 | Настроить виртуальное окружение (venv / conda), убедиться, что всё ставится | A+B | Рабочее окружение у обоих участников |

### Содержимое `requirements.txt`:
```
# Статистика и данные
numpy>=1.24
scipy>=1.11
statsmodels>=0.14
pandas>=2.0

# Базы данных
duckdb>=0.9
clickhouse-connect>=0.7

# LLM
openai>=1.30

# Интерфейс
streamlit>=1.30
plotly>=5.18

# Тестирование
pytest>=7.4
```

---

## 4. Спринт 1: Статистические инструменты + Генератор данных (3–4 дня)

**Основной исполнитель: Участник A (Stats).**
**Участник B параллельно начинает Спринт 2.**

---

### 📦 Задача 1.1: Генератор реалистичных user-level данных
**Файл:** `db/synthetic_generator.py`
**Срок:** 1 день
**Исполнитель:** A

Функция, которая генерирует DataFrame, имитирующий выгрузку завершённого A/B-теста из базы:

```python
def generate_experiment(
    n_users: int = 10000,
    split_ratio: float = 0.5,
    metric_type: str = "revenue",     # "revenue" | "conversion" | "ratio"
    true_effect: float = 0.0,         # 0.0 = нет эффекта (A/A тест)
    has_pre_period: bool = True,
    pre_correlation: float = 0.6,
    outlier_fraction: float = 0.01,
    srm_bias: float = 0.0,           # 0.0 = честный сплит
) -> pd.DataFrame:
    """
    Возвращает DataFrame с колонками:
    - user_id: str
    - group: "control" | "treatment"
    - metric_value: float (user-level метрика за период теста)
    - pre_metric_value: float (user-level метрика за предпериод, для CUPED)
    - orders: int (для ratio-метрик: revenue / orders)
    """
```

**Требования к реализму данных:**
- Выручка: логнормальное распределение с тяжёлыми хвостами (`np.random.lognormal`).
- Конверсии: бернуллиевское распределение с baseline ~3–8%.
- Предпериод: коррелирует с тестовым периодом через копулу или линейную модель.
- Выбросы: случайные «киты» с чеком в 50–100x от медианы.

---

### 📦 Задача 1.2: Tool — SRM Check
**Файл:** `tools/srm.py`
**Срок:** 0.5 дня
**Исполнитель:** A

```python
def srm_check(
    n_control: int,
    n_treatment: int,
    expected_ratio: float = 0.5
) -> dict:
    """
    Returns:
        {
            "test": "chi_square_goodness_of_fit",
            "chi2_statistic": float,
            "p_value": float,
            "is_srm": bool,          # True если p < 0.001
            "verdict": str           # "SRM_OK" | "SRM_BROKEN"
        }
    """
```

**Порог:** `p < 0.001` (индустриальный стандарт, не 0.01).

---

### 📦 Задача 1.3: Tool — Pre-Experiment Power Analysis
**Файл:** `tools/power_analysis.py`
**Срок:** 0.5 дня
**Исполнитель:** A

```python
def pre_experiment_power(
    baseline_mean: float,
    baseline_std: float,
    mde_relative: float,       # Минимальный детектируемый эффект (%)
    n_per_group: int,
    alpha: float = 0.05,
) -> dict:
    """
    Returns:
        {
            "required_n_per_group": int,
            "actual_n_per_group": int,
            "power_at_actual_n": float,       # Мощность при текущем N
            "is_adequately_powered": bool,     # power >= 0.8?
            "days_to_adequate_power": int | None,
            "verdict": str
        }
    """
```

**Важно:** Это НЕ post-hoc power. Мы используем baseline variance и заявленный MDE, а не наблюдаемый эффект.

---

### 📦 Задача 1.4: Tool — Frequentist Tests (Welch, Z-test, Fisher)
**Файл:** `tools/frequentist_tests.py`
**Срок:** 0.5 дня
**Исполнитель:** A

```python
def welch_ttest(control_values: np.ndarray, treatment_values: np.ndarray) -> dict:
    """Для непрерывных метрик (выручка, время)."""

def proportion_ztest(
    conversions_control: int, n_control: int,
    conversions_treatment: int, n_treatment: int
) -> dict:
    """Для бинарных метрик (конверсии)."""

def fisher_exact(
    conversions_control: int, n_control: int,
    conversions_treatment: int, n_treatment: int
) -> dict:
    """Для малых выборок (< 30 конверсий)."""
```

Каждая функция возвращает: `statistic`, `p_value`, `ci_lower`, `ci_upper`, `relative_effect`, `verdict`.

---

### 📦 Задача 1.5: Tool — Delta Method (Ratio-метрики)
**Файл:** `tools/delta_method.py`
**Срок:** 0.5 дня
**Исполнитель:** A

```python
def delta_method_ratio_test(
    numerator_control: np.ndarray,     # Выручка каждого юзера
    denominator_control: np.ndarray,   # Число заказов каждого юзера
    numerator_treatment: np.ndarray,
    denominator_treatment: np.ndarray,
) -> dict:
    """
    Корректная дисперсия для ratio R = sum(Y) / sum(X):
    Var(R) ≈ (1/X̄²) * [Var(Y) - 2R·Cov(X,Y) + R²·Var(X)]

    Returns:
        {
            "ratio_control": float,
            "ratio_treatment": float,
            "delta": float,
            "se_delta": float,                 # Правильная SE через Delta Method
            "se_naive": float,                 # Наивная SE (для сравнения)
            "p_value_delta": float,
            "p_value_naive": float,
            "ci_lower": float,
            "ci_upper": float,
            "naive_would_be_significant": bool, # True = ложная победа без Delta Method
            "verdict": str
        }
    """
```

---

### 📦 Задача 1.6: Tool — CUPED (с проверкой предпосылок)
**Файл:** `tools/cuped.py`
**Срок:** 0.5 дня
**Исполнитель:** A

```python
def cuped_transform(
    metric_values: np.ndarray,           # Y (тестовый период)
    covariate_values: np.ndarray,        # X (предпериод)
    groups: np.ndarray,                  # 0/1
) -> dict:
    """
    Returns:
        {
            "theta": float,
            "correlation_xy": float,
            "variance_before": float,
            "variance_after": float,
            "variance_reduction_pct": float,      # Реально измеренное, не заявленное
            "covariate_balance_ok": bool,          # X сбалансирована между группами?
            "covariate_strength": str,             # "strong" | "moderate" | "weak"
            "adjusted_values_control": np.ndarray,
            "adjusted_values_treatment": np.ndarray,
            "warnings": list[str],
        }
    """
```

**Проверки предпосылок:**
- Если $|\rho| < 0.3$ → warning: «Слабая ковариата, CUPED даст минимальный эффект».
- Если ковариата не сбалансирована между группами → warning: «Ковариата зависит от назначения».

---

### 📦 Задача 1.7: Tool — Bootstrap
**Файл:** `tools/bootstrap.py`
**Срок:** 0.5 дня
**Исполнитель:** A

```python
def bootstrap_mean_diff(
    control: np.ndarray,
    treatment: np.ndarray,
    n_bootstrap: int = 5000,
    ci_level: float = 0.95,
    seed: int = 42,
) -> dict:
    """Векторизованный bootstrap на NumPy для разницы средних."""
```

---

### 📦 Задача 1.8: Tool — Sequential Testing (mSPRT)
**Файл:** `tools/sequential.py`
**Срок:** 0.5 дня
**Исполнитель:** A

```python
def msprt_test(
    control: np.ndarray,
    treatment: np.ndarray,
    tau_squared: float,        # Параметр mixing distribution (ширина prior)
    alpha: float = 0.05,
) -> dict:
    """
    Mixture Sequential Probability Ratio Test.
    Возвращает always-valid p-value, безопасный для многократного подглядывания.
    """
```

---

### 📦 Задача 1.9: Tool — Multiple Testing Correction
**Файл:** `tools/multiple_testing.py`
**Срок:** 0.25 дня
**Исполнитель:** A

```python
def benjamini_hochberg(p_values: list[float], alpha: float = 0.05) -> dict:
    """FDR-поправка. Возвращает скорректированные p-values и какие гипотезы выжили."""

def bonferroni(p_values: list[float], alpha: float = 0.05) -> dict:
    """Консервативная поправка для guardrail-метрик."""
```

---

### 📦 Задача 1.10: Tool — Winsorization + Revenue Calculator
**Файл:** `tools/winsorization.py`, `tools/revenue_calculator.py`
**Срок:** 0.25 дня
**Исполнитель:** A

```python
def winsorize(values: np.ndarray, percentile: float = 99.5) -> np.ndarray:
    """Обрезка выбросов по перцентилю."""

def effect_to_annual_revenue(
    relative_effect: float,
    ci_lower: float,
    ci_upper: float,
    baseline_daily_revenue: float,
) -> dict:
    """
    Расчёт годового эффекта в рублях.
    СТРОГО в Python. LLM передаёт параметры, получает готовый результат.
    """
```

---

### 📦 Задача 1.11: Tool — Bayesian A/B
**Файл:** `tools/bayesian.py`
**Срок:** 0.5 дня
**Исполнитель:** A

```python
def bayesian_binary(
    conversions_a: int, n_a: int,
    conversions_b: int, n_b: int,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    n_samples: int = 100000,
) -> dict:
    """
    Conjugate Beta-Binomial модель.
    Returns: chance_to_win_b, expected_loss_b, credible_interval
    """
```

---

## 5. Спринт 2: LLM-харнесс + Коннекторы (3–4 дня)

**Основной исполнитель: Участник B (Infra).**
**Участник A параллельно заканчивает Спринт 1.**

---

### 📦 Задача 2.1: Коннектор DuckDB (локальная демо-база)
**Файл:** `db/duckdb_local.py`
**Срок:** 0.5 дня
**Исполнитель:** B

```python
class DuckDBClient:
    def __init__(self, db_path: str = ":memory:"):
        ...

    def load_experiment(self, df: pd.DataFrame, experiment_name: str):
        """Загрузить DataFrame в DuckDB как таблицу."""

    def execute_query(self, sql: str) -> pd.DataFrame:
        """Выполнить произвольный SQL и вернуть результат."""

    def get_schema(self) -> dict:
        """Вернуть схему всех таблиц (для контекста LLM)."""
```

---

### 📦 Задача 2.2: Коннектор ClickHouse
**Файл:** `db/clickhouse_client.py`
**Срок:** 0.5 дня
**Исполнитель:** B

```python
class ClickHouseClient:
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        ...

    def execute_query(self, sql: str) -> pd.DataFrame:
        ...

    def get_schema(self) -> dict:
        """Структура таблиц для передачи в контекст LLM."""

    def test_connection(self) -> bool:
        ...
```

---

### 📦 Задача 2.3: Реестр инструментов (Tool Registry)
**Файл:** `harness/tool_registry.py`
**Срок:** 1 день
**Исполнитель:** B

Каждый Tool из Спринта 1 регистрируется в формате OpenAI Function Calling JSON Schema:

```python
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "srm_check",
            "description": "Check Sample Ratio Mismatch between control and treatment groups using Chi-square test. Threshold: p < 0.001.",
            "parameters": {
                "type": "object",
                "properties": {
                    "n_control": {
                        "type": "integer",
                        "description": "Number of users in control group"
                    },
                    "n_treatment": {
                        "type": "integer",
                        "description": "Number of users in treatment group"
                    },
                    "expected_ratio": {
                        "type": "number",
                        "description": "Expected split ratio (default 0.5)"
                    }
                },
                "required": ["n_control", "n_treatment"]
            }
        }
    },
    # ... аналогично для каждого Tool
]
```

Плюс **диспетчер**, который маппит `function_name → реальная Python-функция`:

```python
def execute_tool(name: str, arguments: dict) -> dict:
    """Вызывает нужный Tool по имени и возвращает результат."""
```

---

### 📦 Задача 2.4: Системный промпт (Parent Prompt)
**Файл:** `harness/system_prompt.py`
**Срок:** 1 день
**Исполнитель:** B

Содержимое — SOP из раздела 5 спецификации. Отдельная строковая константа `SYSTEM_PROMPT`, которая передаётся в `messages[0]` при вызове LLM.

Включает:
- Роль агента.
- Протокол аудита (SRM → Power → CUPED → Test → Multiple Corrections → Verdict).
- Список запретов (нет post-hoc power, нет арифметики в голове, нет MWU для средних).
- Формат ответа (структурированный Markdown с флагами).

---

### 📦 Задача 2.5: Agent Core (ReAct Loop)
**Файл:** `harness/agent.py`
**Срок:** 1.5 дня
**Исполнитель:** B

```python
class ExperimentAuditAgent:
    def __init__(
        self,
        llm_client,            # OpenAI-совместимый клиент
        db_client,             # DuckDB или ClickHouse
        tool_registry,
        system_prompt: str,
    ):
        ...

    def audit_experiment(self, experiment_name: str) -> AuditResult:
        """
        Полный цикл аудита одного эксперимента:
        1. LLM генерирует SQL для извлечения данных.
        2. SQL выполняется и логируется.
        3. LLM вызывает Tools по протоколу SOP.
        4. Формируется структурированный вердикт.
        """

    def audit_program(self, experiment_names: list[str]) -> ProgramAuditReport:
        """Аудит всей программы экспериментов с суммарным отчётом."""
```

**Ключевые моменты реализации:**
- Все сгенерированные SQL-запросы сохраняются в `audit_log`.
- Каждый вызов Tool логируется с входными параметрами и результатом.
- LLM вызывается через стандартный OpenAI `chat.completions.create` с `tools=TOOL_DEFINITIONS`.
- ReAct loop: LLM думает → вызывает Tool → получает результат → думает → вызывает следующий Tool → ... → формирует финальный ответ.

---

## 6. Спринт 3: Trap Suite + Интеграция (3–4 дня)

**Участник A:** Создаёт 20 ловушек.
**Участник B:** Интегрирует агента с Tools и пишет тесты.

---

### 📦 Задача 3.1: Trap Suite — 20 синтетических экспериментов
**Папка:** `trap_suite/traps/`
**Срок:** 2–3 дня
**Исполнитель:** A

Каждая ловушка — это отдельный файл с функцией `generate() -> dict`:

| # | Файл | Ловушка | Правильный вердикт |
|:--|:---|:---|:---|
| 01 | `clean_win.py` | Чистая победа, всё корректно | `CLEAN_WIN` |
| 02 | `peeking_false_win.py` | Тест остановлен на 3-й день при p=0.04 | `FALSE_WIN: PEEKING` |
| 03 | `srm_broken.py` | Сплит 10000 vs 8700 | `INVALID: SRM_BROKEN` |
| 04 | `ratio_no_delta.py` | revenue/orders без Delta Method | `FALSE_WIN: RATIO_NO_DELTA` |
| 05 | `multiple_metrics_no_fdr.py` | 8 метрик, 1 "значима" | `FALSE_WIN: NO_FDR_CORRECTION` |
| 06 | `underpowered_lucky.py` | N=500, MDE нужен 5%, "нашли" 12% | `UNRELIABLE: UNDERPOWERED` |
| 07 | `outlier_driven.py` | Эффект держится на 3 китах | `UNRELIABLE: OUTLIER_DRIVEN` |
| 08 | `cuped_bad_covariate.py` | CUPED с $\rho = 0.1$ | `WARNING: WEAK_CUPED` |
| 09 | `mwu_for_revenue.py` | MWU для разницы средних чеков | `METHODOLOGICAL_ERROR` |
| 10 | `clean_loss.py` | Чистый проигрыш, корректная статистика | `CLEAN_LOSS` |
| 11 | `novelty_effect.py` | Эффект затухает к концу теста | `WARNING: NOVELTY_EFFECT` |
| 12 | `simpsons_paradox.py` | Общий эффект +, но в каждом сегменте – | `WARNING: SIMPSONS_PARADOX` |
| 13 | `contaminated_control.py` | Часть treatment-юзеров в control | `INVALID: CONTAMINATION` |
| 14 | `bot_traffic.py` | 15% ботов раздули конверсию | `UNRELIABLE: BOT_TRAFFIC` |
| 15 | `aa_false_positive.py` | A/A тест, который "нашёл" p=0.03 | `FALSE_WIN: AA_TEST` |
| 16 | `three_variants_no_correction.py` | A/B/C, лучший выбран без поправки | `FALSE_WIN: NO_MULTIVAR_CORRECTION` |
| 17 | `sequential_correct.py` | mSPRT ранняя остановка, всё ок | `CLEAN_WIN` |
| 18 | `extreme_skew_revenue.py` | Логнормальная выручка, нужен bootstrap | `NEEDS_BOOTSTRAP` |
| 19 | `cuped_correct_strong.py` | CUPED с $\rho = 0.7$, работает | `CLEAN_WIN` |
| 20 | `mixed_issues.py` | SRM + ratio + 3 метрики | `INVALID: MULTIPLE_ISSUES` |

**Файл ожидаемых ответов:** `trap_suite/expected_verdicts.json`

---

### 📦 Задача 3.2: Интеграция Agent ↔ Tools
**Срок:** 1 день
**Исполнитель:** B

- Подключить все Tools из Спринта 1 к реестру из Задачи 2.3.
- Убедиться, что LLM корректно вызывает каждый Tool и получает результат.
- Протестировать полный цикл: загрузка данных в DuckDB → агент генерирует SQL → вызывает Tools → формирует отчёт.

---

### 📦 Задача 3.3: Тест Trap Suite
**Файл:** `tests/test_trap_detection.py`
**Срок:** 1 день
**Исполнитель:** B (с ревью от A)

```python
@pytest.mark.parametrize("trap_name, expected", load_expected_verdicts())
def test_agent_detects_trap(trap_name, expected):
    """
    Для каждой из 20 ловушек:
    1. Генерируем данные.
    2. Загружаем в DuckDB.
    3. Запускаем агента.
    4. Проверяем, что вердикт совпадает с ожидаемым.
    """
```

---

## 7. Спринт 4: Streamlit UI (2–3 дня)

**Основной исполнитель: Участник B.**
**Участник A:** Пишет юнит-тесты, документирует формулы.

---

### 📦 Задача 4.1: Главный интерфейс
**Файл:** `app.py`
**Срок:** 2 дня
**Исполнитель:** B

**Макет интерфейса:**

```
┌─────────────────────────────────────────────────────────────┐
│  ExpAgent — Experiment Audit Agent                          │
│                                                             │
│  ┌─── Sidebar ────────────────────────────────┐             │
│  │ Data Source:                                │             │
│  │  ○ Demo (DuckDB)                           │             │
│  │  ○ Upload CSV                              │             │
│  │  ○ ClickHouse (host, port, db)             │             │
│  │                                            │             │
│  │ [▶ Run Full Audit]                         │             │
│  │ [▶ Run Trap Suite Test]                    │             │
│  └────────────────────────────────────────────┘             │
│                                                             │
│  ┌─── Main Area ──────────────────────────────────────────┐ │
│  │                                                        │ │
│  │  Tab 1: CHAT WITH AGENT                                │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │ User: Проверь тест exp_new_checkout               │  │ │
│  │  │ Agent: Загружаю данные...                         │  │ │
│  │  │        SQL: SELECT user_id, ...                   │  │ │
│  │  │        [Tool Call: srm_check] → SRM OK            │  │ │
│  │  │        [Tool Call: power_analysis] → 92%          │  │ │
│  │  │        [Tool Call: welch_ttest] → p=0.021         │  │ │
│  │  │        ✅ CLEAN WIN: effect +3.2% [1.1%, 5.3%]   │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  │                                                        │ │
│  │  Tab 2: AUDIT DASHBOARD (результат аудита программы)   │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │  ✅ Clean wins: 31  ⚠️ Questionable: 24          │  │ │
│  │  │  ❌ False wins: 14  ➖ Inconclusive: 18           │  │ │
│  │  │  Claimed: +23.4%  →  Adjusted: +7.1%             │  │ │
│  │  │                                                    │  │ │
│  │  │  [Таблица по экспериментам с флагами]              │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  │                                                        │ │
│  │  Tab 3: SQL LOG (все запросы агента для верификации)    │ │
│  │  Tab 4: TRAP SUITE RESULTS (19/20 ловушек пойманы)     │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

### 📦 Задача 4.2: Юнит-тесты математики
**Файл:** `tests/test_tools_math.py`
**Срок:** 1 день
**Исполнитель:** A

```python
def test_srm_detects_broken_split():
    """10000 vs 8700 при ожидаемом 50/50 → SRM_BROKEN."""

def test_srm_passes_clean_split():
    """10000 vs 9950 → SRM_OK."""

def test_delta_method_catches_false_significance():
    """Ratio-метрика: наивный t-test = significant, delta = not significant."""

def test_cuped_reduces_variance():
    """При rho=0.7 дисперсия должна снизиться примерно на 49%."""

def test_cuped_warns_weak_covariate():
    """При rho=0.1 должен вернуть warning."""

def test_benjamini_hochberg_kills_false_discoveries():
    """10 p-values, 1 чуть ниже 0.05 → после BH не значим."""

def test_msprt_always_valid():
    """Always-valid p-value не падает ниже alpha при A/A тесте с подглядыванием."""

def test_bootstrap_ci_covers_true_effect():
    """95% CI должен покрывать истинный эффект в >93% случаев (при 100 симуляциях)."""
```

---

## 8. Спринт 5: Полировка и README (2–3 дня)

**Выполняется совместно.**

| # | Задача | Кто | Срок |
|:--|:---|:--:|:--:|
| 5.1 | Написать полноценный `README.md` с архитектурой, примерами запуска и результатами Trap Suite | A+B | 1 день |
| 5.2 | Записать GIF / скринкаст работы агента для README | B | 0.5 дня |
| 5.3 | Деплой на Streamlit Cloud (если возможно) или инструкция по локальному запуску | B | 0.5 дня |
| 5.4 | Code review, рефакторинг, docstrings | A+B | 1 день |
| 5.5 | Финальный прогон всех тестов (pytest + Trap Suite) | A+B | 0.5 дня |

---

## 9. Сводная таблица: Кто что делает

### Участник A (Stats & Data Engineer):

| Спринт | Задачи | Дней |
|:--|:---|:--:|
| 0 | Совместная настройка | 0.5 |
| 1 | Генератор данных + 12 статистических Tools | 3–4 |
| 3 | 20 ловушек Trap Suite | 2–3 |
| 4 | Юнит-тесты математики | 1 |
| 5 | README, ревью | 1 |
| | **Итого:** | **7.5–9.5** |

### Участник B (LLM & Infra Engineer):

| Спринт | Задачи | Дней |
|:--|:---|:--:|
| 0 | Совместная настройка, репозиторий | 0.5 |
| 2 | DB коннекторы + Tool Registry + System Prompt + Agent Core | 3–4 |
| 3 | Интеграция Agent↔Tools, тест Trap Suite | 2 |
| 4 | Streamlit UI (чат + дашборд + SQL-лог) | 2–3 |
| 5 | Деплой, GIF, ревью | 1.5 |
| | **Итого:** | **9–11** |

---

## 10. Зависимости между задачами (что от чего зависит)

```
Спринт 0 (совместно)
    │
    ├───► Спринт 1 (A: Tools)  ────────────────┐
    │                                           │
    └───► Спринт 2 (B: Harness + DB)           │
              │                                 │
              │         ◄──────────────────────┘
              ▼                (Tools готовы)
         Спринт 3 (A: Trap Suite)
         Спринт 3 (B: Интеграция + тесты)
              │
              ▼
         Спринт 4 (B: UI  |  A: Юнит-тесты)
              │
              ▼
         Спринт 5 (совместно: README + деплой)
```

**Критический путь:** Спринты 1 и 2 идут **параллельно**. Спринт 3 начинается, когда оба завершены. Это самая эффективная загрузка двух людей.
