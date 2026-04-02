import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ExecutionResult:
    """Result of code execution"""
    status: str  # "success", "compile_error", "runtime_error", "timeout", "error"
    output: str = ""
    error: str = ""
    execution_time_ms: float = 0.0
    memory_used_mb: Optional[float] = None


class JavaExecutor:
    """Safely execute Java code with test cases"""

    def __init__(self, timeout_seconds: int = 2, memory_limit_mb: int = 256):
        if int(timeout_seconds) <= 0:
            raise ValueError("timeout_seconds must be a positive integer")
        self.timeout_seconds = int(timeout_seconds)
        if int(memory_limit_mb) <= 0:
            raise ValueError("memory_limit_mb must be a positive integer")
        self.memory_limit_mb = int(memory_limit_mb)
        self.temp_dir = tempfile.mkdtemp(prefix="java_exec_")

    def compile_code(self, code: str) -> tuple[bool, str]:
        """
        Compile Java code.
        
        Args:
            code: Java source code string
            
        Returns:
            (success: bool, error_message: str)
        """
        java_file = Path(self.temp_dir) / "Main.java"
        
        try:
            # Write code to file
            with open(java_file, "w", encoding="utf-8") as f:
                f.write(code)

            # Compile
            result = subprocess.run(
                ["javac", str(java_file)],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return False, result.stderr

            return True, ""

        except subprocess.TimeoutExpired:
            return False, "Compilation timeout"
        except FileNotFoundError:
            return False, "Java compiler (javac) not found. Ensure JDK is installed."
        except Exception as e:
            return False, str(e)

    def run_code(self, input_data: str = "") -> ExecutionResult:
        """
        Run compiled Java code with input.
        
        Args:
            input_data: stdin input for the program
            
        Returns:
            ExecutionResult with status, output, time, etc.
        """
        class_file = Path(self.temp_dir) / "Main.class"
        
        if not class_file.exists():
            return ExecutionResult(
                status="error",
                error="Code not compiled. Run compile_code first."
            )

        try:
            start_time = time.time()

            result = subprocess.run(
                [
                    "java",
                    f"-Xmx{self.memory_limit_mb}m",
                    "-cp",
                    self.temp_dir,
                    "Main",
                ],
                input=input_data,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                encoding="utf-8"
            )

            execution_time = (time.time() - start_time) * 1000  # ms

            process_status = "success" if result.returncode == 0 else "runtime_error"
            error_text = result.stderr.strip() if result.stderr else ""
            if result.returncode != 0 and not error_text:
                error_text = f"Process exited with return code {result.returncode}"

            return ExecutionResult(
                status=process_status,
                output=result.stdout.strip(),
                error=error_text,
                execution_time_ms=execution_time
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                status="timeout",
                error=f"Execution exceeded {self.timeout_seconds} seconds",
                execution_time_ms=self.timeout_seconds * 1000
            )
        except Exception as e:
            return ExecutionResult(
                status="error",
                error=str(e)
            )

    def evaluate_test_case(self, input_data: str, expected_output: str) -> dict:
        """
        Evaluate single test case.
        
        Returns dict with:
        - passed: bool
        - output: str (actual output)
        - expected: str
        - error: str
        - time_ms: float
        """
        result = self.run_code(input_data)

        passed = (
            result.status == "success" and
            result.output == expected_output.strip()
        )

        return {
            "passed": passed,
            "output": result.output,
            "expected": expected_output.strip(),
            "status": result.status,
            "error": result.error,
            "time_ms": result.execution_time_ms
        }

    def evaluate_all_test_cases(
        self,
        code: str,
        visible_tests: list[dict],
        hidden_tests: list[dict]
    ) -> dict:
        """
        Compile code and evaluate all test cases.
        
        Returns:
        {
            "status": "accepted" | "wrong_answer" | "compile_error" | "timeout",
            "passed_visible": int,
            "passed_hidden": int,
            "total_visible": int,
            "total_hidden": int,
            "max_time_ms": float,
            "visible_results": [...],
            "hidden_results": [...],
            "error": str
        }
        """
        # Step 1: Compile
        success, compile_error = self.compile_code(code)
        if not success:
            return {
                "status": "compile_error",
                "error": compile_error,
                "passed_visible": 0,
                "passed_hidden": 0,
                "total_visible": len(visible_tests),
                "total_hidden": len(hidden_tests),
                "visible_results": [],
                "hidden_results": [],
            }

        # Step 2: Evaluate visible tests
        visible_results = []
        passed_visible = 0
        max_time = 0.0

        for i, test in enumerate(visible_tests):
            test_result = self.evaluate_test_case(
                test.get("input", ""),
                test.get("expected", "")
            )
            visible_results.append(test_result)
            if test_result["passed"]:
                passed_visible += 1
            max_time = max(max_time, test_result.get("time_ms", 0))

            # Early exit on timeout/error
            if test_result["status"] in ["timeout", "error"]:
                return {
                    "status": "timeout" if test_result["status"] == "timeout" else "error",
                    "error": test_result["error"],
                    "passed_visible": passed_visible,
                    "passed_hidden": 0,
                    "total_visible": len(visible_tests),
                    "total_hidden": len(hidden_tests),
                    "visible_results": visible_results,
                    "hidden_results": [],
                    "max_time_ms": max_time
                }

        # All visible passed?
        if passed_visible < len(visible_tests):
            return {
                "status": "wrong_answer",
                "error": "Failed visible test case(s)",
                "passed_visible": passed_visible,
                "passed_hidden": 0,
                "total_visible": len(visible_tests),
                "total_hidden": len(hidden_tests),
                "visible_results": visible_results,
                "hidden_results": [],
                "max_time_ms": max_time
            }

        # Step 3: Evaluate hidden tests
        hidden_results = []
        passed_hidden = 0

        for i, test in enumerate(hidden_tests):
            test_result = self.evaluate_test_case(
                test.get("input", ""),
                test.get("expected", "")
            )
            hidden_results.append(test_result)
            if test_result["passed"]:
                passed_hidden += 1
            max_time = max(max_time, test_result.get("time_ms", 0))

            # Early exit on timeout/error
            if test_result["status"] in ["timeout", "error"]:
                return {
                    "status": "timeout" if test_result["status"] == "timeout" else "error",
                    "error": test_result["error"],
                    "passed_visible": passed_visible,
                    "passed_hidden": passed_hidden,
                    "total_visible": len(visible_tests),
                    "total_hidden": len(hidden_tests),
                    "visible_results": visible_results,
                    "hidden_results": hidden_results,
                    "max_time_ms": max_time
                }

        # All hidden passed?
        final_status = "accepted" if passed_hidden == len(hidden_tests) else "wrong_answer"

        return {
            "status": final_status,
            "error": "" if final_status == "accepted" else f"Failed {len(hidden_tests) - passed_hidden} hidden test(s)",
            "passed_visible": passed_visible,
            "passed_hidden": passed_hidden,
            "total_visible": len(visible_tests),
            "total_hidden": len(hidden_tests),
            "visible_results": visible_results,
            "hidden_results": hidden_results,
            "max_time_ms": max_time
        }

    def cleanup(self):
        """Clean up temporary files"""
        if hasattr(self, 'temp_dir') and self.temp_dir and Path(self.temp_dir).exists():
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup"""
        self.cleanup()
        return False
