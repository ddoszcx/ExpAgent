import os
import json 
class  ExperimentAuditAgent: 
    def __init__(
        self, 
        db_client,
        model: str,
        api_key: str | None = None, 
        base_url: str | None = None, 
        max_iterations: int  = 15 # ставьте нужный вам количество итераций
    ): 
        self.db_client = db_client
        self.model = model
        self.api_key = api_key
        self.max_iterations = max_iterations
        self.base_url = base_url
        self.schema = self.db_client.get_schema() #достаем схему

        from openai import OpenAI
        revealed_base_url = self.base_url or os.getenv('OPENAI_BASE_URL')
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"), base_url= revealed_base_url)

    
    

    def audit_experiment(self, experiment_name: str) -> dict:
        from harness.system_prompt import get_system_prompt
        from harness.tool_registry import get_tool_names, execute_tool, TOOL_DEFINITIONS

        promt_text = get_system_prompt(schema = self.schema, tool_names= get_tool_names())

        messages = [
            {'role': 'system', 'content': promt_text},
            
            {'role': 'user', 'content': f"Проведи аудит эксперимента '{experiment_name}'."}
        ]

        executed_sql = []
        tool_calls_trace = []


        for x in range(self.max_iterations):
            completion = self.client.chat.completions.create(model=self.model, 
            messages = messages, 
            tools = TOOL_DEFINITIONS)
            response = completion.choices[0].message

            
            if response.tool_calls:
                messages.append(response)

                for y in response.tool_calls:
                    name = y.function.name 
                    arguments = y.function.arguments
                    if name == "run_sql_query":
                        executed_sql.append({str(y.id): arguments})
                    result = json.dumps(execute_tool(name, arguments, self.db_client), ensure_ascii=False)
                    messages.append({'role': 'tool', 'tool_call_id': y.id, 'content': result})
                    tool_calls_trace.append({"tool_name": name, "arguments":arguments})
            else:
                break 



            

        return {"experiment_name": experiment_name,
                "report_markdown": response.content  or f" Превышен лимит шагов ({self.max_iterations}). Агент не успел завершить аудит.",
                "executed_sql": executed_sql,
                "tool_calls_trace": tool_calls_trace,
                }

