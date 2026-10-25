from scipy.stats import alpha
TOOL_DEFINITIONS = [
    # 1. работа с базой данных
    {
        "type": "function",
        "function": {
            "name": "run_sql_query",
            "description": "Выполняет SQL-запрос в аналитической базе данных (DuckDB/ClickHouse) и возвращает результат в виде строк. Используй для подсчета размеров групп, конверсий, средних и дисперсий.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL-запрос. Зарезервированные слова экранируй в двойные кавычки: \"group\", \"order\", \"user\"."
                    }
                },
                "required": ["sql"]
            }
        }
    },

    # 2. проверка гигиены данных (data quality & integrity)
    {
        "type": "function",
        "function": {
            "name": "srm_check",
            "description": "Проверяет Sample Ratio Mismatch (SRM) через критерий согласия хи-квадрат Пирсона. Порог нарушения: p < 0.001. При нарушении доверие к эксперименту полностью теряется.",
            "parameters": {
                "type": "object",
                "properties": {
                    "n_control": {
                        "type": "integer",
                        "description": "Фактическое число уникальных пользователей в контрольной группе (A)"
                    },
                    "n_treatment": {
                        "type": "integer",
                        "description": "Фактическое число уникальных пользователей в тестовой группе (B)"
                    },
                    "expected_ratio": {
                        "type": "number",
                        "description": "Ожидаемая доля контроля в сплите (по умолчанию 0.5 для сплита 50/50)"
                    }
                },
                "required": ["n_control", "n_treatment"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "data_quality_check",
            "description": "Проверяет целостность данных: наличие дубликатов, пользователей в обеих группах одновременно (cross-assignment) и завершенность окон конверсии.",
            "parameters": {
                "type": "object",
                "properties": {
                    "total_users": {
                        "type": "integer",
                        "description": "Общее число залогированных пользователей"
                    },
                    "cross_assigned_users": {
                        "type": "integer",
                        "description": "Число пользователей, зафиксированных одновременно в контроле и тесте"
                    },
                    "duplicate_users": {
                        "type": "integer",
                        "description": "Число дублирующихся строк логов по одному и тому же пользователю"
                    },
                    "immature_users_ratio": {
                        "type": "number",
                        "description": "Доля пользователей, у которых окно наблюдения еще не закрылось (от 0.0 до 1.0)"
                    }
                },
                "required": ["total_users", "cross_assigned_users"]
            }
        }
    },

    # 3. статистические тесты (параметрические и непараметрические)
    {
        "type": "function",
        "function": {
            "name": "proportion_ztest",
            "description": "Двусторонний Z-тест разности долей для бинарных метрик (конверсия в покупку, кликабельность, retention). Возвращает p-value, CI и относительный эффект.",
            "parameters": {
                "type": "object",
                "properties": {
                    "conversions_control": {
                        "type": "integer",
                        "description": "Количество успешных конверсий в контроле"
                    },
                    "n_control": {
                        "type": "integer",
                        "description": "Всего участников в контроле (включая тех, кто не совершил действие!)"
                    },
                    "conversions_treatment": {
                        "type": "integer",
                        "description": "Количество успешных конверсий в тесте"
                    },
                    "n_treatment": {
                        "type": "integer",
                        "description": "Всего участников в тесте (включая тех, кто не совершил действие!)"
                    },
                    "alpha": {
                        "type": "number",
                        "description": "Уровень значимости (по умолчанию 0.05)"
                    }
                },
                "required": ["conversions_control", "n_control", "conversions_treatment", "n_treatment"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fisher_exact",
            "description": "Точный тест Фишера для малых выборок. Вызывай ВМЕСТО proportion_ztest, если число конверсий в любой из групп меньше 30.",
            "parameters": {
                "type": "object",
                "properties": {
                    "conversions_control": {
                        "type": "integer",
                        "description": "Количество конверсий в контроле"
                    },
                    "n_control": {
                        "type": "integer",
                        "description": "Всего участников в контроле"
                    },
                    "conversions_treatment": {
                        "type": "integer",
                        "description": "Количество конверсий в тесте"
                    },
                    "n_treatment": {
                        "type": "integer",
                        "description": "Всего участников в тесте"
                    }
                },
                "required": ["conversions_control", "n_control", "conversions_treatment", "n_treatment"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "welch_ttest",
            "description": "t-критерий Уэлча для сравнения непрерывных метрик на пользователя (выручка на юзера RPV, время сессии). Не требует равенства дисперсий групп.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mean_control": {
                        "type": "number",
                        "description": "Выборочное среднее метрики в контроле"
                    },
                    "std_control": {
                        "type": "number",
                        "description": "Выборочное стандартное отклонение в контроле"
                    },
                    "n_control": {
                        "type": "integer",
                        "description": "Количество пользователей в контроле"
                    },
                    "mean_treatment": {
                        "type": "number",
                        "description": "Выборочное среднее метрики в тесте"
                    },
                    "std_treatment": {
                        "type": "number",
                        "description": "Выборочное стандартное отклонение в тесте"
                    },
                    "n_treatment": {
                        "type": "integer",
                        "description": "Количество пользователей в тесте"
                    },
                    "alpha": {
                        "type": "number",
                        "description": "Уровень значимости (по умолчанию 0.05)"
                    }
                },
                "required": ["mean_control", "std_control", "n_control", "mean_treatment", "std_treatment", "n_treatment"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delta_method_ratio_test",
            "description": "Дельта-метод для корректной оценки дисперсии ratio-метрик (отношений случайных величин: средний чек = сумма выручки / число заказов, CTR = клики / показы). Учитывает ковариацию между числителем и знаменателем.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mean_num_control": {"type": "number", "description": "Среднее числителя в контроле (например, средняя выручка на юзера)"},
                    "var_num_control": {"type": "number", "description": "Дисперсия числителя в контроле"},
                    "mean_denom_control": {"type": "number", "description": "Среднее знаменателя в контроле (например, среднее число заказов на юзера)"},
                    "var_denom_control": {"type": "number", "description": "Дисперсия знаменателя в контроле"},
                    "cov_control": {"type": "number", "description": "Ковариация числителя и знаменателя в контроле"},
                    "n_control": {"type": "integer", "description": "Число пользователей в контроле"},

                    "mean_num_treatment": {"type": "number", "description": "Среднее числителя в тесте"},
                    "var_num_treatment": {"type": "number", "description": "Дисперсия числителя в тесте"},
                    "mean_denom_treatment": {"type": "number", "description": "Среднее знаменателя в тесте"},
                    "var_denom_treatment": {"type": "number", "description": "Дисперсия знаменателя в тесте"},
                    "cov_treatment": {"type": "number", "description": "Ковариация числителя и знаменателя в тесте"},
                    "n_treatment": {"type": "integer", "description": "Число пользователей в тесте"},
                    "alpha": {"type": "number", "description": "Уровень значимости (по умолчанию 0.05)"}
                },
                "required": [
                    "mean_num_control", "var_num_control", "mean_denom_control", "var_denom_control", "cov_control", "n_control",
                    "mean_num_treatment", "var_num_treatment", "mean_denom_treatment", "var_denom_treatment", "cov_treatment", "n_treatment"
                ]
            }
        }
    },

    # 4. продвинутые методы (cuped, множественные поправки, подглядывание)
    {
        "type": "function",
        "function": {
            "name": "cuped_transform",
            "description": "Снижение дисперсии метрики с использованием ковариаты из предпериода (CUPED). Проверяет баланс ковариаты и силу корреляции.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mean_target_control": {"type": "number", "description": "Среднее целевой метрики в контроле"},
                    "mean_target_treatment": {"type": "number", "description": "Среднее целевой метрики в тесте"},
                    "mean_covariate_control": {"type": "number", "description": "Среднее предпериода в контроле"},
                    "mean_covariate_treatment": {"type": "number", "description": "Среднее предпериода в тесте"},
                    "cov_xy": {"type": "number", "description": "Ковариация между предпериодом и тестом"},
                    "var_x": {"type": "number", "description": "Дисперсия предпериода"},
                    "var_y": {"type": "number", "description": "Дисперсия целевой метрики"}
                },
                "required": ["mean_target_control", "mean_target_treatment", "cov_xy", "var_x", "var_y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "msprt_test",
            "description": "Mixture Sequential Probability Ratio Test (mSPRT). Рассчитывает always-valid p-value для защиты от ошибки ранней остановки (подглядывания / peeking).",
            "parameters": {
                "type": "object",
                "properties": {
                    "n_control": {"type": "integer", "description": "Размер контрольной группы"},
                    "n_treatment": {"type": "integer", "description": "Размер тестовой группы"},
                    "mean_control": {"type": "number", "description": "Среднее в контроле"},
                    "mean_treatment": {"type": "number", "description": "Среднее в тесте"},
                    "var_pooled": {"type": "number", "description": "Объединенная дисперсия"}
                },
                "required": ["n_control", "n_treatment", "mean_control", "mean_treatment", "var_pooled"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "benjamini_hochberg",
            "description": "Поправка Бенджамини-Хохберга (FDR) при одновременной проверке нескольких secondary-метрик или сегментов для защиты от ложных открытий.",
            "parameters": {
                "type": "object",
                "properties": {
                    "p_values": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Список нескорректированных p-value всех проверяемых гипотез"
                    },
                    "alpha": {
                        "type": "number",
                        "description": "Уровень значимости FDR (по умолчанию 0.05)"
                    }
                },
                "required": ["p_values"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "bonferroni",
            "description": "Консервативная поправка Бонферрони для контроля групповой ошибки первого рода (FWER). Используется для guardrail-метрик безопасности.",
            "parameters": {
                "type": "object",
                "properties": {
                    "p_values": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Список p-value guardrail-метрик"
                    },
                    "alpha": {
                        "type": "number",
                        "description": "Общий порог значимости (по умолчанию 0.05)"
                    }
                },
                "required": ["p_values"]
            }
        }
    },

    # 5. мощность и бизнес-оценка
    {
        "type": "function",
        "function": {
            "name": "pre_experiment_power",
            "description": "Расчет статистической мощности (Power Analysis) ДО теста на основе исторической дисперсии и планового MDE. Никогда не используй наблюдаемый эффект для post-hoc power!",
            "parameters": {
                "type": "object",
                "properties": {
                    "baseline_mean": {"type": "number", "description": "Историческое среднее метрики"},
                    "baseline_std": {"type": "number", "description": "Историческое стандартное отклонение"},
                    "mde_relative_pct": {"type": "number", "description": "Минимальный ожидаемый эффект в процентах (например, 2.5 для +2.5%)"},
                    "n_per_group": {"type": "integer", "description": "Фактический размер группы"}
                },
                "required": ["baseline_mean", "baseline_std", "mde_relative_pct", "n_per_group"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "effect_to_annual_revenue",
            "description": "Детерминированный перевод относительного эффекта в годовые рубли выручки с учетом доверительного интервала. Запрещено считать рубли в уме!",
            "parameters": {
                "type": "object",
                "properties": {
                    "relative_effect_pct": {
                        "type": "number",
                        "description": "Относительный эффект метрики в процентах (например, 3.2)"
                    },
                    "ci_lower_pct": {
                        "type": "number",
                        "description": "Нижняя граница 95% CI в процентах (например, 0.8)"
                    },
                    "ci_upper_pct": {
                        "type": "number",
                        "description": "Верхняя граница 95% CI в процентах (например, 5.6)"
                    },
                    "baseline_daily_revenue": {
                        "type": "number",
                        "description": "Базовая среднесуточная выручка компании в рублях"
                    }
                },
                "required": ["relative_effect_pct", "ci_lower_pct", "ci_upper_pct", "baseline_daily_revenue"]
            }
        }
    }
]



def get_tool_names() -> list[str]: 
    names = []
    for x in TOOL_DEFINITIONS:
        names.append(x['function']['name'])
    return names




def execute_tool(name: str, arguments: dict, db_client = None) -> dict:
    try: 
        if isinstance(arguments, str):
            import json
            arguments = json.loads(arguments)

        if name == 'run_sql_query': 
            if db_client == None:
                return {'error': 'База данных не подключена к агенту'}
                pass
            sql_text = arguments['sql']
            df = db_client.execute_query(sql_text)
            return {'rows': df.to_dict(orient = 'records')}

        elif name ==  'srm_check':
            n_cont = arguments['n_control'] #количество конроль группы
            n_treat = arguments['n_treatment'] #количество тестовой
            exp_ratio = arguments.get('expected_ratio', 0.5)
            from scipy import stats
            import numpy as np
            chi2_stat, p_value = stats.chisquare(f_obs= [n_cont, n_treat], f_exp = [(n_cont + n_treat) * exp_ratio, (n_cont + n_treat) * (1-exp_ratio)])
            check = p_value < 0.001
            return {
                'test':  "chi_square_goodness_of_fit", 
                 "chi2_statistic": round(chi2_stat, 4),
                "p_value": p_value,
                "is_srm": check,
                'verdict': "SRM_BROKEN" if check else 'SRM_OK'
            }

        else:
            # Для всех инструментов что ты допишешь потом в  tools/
            return {
                "status": "not_implemented_yet",
                "tool_name": name,
                "message": f"Инструмент '{name}' зарегистрирован, но будет реализован на следующем этапе."
            }


    except Exception as e:
        return {
            "error": f"Ошибка при вызове инструмента '{name}': {str(e)}"
        }

