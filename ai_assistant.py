import json
import os
import ssl
import urllib.request
import urllib.error
from datetime import date, datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, quote_plus


class AIAssistant:
    def __init__(self, task_service=None):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set. Set the environment variable.")

        self.api_url = f"{os.getenv('GOOGLE_GEMINI_BASE_URL', 'https://generativelanguage.googleapis.com')}/v1beta/models/gemini-2.5-flash-lite:generateContent"
        self.task_service = task_service # Store the TaskService instance
        self.now = datetime.now()
        self.today_date = self.now.date().isoformat()
        self.now_time = self.now.strftime("%H:%M")

        # Updated system prompt for comprehensive task management
        self.system_prompt = f"""RESPOND ONLY WITH VALID JSON. NO OTHER TEXT.

Analyze user text and return a JSON object describing the requested task management operation.
You must infer the user's intent and provide the most appropriate JSON based on the following structure and rules.

Current date: {self.today_date}. Current time: {self.now_time}.

Available actions: "create", "delete", "mark_done", "update", "list", "get_stats".

JSON Structure:
{{
  "action": "create" | "delete" | "mark_done" | "update" | "list" | "get_stats" | null,
  
  // Fields for "create" action:
  "title": "task title", // Mandatory. Formulate as a noun phrase (e.g., "Защита диплома", "Покупка продуктов").
  "description": "extra details or empty string", // Optional.
  "category": "работа|личное|покупки|здоровье|другое", // Infer from context.
  "due_date": "YYYY-MM-DD" | null, // Parse relative to {self.today_date}.
  "due_time": "HH:MM" | null, // Parse relative to current time {self.now_time}.
  "priority": "низкий|средний|высокий" | "", // Empty string if not specified.

  // Fields for "delete" and "mark_done" actions:
  "task_id": integer, // Use if explicitly given.
  "title_query": "task title to search for", // Mandatory if task_id is unknown.

  // Fields for "update" action:
  "task_id": integer, // Use if explicitly given.
  "title_query": "task title to search for", // Mandatory if task_id is unknown.
  "new_values": {{ // Contains fields to update.
    "title": "new task title",
    "description": "new description",
    "category": "new category",
    "due_date": "YYYY-MM-DD",
    "due_time": "HH:MM",
    "priority": "низкий|средний|высокий",
    "clear_due_date": true 
  }},

  // Fields for "list" action:
  "filters": {{
    "category": "category name",
    "status": "активна|выполнена|просрочена",
    "title_query": "search text",
    "view": "actual" | "all"
  }},

  // General fields for errors or clarifications:
  "error": "Descriptive error message", 
  "clarification": "Question to ask the user"
}}

Rules:
1.  ALWAYS return a valid JSON object.
2.  If the user's request is unclear, ambiguous, or missing essential information, return JSON with `action: null`, an appropriate `error` message, and a `clarification` question.
3.  For `create` action:
    *   `title` is mandatory.
    *   Formulate titles as concise noun phrases (e.g., "Поход в магазин", "Сдача отчета").
    *   Calculate `due_date` and `due_time` based on current time ({self.now_time}) and date ({self.today_date}). "Через час" should be calculated relative to {self.now_time}.
4.  For `delete`, `mark_done`, and `update` actions:
    *   If `task_id` is unknown, use `title_query` to search.
    *   IF NO TASK IS FOUND, OR IF THE REQUEST IS AMBIGUOUS, YOU MUST REQUEST A LIST OF ACTIVE TASKS TO PRESENT TO THE USER, RATHER THAN ASKING A VAGUE CLARIFICATION QUESTION. Return `action: null`, and in the `clarification` field, explicitly ask the user to choose from the list, and set the expectation that the service will provide it.
5.  If the user asks for actions on tasks, and you are unsure which task, return `action: null` with a `clarification` question requesting the user to select from the task list.
6.  If no action is determinable, return `action: null`.
"""

    def process_message(self, text: str) -> dict:
        try:
            full_prompt = f"{self.system_prompt}\n\nUser: {text}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": full_prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 500,
                }
            }

            json_payload = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                f"{self.api_url}?key={self.api_key}",
                data=json_payload,
                headers={"Content-Type": "application/json"}
            )

            # --- PROXY CONFIGURATION START ---
            proxy_handler = None
            http_proxy = os.getenv("HTTP_PROXY")
            https_proxy = os.getenv("HTTPS_PROXY")

            # Создаём SSL-контекст: на Android certifi недоступен, используем системные сертификаты
            try:
                ssl_context = ssl.create_default_context()
                import certifi
                ssl_context.load_verify_locations(certifi.where())
            except Exception:
                # На Android certifi может отсутствовать — используем системные CA
                try:
                    ssl_context = ssl.create_default_context()
                except Exception:
                    ssl_context = ssl._create_unverified_context()

            https_handler = urllib.request.HTTPSHandler(context=ssl_context)

            if http_proxy or https_proxy:
                proxy_support = {}
                if http_proxy:
                    try:
                        parsed_http = urlparse(http_proxy)
                        encoded_username = quote_plus(parsed_http.username) if parsed_http.username else ""
                        encoded_password = quote_plus(parsed_http.password) if parsed_http.password else ""
                        if parsed_http.username and parsed_http.password:
                            netloc = f"{encoded_username}:{encoded_password}@{parsed_http.hostname}:{parsed_http.port}"
                        elif parsed_http.username:
                            netloc = f"{encoded_username}@{parsed_http.hostname}:{parsed_http.port}"
                        else:
                            netloc = f"{parsed_http.hostname}:{parsed_http.port}"
                        proxy_support['http'] = f"{parsed_http.scheme}://{netloc}"
                    except Exception:
                        proxy_support['http'] = http_proxy

                if https_proxy:
                    try:
                        parsed_https = urlparse(https_proxy)
                        encoded_username = quote_plus(parsed_https.username) if parsed_https.username else ""
                        encoded_password = quote_plus(parsed_https.password) if parsed_https.password else ""
                        if parsed_https.username and parsed_https.password:
                            netloc = f"{encoded_username}:{encoded_password}@{parsed_https.hostname}:{parsed_https.port}"
                        elif parsed_https.username:
                            netloc = f"{encoded_username}@{parsed_https.hostname}:{parsed_https.port}"
                        else:
                            netloc = f"{parsed_https.hostname}:{parsed_https.port}"
                        proxy_support['https'] = f"{parsed_https.scheme}://{netloc}"
                    except Exception:
                        proxy_support['https'] = https_proxy

                proxy_handler = urllib.request.ProxyHandler(proxy_support)
                opener = urllib.request.build_opener(https_handler, proxy_handler)
            else:
                opener = urllib.request.build_opener(https_handler)
            # --- PROXY CONFIGURATION END ---

            with opener.open(req, timeout=30) as response:
                raw_response = response.read().decode('utf-8')
                if not raw_response:
                    return {
                        "success": False,
                        "error": "Empty response from server",
                    }
                result = json.loads(raw_response)

            if "candidates" not in result or not result["candidates"]:
                return {
                    "success": False,
                    "error": "Empty API response",
                }

            content = result["candidates"][0]["content"]["parts"][0]["text"]

            # Try to find JSON in the response if it's not direct JSON
            content = content.strip()
            if content.startswith("```"):
                # Extract JSON from markdown code block
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end > start:
                    content = content[start:end]

            data = json.loads(content)
            return {
                "success": True,
                "data": data,
                "raw_response": content,
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON parsing error: {str(e)}",
            }
        except HTTPError as e:
            # Специфическая ошибка от Google (код 400, 403 и т.д.)
            # Должна стоять ВЫШЕ обычного URLError
            try:
                error_body = e.read().decode('utf-8')
            except Exception:
                error_body = "Could not read error body"
            return {
                "success": False,
                "error": f"HTTP Error {e.code}: {error_body}",
            }
        except URLError as e:
            # Общие сетевые проблемы (таймаут, нет интернета)
            return {
                "success": False,
                "error": f"Network error: {str(e)}",
            }
        except Exception as e:
            # Самый общий перехват для непредвиденных сбоев (всегда в самом низу)
            return {
                "success": False,
                "error": f"An unexpected error occurred: {str(e)}",
            }

    def get_response(self, text: str) -> str:
        ai_result = self.process_message(text)

        if not ai_result.get("success"):
            # If process_message failed, return the error directly.
            return f"AI Error: {ai_result.get('error', 'Unknown error')}"

        data = ai_result.get("data", {})
        action = data.get("action")

        if not data:
            return "AI returned an empty response."
        
        # If AI returned an error or clarification directly
        if action is None and (data.get("error") or data.get("clarification")):
            return data.get("clarification", data.get("error", "I'm not sure how to proceed."))

        # Handle task management actions if TaskService is available
        if self.task_service:
            try:
                service_response = {}
                if action == "create":
                    # Check for mandatory 'title' before calling service
                    if not data.get("title"):
                        return "I need a title to create a task. Please describe it."
                    service_response = self.task_service.create_task_from_ai(data)
                elif action == "delete":
                    service_response = self.task_service.delete_task_from_ai(data)
                elif action == "mark_done":
                    service_response = self.task_service.mark_task_done_from_ai(data)
                elif action == "update":
                    service_response = self.task_service.update_task_from_ai(data)
                elif action == "list":
                    service_response = self.task_service.list_tasks_for_ai(data.get("filters", {}))
                elif action == "get_stats":
                    service_response = self.task_service.get_statistics_for_ai()
                
        # If the service call was successful and returned an answer
                if service_response:
                    # If candidates are present, they should be displayed
                    if "candidates" in service_response and service_response["candidates"]:
                        # We might need to handle how candidates are displayed. 
                        # Assuming service_response["answer"] contains the formatted candidate list.
                        return service_response.get("answer", "Выберите задачу из списка.")
                    
                    if "answer" in service_response:
                        return service_response["answer"]
                
                # If the service returned an error or clarification without an answer
                elif service_response and ("error" in service_response or "clarification" in service_response):
                    return service_response.get("clarification", service_response.get("error", "Failed to process task request."))
                # If action was recognized but no service response or answer
                elif action: # If an action was specified but we didn't get a good response
                     return "I processed your request, but couldn't get a clear confirmation. Please try again or check the task list."
                else: # If action was null and no specific error/clarification from AI.
                    return "I'm not sure how to help with that. Can you please rephrase?"

            except Exception as e:
                # Catch any unexpected errors during TaskService calls
                return f"An error occurred while processing your request: {str(e)}"
        else:
            # TaskService is not available
            if action:
                return f"AI understood the action '{action}', but the task management system is not configured. Please set up the necessary services."
            else:
                return "I cannot process your request as the AI assistant is not fully configured for task management."
