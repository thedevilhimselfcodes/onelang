import os

class CCodeGenerator:
    def __init__(self):
        self.headers = [
            "#include <stdio.h>", 
            "#include <stdbool.h>", 
            "#include <stdlib.h>", 
            "#include <string.h>"
        ]
        # SCOPE ISOLATION FIX: Track local scope contexts independently from global variables
        self.global_symbol_table = {}
        self.local_symbol_table = None  # Will hold a dict when compiling a function body
        self.array_sizes = {}          
        
        self.function_prototypes = []  
        self.function_definitions = []
        self.main_body = []
        self.indentation_level = 1

    def get_indent(self):
        return "    " * self.indentation_level

    def get_symbol_type(self, name):
        """Queries the active local scope first before falling back to global definitions"""
        if self.local_symbol_table is not None and name in self.local_symbol_table:
            return self.local_symbol_table[name]
        return self.global_symbol_table.get(name, "double")

    def register_symbol(self, name, inferred_type):
        """Registers symbols strictly within the active compilation scope context"""
        if self.local_symbol_table is not None:
            self.local_symbol_table[name] = inferred_type
        else:
            self.global_symbol_table[name] = inferred_type

    def is_symbol_declared_in_current_scope(self, name):
        if self.local_symbol_table is not None:
            return name in self.local_symbol_table
        return name in self.global_symbol_table

    def infer_node_type(self, node) -> str:
        node_type = type(node).__name__
        if node_type == "NumberNode":
            return "int" if float(node.value).is_integer() else "double"
        elif node_type == "StringNode":
            return "string"
        elif node_type == "BooleanNode":
            return "bool"
        elif node_type == "VariableNode":
            return self.get_symbol_type(node.name)
        elif node_type == "ArrayIndexNode":
            return "double" 
        elif node_type == "CallNode":
            if node.func_name in ("str_concat", "http_get", "json_get", "file_read"):
                return "string"
            elif node.func_name in ("str_len", "len"):
                return "int"
            return "double"
        elif node_type == "BinOpNode":
            left_t = self.infer_node_type(node.left)
            right_t = self.infer_node_type(node.right)
            if left_t == "double" or right_t == "double": return "double"
            if left_t == "string" or right_t == "string": return "string"
            return left_t
        return "double"

    def translate_node(self, node) -> str:
        node_type = type(node).__name__

        if node_type == "NumberNode":
            if float(node.value).is_integer(): return str(int(node.value))
            return str(node.value)
        elif node_type == "StringNode":
            return f'"{node.value}"'
        elif node_type == "BooleanNode":
            return "true" if node.value else "false"
        elif node_type == "VariableNode":
            return node.name
        elif node_type == "BinOpNode":
            left_val = self.translate_node(node.left)
            right_val = self.translate_node(node.right)
            op = node.op_token.value
            return f"({left_val} {op} {right_val})"
        elif node_type == "ArrayIndexNode":
            arr_name = self.translate_node(node.array_expr)
            idx_expr = self.translate_node(node.index_expr)
            size_var = f"{arr_name}_size" if arr_name in self.array_sizes else "1000"
            return f"ONELANG_CHECK_BOUNDS(((double*){arr_name}), (int)({idx_expr}), {size_var})"
        elif node_type == "CallNode":
            if node.func_name == "input":
                prompt_arg = self.translate_node(node.args[0]) if node.args else '""'
                return f"one_lang_intrinsic_input({prompt_arg})"
            elif node.func_name == "file_read":
                return f"one_lang_intrinsic_file_read({self.translate_node(node.args[0])})"
            elif node.func_name == "str_len":
                return f"strlen({self.translate_node(node.args[0])})"
            elif node.func_name == "len":
                target_array_name = self.translate_node(node.args[0])
                return f"{target_array_name}_size"
                
            processed_args = []
            for arg in node.args:
                arg_expr = self.translate_node(arg)
                if type(arg).__name__ == "VariableNode" and self.get_symbol_type(arg.name) == "array":
                    processed_args.append(f"(double*){arg_expr}")
                    processed_args.append(f"{arg_expr}_size")
                else:
                    processed_args.append(arg_expr)
            return f"{node.func_name}({', '.join(processed_args)})"
        return ""

    def process_statement(self, node, buffer_target):
        node_type = type(node).__name__

        if node_type == "AssignNode":
            if type(node.var_node).__name__ == "ArrayIndexNode":
                # LVALUE BOUNDS SAFETY FIX: Output pointer tracking for array value mutations
                arr_name = self.translate_node(node.var_node.array_expr)
                idx_expr = self.translate_node(node.var_node.index_expr)
                val_expr = self.translate_node(node.expr_node)
                size_var = f"{arr_name}_size" if arr_name in self.array_sizes else "1000"
                
                buffer_target.append(f"{self.get_indent()}if ((int)({idx_expr}) < 0 || (int)({idx_expr}) >= (int)({size_var})) {{ printf(\"[Fatal Memory Error]: Out of bounds modification!\\n\"); exit(1); }}")
                buffer_target.append(f"{self.get_indent()}((double*){arr_name})[(int)({idx_expr})] = {val_expr};")
            else:
                var_name = node.var_node.name
                expr_type = type(node.expr_node).__name__
                
                if expr_type == "ArrayNode":
                    elements = [self.translate_node(el) for el in node.expr_node.elements]
                    size = len(elements)
                    self.register_symbol(var_name, "array")
                    self.array_sizes[var_name] = size
                    buffer_target.append(f"{self.get_indent()}int {var_name}_size = {size};")
                    buffer_target.append(f"{self.get_indent()}double {var_name}[{size}] = {{{', '.join(elements)}}};")
                else:
                    inferred_type = self.infer_node_type(node.expr_node)
                    value_expr = self.translate_node(node.expr_node)
                    
                    if not self.is_symbol_declared_in_current_scope(var_name):
                        self.register_symbol(var_name, inferred_type)
                        c_mapping = {"int": "int", "double": "double", "string": "const char*", "bool": "bool"}
                        c_type = c_mapping.get(inferred_type, "double")
                        buffer_target.append(f"{self.get_indentParent() if hasattr(self, 'get_indentParent') else self.get_indent()}{c_type} {var_name} = {value_expr};")
                    else:
                        buffer_target.append(f"{self.get_indent()}{var_name} = {value_expr};")

        elif node_type == "PrintNode":
            value_expr = self.translate_node(node.expr_node)
            inferred_type = self.infer_node_type(node.expr_node)
            if inferred_type == "string":
                buffer_target.append(f'{self.get_indent()}printf("[OneLang Out]: %s\\n", {value_expr});')
            elif inferred_type == "int":
                buffer_target.append(f'{self.get_indent()}printf("[OneLang Out]: %d\\n", {value_expr});')
            elif inferred_type == "bool":
                buffer_target.append(f'{self.get_indent()}printf("[OneLang Out]: %s\\n", {value_expr} ? "true" : "false");')
            else:
                buffer_target.append(f'{self.get_indent()}printf("[OneLang Out]: %g\\n", (double)({value_expr}));')

        elif node_type == "IfNode":
            buffer_target.append(f"{self.get_indent()}if ({self.translate_node(node.condition)}) {{")
            self.indentation_level += 1
            for stmt in node.then_block.statements: self.process_statement(stmt, buffer_target)
            self.indentation_level -= 1
            buffer_target.append(f"{self.get_indent()}}}")

        elif node_type == "WhileNode":
            buffer_target.append(f"{self.get_indent()}while ({self.translate_node(node.condition)}) {{")
            self.indentation_level += 1
            for stmt in node.block.statements: self.process_statement(stmt, buffer_target)
            self.indentation_level -= 1
            buffer_target.append(f"{self.get_indent()}}}")

        elif node_type == "ReturnNode":
            buffer_target.append(f"{self.get_indent()}return {self.translate_node(node.expr_node) if node.expr_node else '0'};")

        elif node_type == "FunctionDeclNode":
            func_name = node.name
            c_param_list = []
            func_buffer = []
            
            # ACTIVATION OF LOCAL LAYER: Separate functional scope initialization pass
            self.local_symbol_table = {}
            
            for p in node.params:
                p_kind = node.param_types.get(p, "scalar")
                if p_kind == "array":
                    self.local_symbol_table[p] = "array"
                    c_param_list.append(f"double* {p}")
                    c_param_list.append(f"int {p}_size")
                    self.array_sizes[p] = f"{p}_size"
                elif p in ("idx", "index", "target_idx", "limit", "i"):
                    self.local_symbol_table[p] = "int"
                    c_param_list.append(f"int {p}")
                else:
                    self.local_symbol_table[p] = "double"
                    c_param_list.append(f"double {p}")
            
            c_params_str = ", ".join(c_param_list)
            self.function_prototypes.append(f"double {func_name}({c_params_str});")
            self.function_definitions.append(f"\ndouble {func_name}({c_params_str}) {{")
            
            old_indent = self.indentation_level
            self.indentation_level = 1
            for stmt in node.body.statements: self.process_statement(stmt, func_buffer)
            for f_line in func_buffer: self.function_definitions.append(f_line)
            self.indentation_level = old_indent
            self.function_definitions.append("}")
            
            # CLOSE LOCAL SCOPE LAYER: Revert compilation tracking state to global scope baseline
            self.local_symbol_table = None

    def inject_bounds_guard(self):
        return """
#define ONELANG_CHECK_BOUNDS(arr, idx, size) \\
    (((idx) < 0 || (idx) >= (int)(size)) ? \\
    (printf("[Fatal Memory Error]: Out of bounds access! Element %d invalid.\\n", (idx)), exit(1), 0.0) : \\
    arr[(idx)])
"""

    def inject_string_intrinsics(self):
        return """
const char* one_lang_intrinsic_str_concat(const char* s1, const char* s2) {
    char* allocation = (char*)malloc(strlen(s1) + strlen(s2) + 1);
    strcpy(allocation, s1); strcat(allocation, s2); return allocation;
}

const char* one_lang_intrinsic_input(const char* prompt) {
    if (strlen(prompt) > 0) printf("%s", prompt);
    char* buffer = (char*)malloc(256);
    if (!fgets(buffer, 256, stdin)) { buffer[0] = '\\0'; return buffer; }
    buffer[strcspn(buffer, "\\r\\n")] = 0;
    return buffer;
}

const char* one_lang_intrinsic_file_read(const char* filepath) {
    FILE* file = fopen(filepath, "r");
    if (!file) return "File Not Found Error";
    fseek(file, 0, SEEK_END);
    long length = ftell(file);
    fseek(file, 0, SEEK_SET);
    char* allocation = (char*)malloc(length + 1);
    if (allocation) {
        size_t read_bytes = fread(allocation, 1, length, file);
        allocation[read_bytes] = '\\0';
    }
    fclose(file);
    return allocation ? allocation : "";
}
"""

    def generate_source(self, ast_statements) -> str:
        for stmt in ast_statements:
            if type(stmt).__name__ == "FunctionDeclNode": self.process_statement(stmt, self.function_definitions)
            else: self.process_statement(stmt, self.main_body)
        output_lines = []
        output_lines.extend(self.headers)
        output_lines.append(self.inject_bounds_guard())
        output_lines.append(self.inject_string_intrinsics())
        if self.function_prototypes:
            output_lines.append("\n// --- Static Symbol Forward Prototypes ---")
            output_lines.extend(self.function_prototypes)
        output_lines.append("\n// --- Compiled OneLang Functions ---")
        output_lines.extend(self.function_definitions)
        output_lines.append("\nint main() {")
        output_lines.extend(self.main_body)
        output_lines.append("\n    // --- Type-Inferred Memory Cleanup Passes ---")
        for var, inferred_t in self.global_symbol_table.items():
            if inferred_t == "string":
                is_dynamic = any(f"{var} = " in line and ("_get" in line or "str_concat" in line or "input" in line or "file_read" in line) for line in self.main_body)
                is_def_dynamic = any(f"const char* {var} = " in line and ("_get" in line or "str_concat" in line or "input" in line or "file_read" in line) for line in self.main_body)
                if is_dynamic or is_def_dynamic:
                    output_lines.append(f"    free((void*){var});")
        output_lines.append("    return 0;\n}")
        return "\n".join(output_lines)