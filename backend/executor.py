import cadquery as cq


SYSTEM_PROMPT = """\
You are a CADQuery 3D modeling assistant. The user will describe objects in natural language.
Your job is to write CADQuery Python code that creates the described 3D model.

Rules:
- Use the cadquery library (imported as `cq`).
- Always assign the final workplane or solid to a variable named `result`.
- The script is cumulative — each response should produce the complete model, not just a modification.
- Use reasonable default dimensions when the user doesn't specify them.
- Keep the code clean and well-structured.
- Only output Python code, wrapped in ```python ... ``` markers.
- Do NOT include any explanation outside the code block.

Example:
```python
import cadquery as cq
result = cq.Workplane("XY").box(10, 10, 10)
```"""

ERROR_RECOVERY_PROMPT = """\
The previous CADQuery script produced an error:

{error}

Here is the original user request: {user_request}

Please fix the code and output a corrected complete script wrapped in ```python ... ``` markers."""

SELF_ASSESS_PROMPT = """\
You have created a 3D model. You are now seeing a screenshot of the rendered model.
Review it and determine if it looks correct based on the user's request: {user_request}

If the model looks correct, respond with exactly: APPROVED

If it does NOT look correct, explain what's wrong and provide a corrected complete
CADQuery script wrapped in ```python ... ``` markers."""


def extract_code(response: str) -> str:
    """Extract Python code from a markdown code block in the LLM response."""
    if "```python" in response:
        start = response.index("```python") + len("```python")
        end = response.index("```", start)
        return response[start:end].strip()
    if "```" in response:
        start = response.index("```") + 3
        end = response.rindex("```")
        return response[start:end].strip()
    return response.strip()


class CadExecutor:
    """Executes CADQuery scripts in a restricted namespace."""

    def __init__(self):
        self._result = None

    @property
    def result(self):
        return self._result

    def execute(self, code: str) -> tuple[str | None, str | None]:
        """Execute a CADQuery script.

        Returns:
            (error_message, obj_data) — one will be None.
            If success: (None, "script executed, result stored")
            If failure: ("error traceback", None)
        """
        safe_builtins = {
            "__import__": __import__,
            "abs": abs, "bool": bool, "int": int, "float": float,
            "str": str, "list": list, "dict": dict, "tuple": tuple,
            "range": range, "len": len, "min": min, "max": max,
            "None": None, "True": True, "False": False,
        }
        namespace = {"__builtins__": safe_builtins, "cq": cq}
        try:
            exec(code, namespace)
            self._result = namespace.get("result")
            if self._result is None:
                raise RuntimeError("Script did not produce a 'result' variable. Assign your final model to 'result'.")
            return (None, "Script executed successfully.")
        except Exception as e:
            return (f"{type(e).__name__}: {e}", None)
