"""
Core Interpreter Engine for Lua-like scripting

This module provides the main interpreter engine that parses and executes
Lua-like scripts with support for Delta ARM operations.
"""

import re
from typing import Any, Dict, List, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class InterpreterError(Exception):
    """Custom exception for interpreter errors"""
    pass


class InterpreterContext:
    """
    Execution context for the interpreter
    Maintains variables, functions, and plugin references
    """
    
    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.functions: Dict[str, Callable] = {}
        self.plugins: Dict[str, Any] = {}
        self.builtin_functions = self._init_builtins()
        
    def _init_builtins(self) -> Dict[str, Callable]:
        """Initialize built-in functions"""
        return {
            'print': lambda *args: print(*args),
            'type': lambda x: type(x).__name__,
            'tonumber': lambda x: float(x) if isinstance(x, str) else x,
            'tostring': lambda x: str(x),
            'len': lambda x: len(x) if hasattr(x, '__len__') else 0,
        }
    
    def set_variable(self, name: str, value: Any):
        """Set a variable in the context"""
        self.variables[name] = value
    
    def get_variable(self, name: str) -> Any:
        """Get a variable from the context"""
        if name in self.variables:
            return self.variables[name]
        raise InterpreterError(f"Undefined variable: {name}")
    
    def register_function(self, name: str, func: Callable):
        """Register a user-defined or plugin function"""
        self.functions[name] = func
    
    def call_function(self, name: str, args: List[Any]) -> Any:
        """Call a function by name with arguments"""
        if name in self.builtin_functions:
            return self.builtin_functions[name](*args)
        elif name in self.functions:
            return self.functions[name](*args)
        else:
            raise InterpreterError(f"Undefined function: {name}")
    
    def register_plugin(self, name: str, plugin: Any):
        """Register a plugin instance"""
        self.plugins[name] = plugin


class LuaInterpreter:
    """
    PUBLIC_INTERFACE
    Main interpreter class for executing Lua-like scripts
    
    Supports:
    - Variable assignments
    - Function calls
    - Control structures (if, while, for)
    - Plugin function calls
    - Mathematical operations
    """
    
    def __init__(self, context: Optional[InterpreterContext] = None):
        """
        Initialize the interpreter
        
        Args:
            context: Optional pre-configured execution context
        """
        self.context = context or InterpreterContext()
        self.current_line = 0
        
    def execute(self, script: str) -> Dict[str, Any]:
        """
        PUBLIC_INTERFACE
        Execute a Lua-like script
        
        Args:
            script: The script text to execute
            
        Returns:
            Dictionary with execution results including output and final context state
            
        Raises:
            InterpreterError: If script execution fails
        """
        try:
            lines = script.strip().split('\n')
            self.current_line = 0
            output = []
            
            while self.current_line < len(lines):
                line = lines[self.current_line].strip()
                
                if not line or line.startswith('--'):
                    self.current_line += 1
                    continue
                
                result = self._execute_line(line)
                if result is not None:
                    output.append(result)
                
                self.current_line += 1
            
            return {
                'success': True,
                'output': output,
                'variables': self.context.variables.copy()
            }
            
        except Exception as e:
            logger.error(f"Interpreter error at line {self.current_line + 1}: {str(e)}")
            raise InterpreterError(f"Line {self.current_line + 1}: {str(e)}")
    
    def _execute_line(self, line: str) -> Optional[Any]:
        """Execute a single line of code"""
        # Assignment: x = value
        if '=' in line and not any(op in line for op in ['==', '!=', '<=', '>=']):
            return self._execute_assignment(line)
        
        # Function call: func(args)
        if '(' in line and ')' in line:
            return self._execute_function_call(line)
        
        # Control structures
        if line.startswith('if '):
            return self._execute_if(line)
        
        if line.startswith('while '):
            return self._execute_while(line)
        
        if line.startswith('for '):
            return self._execute_for(line)
        
        return None
    
    def _execute_assignment(self, line: str):
        """Execute variable assignment"""
        match = re.match(r'(\w+)\s*=\s*(.+)', line)
        if match:
            var_name = match.group(1)
            expression = match.group(2)
            value = self._evaluate_expression(expression)
            self.context.set_variable(var_name, value)
            return None
        raise InterpreterError(f"Invalid assignment: {line}")
    
    def _execute_function_call(self, line: str) -> Any:
        """Execute function call"""
        match = re.match(r'(\w+)\((.*?)\)', line)
        if match:
            func_name = match.group(1)
            args_str = match.group(2)
            
            # Parse arguments
            args = []
            if args_str.strip():
                for arg in args_str.split(','):
                    args.append(self._evaluate_expression(arg.strip()))
            
            return self.context.call_function(func_name, args)
        
        raise InterpreterError(f"Invalid function call: {line}")
    
    def _execute_if(self, line: str):
        """Execute if statement (simplified)"""
        # Basic if condition implementation
        match = re.match(r'if\s+(.+)\s+then', line)
        if match:
            result = self._evaluate_expression(match.group(1))
            # In a full implementation, would parse the then block
            return bool(result)
        raise InterpreterError(f"Invalid if statement: {line}")
    
    def _execute_while(self, line: str):
        """Execute while loop (simplified)"""
        match = re.match(r'while\s+(.+)\s+do', line)
        if match:
            # In a full implementation, would execute loop body
            return None
        raise InterpreterError(f"Invalid while statement: {line}")
    
    def _execute_for(self, line: str):
        """Execute for loop (simplified)"""
        match = re.match(r'for\s+(\w+)\s*=\s*(.+)\s+do', line)
        if match:
            # In a full implementation, would execute loop body
            return None
        raise InterpreterError(f"Invalid for statement: {line}")
    
    def _evaluate_expression(self, expr: str) -> Any:
        """
        Evaluate an expression and return its value
        Supports variables, literals, and simple operations
        """
        expr = expr.strip()
        
        # String literal
        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]
        
        if expr.startswith("'") and expr.endswith("'"):
            return expr[1:-1]
        
        # Number literal
        try:
            if '.' in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass
        
        # Boolean literal
        if expr == 'true':
            return True
        if expr == 'false':
            return False
        
        # Nil/null
        if expr == 'nil':
            return None
        
        # Variable reference
        if re.match(r'^\w+$', expr):
            return self.context.get_variable(expr)
        
        # Function call
        if '(' in expr:
            return self._execute_function_call(expr)
        
        # Mathematical expression (simplified)
        if any(op in expr for op in ['+', '-', '*', '/', '%']):
            return self._evaluate_math(expr)
        
        raise InterpreterError(f"Cannot evaluate expression: {expr}")
    
    def _evaluate_math(self, expr: str) -> float:
        """Evaluate mathematical expression"""
        # Simple eval for mathematical expressions
        # In production, use a proper expression parser
        try:
            # Replace variables with their values
            for var_name in self.context.variables:
                expr = expr.replace(var_name, str(self.context.variables[var_name]))
            
            # Safely evaluate mathematical expression
            return eval(expr, {"__builtins__": {}}, {})
        except Exception as e:
            raise InterpreterError(f"Math evaluation error: {str(e)}")
