import ast
from pathlib import Path
from typing import Any, Dict, List

class AntiTautologyAudit:
    def __init__(self):
        self.tautological_tests = []
        self.or_true_tests = []
        self.and_true_tests = []
        self.assert_true_tests = []
        self.weak_tests = []

    def scan_file(self, file_path: Path) -> Dict[str, Any]:
        if not file_path.exists():
            return {}

        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                self._check_test_function(node)

        return {
            "tautological_tests_count": len(self.tautological_tests),
            "tautological_tests": self.tautological_tests,
            "or_true_tests_count": len(self.or_true_tests),
            "or_true_tests": self.or_true_tests,
            "and_true_tests_count": len(self.and_true_tests),
            "and_true_tests": self.and_true_tests,
            "assert_true_tests_count": len(self.assert_true_tests),
            "assert_true_tests": self.assert_true_tests,
            "weak_tests_count": len(self.weak_tests),
            "weak_tests": self.weak_tests,
            "test_quality_passed": (len(self.tautological_tests) == 0 and 
                                  len(self.or_true_tests) == 0 and 
                                  len(self.and_true_tests) == 0 and 
                                  len(self.assert_true_tests) == 0 and 
                                  len(self.weak_tests) == 0)
        }

    def _check_test_function(self, func_node: ast.FunctionDef):
        func_name = func_node.name
        has_assert = False

        for node in ast.walk(func_node):
            # Detection of 'assert True'
            if isinstance(node, ast.Assert):
                has_assert = True
                if self._is_constant_true(node.test):
                    self.assert_true_tests.append(func_name)
                    if func_name not in self.tautological_tests:
                        self.tautological_tests.append(func_name)

            # Detection of 'expr or True' / 'expr | True'
            if isinstance(node, ast.BinOp):
                if isinstance(node.op, (ast.Or, ast.BitOr)):
                    if self._is_constant_true(node.right) or self._is_constant_true(node.left):
                        self.or_true_tests.append(func_name)
                        if func_name not in self.tautological_tests:
                            self.tautological_tests.append(func_name)
                
                # Detection of 'expr and True' / 'expr & True'
                if isinstance(node, ast.BoolOp):
                    if isinstance(node.op, (ast.And, ast.BitAnd)):
                        if any(self._is_constant_true(v) for v in node.values):
                            self.and_true_tests.append(func_name)
                            if func_name not in self.tautological_tests:
                                self.tautological_tests.append(func_name)
            
            # Special case for BoolOp (and/or) which are not BinOp in AST
            if isinstance(node, ast.BoolOp):
                if isinstance(node.op, ast.Or):
                    if any(self._is_constant_true(v) for v in node.values):
                        self.or_true_tests.append(func_name)
                        if func_name not in self.tautological_tests:
                            self.tautological_tests.append(func_name)
                if isinstance(node.op, ast.And):
                    if any(self._is_constant_true(v) for v in node.values):
                        self.and_true_tests.append(func_name)
                        if func_name not in self.tautological_tests:
                            self.tautological_tests.append(func_name)

        if not has_assert:
            # We check if there's at least a pytest.raises or a subprocess check
            # For simplicity, we just look for calls that look like verification
            is_weak = True
            for node in ast.walk(func_node):
                if isinstance(node, ast.Call):
                    call_name = ""
                    if isinstance(node.func, ast.Name):
                        call_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        call_name = node.func.attr
                    
                    if call_name in ["raises", "run", "check_call", "check_output"]:
                        is_weak = False
                        break
            if is_weak:
                self.weak_tests.append(func_name)

    def _is_constant_true(self, node: ast.AST) -> bool:
        # Python 3.8+ handles Constant, older versions use NameConstant(value=True) or Name(id='True')
        if isinstance(node, ast.Constant) and node.value is True:
            return True
        if hasattr(ast, "NameConstant") and isinstance(node, ast.NameConstant) and node.value is True:
            return True
        if isinstance(node, ast.Name) and node.id == "True":
            return True
        return False
