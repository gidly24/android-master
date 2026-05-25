import json
import os
import urllib.request
import urllib.error
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, quote_plus


class AIAssistant:
    def __init__(self, task_service=None):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set. Set the environment variable.")

        self.api_url = f"{os.getenv('GOOGLE_GEMINI_BASE_URL', 'https://generativelanguage.googleapis.com')}/v1beta/models/gemini-2.5-flash-lite:generateContent"
        self.task_service = task_service # Store the TaskService instance
        self.today_date = date.today().isoformat()

        # Updated system prompt for comprehensive task management
        self.system_prompt = f"""RESPOND ONLY WITH VALID JSON. NO OTHER TEXT.

Analyze user text and return a JSON object describing the requested task management operation.
You must infer the user's intent and provide the most appropriate JSON based on the following structure and rules.

Today's date is {self.today_date}.

Available actions: "create", "delete", "mark_done", "update", "list", "get_stats".

JSON Structure:
{{
  "action": "create" | "delete" | "mark_done" | "update" | "list" | "get_stats" | null,
  
  // Fields for "create" action:
  "title": "task title", // Mandatory. If missing, return an error JSON.
  "description": "extra details or empty string", // Optional.
  "category": "работа|личное|покупки|здоровье|другое", // Infer from context.
  "due_date": "YYYY-MM-DD" | null, // Parse relative to {self.today_date}. Null if not specified.
  "due_time": "HH:MM" | null, // Parse relative to {self.today_date}. Null if not specified. If only date, use "23:59".
  "priority": "низкий|средний|высокий" | "", // Empty string if not specified.

  // Fields for "delete" action:
  "task_id": integer, // Use if explicitly given.
  "title_query": "task title to search for and delete", // Use if task_id is not known or provided.

  // Fields for "mark_done" action:
  "task_id": integer, // Use if explicitly given.
  "title_query": "task title to search for and mark as done", // Use if task_id is not known or provided. Use for "выполнить", "сделано", "завершить".

  // Fields for "update" action:
  "task_id": integer, // Use if explicitly given.
  "title_query": "task title to search for and update", // Use if task_id is not known or provided.
  "new_values": {{ // Contains fields to update. Can be partial.
    "title": "new task title", // Optional
    "description": "new description", // Optional
    "category": "new category", // Optional
    "due_date": "YYYY-MM-DD", // Optional
    "due_time": "HH:MM", // Optional
    "priority": "низкий|средний|высокий", // Optional
    "clear_due_date": true // Optional, set to true to remove due date and time.
  }},

  // Fields for "list" action:
  "filters": {{
    "category": "category name", // Optional
    "status": "активна|выполнена|просрочена", // Optional
    "title_query": "search text", // Optional
    "view": "actual" | "all" // "actual" (default) for upcoming/urgent, "all" for everything.
  }},

  // General fields for errors or clarifications:
  "error": "Descriptive error message if the request cannot be fully understood or fulfilled", // Use when action is null or an action fails due to missing info.
  "clarification": "Question to ask the user if more information is needed for an action." // Use when ambiguous or insufficient info.
}}

Rules:
1.  You must ALWAYS return a JSON object.
2.  If the user's request is unclear, ambiguous, or missing essential information for any action, return JSON with `action: null`, an appropriate `error` message, and potentially a `clarification` question.
3.  For `create` action: `title` is mandatory. If missing, return an error JSON.
4.  For `delete`, `mark_done`, and `update` actions: The request MUST include EITHER `task_id` OR `title_query`. If neither is provided, return an error.
5.  For `update` action: At least one field within `new_values` should be provided for a meaningful update. If `new_values` is empty or missing, return an error or clarification.
6.  Preserve existing values for fields not specified in `new_values` during an update.
7.  Parse dates and times relative to today's date: {self.today_date}. Use `YYYY-MM-DD` for dates and `HH:MM` for times. If only a date is given, assume time is `23:59`. If the user explicitly asks to remove the due date, use `clear_due_date: true`.
8.  If no specific action can be determined, return `action: null` with an `error` or `clarification`.
9.  If the user asks to "показать задачи", "список", "что у меня на сегодня", use the `list` action.
10. If the user asks for "статистика", "сколько задач", use the `get_stats` action.
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

            if http_proxy or https_proxy:
                proxy_support = {}
                if http_proxy:
                    try:
                        parsed_http = urlparse(http_proxy)
                        encoded_username = quote_plus(parsed_http.username) if parsed_http.username else ""
                        encoded_password = quote_plus(parsed_http.password) if parsed_http.password else ""
                        
                        # Reconstruct netloc with encoded credentials
                        if parsed_http.username and parsed_http.password:
                            netloc = f"{encoded_username}:{encoded_password}@{parsed_http.hostname}:{parsed_http.port}"
                        elif parsed_http.username:
                            netloc = f"{encoded_username}@{parsed_http.hostname}:{parsed_http.port}"
                        else:
                            netloc = f"{parsed_http.hostname}:{parsed_http.port}" # No credentials

                        # Construct the final URL
                        encoded_http_proxy_url = f"{parsed_http.scheme}://{netloc}"
                        proxy_support['http'] = encoded_http_proxy_url
                    except Exception:
                        # Fallback to original if parsing/encoding fails
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
                            netloc = f"{parsed_https.hostname}:{parsed_https.port}" # No credentials

                        encoded_https_proxy_url = f"{parsed_https.scheme}://{netloc}"
                        proxy_support['https'] = encoded_https_proxy_url
                    except Exception:
                        # Fallback to original if parsing/encoding fails
                        proxy_support['https'] = https_proxy 
                
                proxy_handler = urllib.request.ProxyHandler(proxy_support)
                opener = urllib.request.build_opener(proxy_handler)
            else:
                opener = urllib.request.build_opener() # Default opener if no proxy
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
                if service_response and "answer" in service_response:
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
