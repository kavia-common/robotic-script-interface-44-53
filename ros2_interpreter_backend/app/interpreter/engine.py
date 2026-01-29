"""
Core Interpreter Engine for Lua-like scripting

This module provides the main interpreter engine that parses and executes
Lua-like scripts with support for Delta ARM operations and dictionary literals.
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
    - Function calls (including plugin.function notation)
    - Control structures (if, while, for)
    - Dictionary/table literals
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
        
        # Function call: func(args) or plugin.func(args)
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
        """Execute function call with support for plugin.function notation and complex arguments"""
        # Match function name and extract arguments more carefully
        match = re.match(r'(\w+(?:\.\w+)*)\s*\((.*)\)$', line, re.DOTALL)
        if match:
            func_path = match.group(1)
            args_str = match.group(2)
            
            # Handle dot notation (e.g., delta.ReadModbus)
            if '.' in func_path:
                parts = func_path.split('.')
                # For plugin.function notation
                if len(parts) == 2:
                    plugin_name, func_name = parts
                    # Get plugin instance
                    if plugin_name in self.context.plugins:
                        plugin = self.context.plugins[plugin_name]
                        # Get plugin functions
                        plugin_functions = plugin.get_functions()
                        if func_name in plugin_functions:
                            # Parse and evaluate arguments
                            args = self._parse_function_arguments(args_str)
                            return plugin_functions[func_name](*args)
                        else:
                            raise InterpreterError(f"Function {func_name} not found in plugin {plugin_name}")
                    else:
                        # Try as a direct function call
                        func_name = func_path
                else:
                    func_name = func_path
            else:
                func_name = func_path
            
            # Parse and evaluate arguments
            args = self._parse_function_arguments(args_str)
            
            return self.context.call_function(func_name, args)
        
        raise InterpreterError(f"Invalid function call: {line}")
    
    def _parse_function_arguments(self, args_str: str) -> List[Any]:
        """
        Parse function arguments, handling complex types like dictionaries
        
        Args:
            args_str: Comma-separated argument string
            
        Returns:
            List of evaluated argument values
        """
        args = []
        
        if not args_str.strip():
            return args
        
        # Split arguments carefully, respecting nested structures
        arg_strings = self._split_arguments(args_str)
        
        for arg in arg_strings:
            args.append(self._evaluate_expression(arg.strip()))
        
        return args
    
    def _split_arguments(self, args_str: str) -> List[str]:
        """
        Split function arguments by commas, respecting nested structures and quotes
        
        Args:
            args_str: Comma-separated arguments string
            
        Returns:
            List of individual argument strings
        """
        arguments = []
        current = []
        depth = 0
        in_string = False
        string_char = None
        
        for i, char in enumerate(args_str):
            # Handle string boundaries
            if char in ['"', "'"] and (i == 0 or args_str[i-1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
            
            # Track nested brackets/braces/parentheses
            if not in_string:
                if char in ['{', '[', '(']:
                    depth += 1
                elif char in ['}', ']', ')']:
                    depth -= 1
                elif char == ',' and depth == 0:
                    # Found a separator at top level
                    arguments.append(''.join(current))
                    current = []
                    continue
            
            current.append(char)
        
        # Add the last argument
        if current:
            arguments.append(''.join(current))
        
        return arguments
    
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
        Supports variables, literals, simple operations, and dictionary/table literals
        """
        expr = expr.strip()
        
        # String literal
        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]
        
        if expr.startswith("'") and expr.endswith("'"):
            return expr[1:-1]
        
        # Dictionary/Table literal: {key1 = value1, key2 = value2}
        # Also supports ["key"] = value syntax for Modbus registers
        if expr.startswith('{') and expr.endswith('}'):
            return self._parse_table_literal(expr)
        
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
    
    def _parse_table_literal(self, expr: str) -> Dict[str, Any]:
        """
        Parse Lua-style table literal into Python dictionary
        
        Supports:
        - {key = value, key2 = value2}  (Lua style)
        - {["key"] = value, ["key2"] = value2}  (Bracket notation)
        - {[key] = value}  (Variable key)
        - Mixed formats
        
        Args:
            expr: Table literal expression like '{"40001" = 1, "40002" = 2}'
            
        Returns:
            Python dictionary
        """
        # Remove outer braces
        content = expr[1:-1].strip()
        
        if not content:
            return {}
        
        result = {}
        
        # Split by commas, but be careful with nested structures
        entries = self._split_table_entries(content)
        
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue
            
            # Match patterns: key = value, ["key"] = value, [key] = value
            # Pattern 1: ["key"] = value or ['key'] = value
            match = re.match(r'\[([\"\']?)([^\"\']+)\1\]\s*=\s*(.+)', entry)
            if match:
                key = match.group(2)
                value_expr = match.group(3).strip()
                value = self._evaluate_expression(value_expr)
                result[key] = value
                continue
            
            # Pattern 2: key = value (simple identifier key)
            match = re.match(r'(\w+)\s*=\s*(.+)', entry)
            if match:
                key = match.group(1)
                value_expr = match.group(2).strip()
                value = self._evaluate_expression(value_expr)
                result[key] = value
                continue
            
            # If no match, raise error
            raise InterpreterError(f"Invalid table entry: {entry}")
        
        return result
    
    def _split_table_entries(self, content: str) -> List[str]:
        """
        Split table content by commas, respecting nested structures and quotes
        
        Args:
            content: Table content without outer braces
            
        Returns:
            List of entry strings
        """
        entries = []
        current = []
        depth = 0
        in_string = False
        string_char = None
        
        for i, char in enumerate(content):
            # Handle string boundaries
            if char in ['"', "'"] and (i == 0 or content[i-1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
            
            # Track nested brackets/braces/parentheses
            if not in_string:
                if char in ['{', '[', '(']:
                    depth += 1
                elif char in ['}', ']', ')']:
                    depth -= 1
                elif char == ',' and depth == 0:
                    # Found a separator at top level
                    entries.append(''.join(current))
                    current = []
                    continue
            
            current.append(char)
        
        # Add the last entry
        if current:
            entries.append(''.join(current))
        
        return entries
    
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
