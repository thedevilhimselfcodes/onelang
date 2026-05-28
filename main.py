import sys
import os
import argparse

sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from lexer import Lexer
from parser import Parser
from codegen import CCodeGenerator

def resolve_ast_dependencies(statements, base_dir, loaded_modules=None):
    """DYNAMIC RECURSIVE DEPENDENCY RESOLVER PASS"""
    if loaded_modules is None:
        loaded_modules = set()
        
    resolved_statements = []
    
    for stmt in statements:
        if type(stmt).__name__ == "ImportNode":
            module_name = stmt.module_name
            if module_name in loaded_modules:
                continue # Circular dependency block defense
                
            # Attempt to find the target library file relative to the execution script's path
            module_filename = os.path.join(base_dir, f"{module_name}.onelang")
            if not os.path.exists(module_filename):
                # Fallback path traversal pass checking our standard test workspace folder
                module_filename = os.path.join(os.getcwd(), 'tests', f"{module_name}.onelang")
                
            if not os.path.exists(module_filename):
                raise FileNotFoundError(f"OneLang Module Error: Cannot resolve dependency module tracking script '{module_name}.onelang'")
                
            loaded_modules.add(module_name)
            
            # Read, lex, and parse the imported file recursively
            with open(module_filename, "r") as f:
                module_code = f.read()
                
            mod_lexer = Lexer(module_code)
            mod_parser = Parser(mod_lexer)
            mod_ast = mod_parser.parse()
            
            # Recursively expand sub-modules inside the dependency script
            expanded_ast = resolve_ast_dependencies(mod_ast, os.path.dirname(module_filename), loaded_modules)
            resolved_statements.extend(expanded_ast)
        else:
            resolved_statements.append(stmt)
            
    return resolved_statements

def main():
    parser_args = argparse.ArgumentParser(description="OneLang Production Modular Compiler")
    parser_args.add_argument("--compile", help="Path to the source .onelang file to compile")
    args = parser_args.parse_args()

    if not args.compile:
        print("[Compiler Error]: No source input file specified. Use --compile <file.onelang>")
        sys.exit(1)

    try:
        with open(args.compile, "r") as f:
            code = f.read()
    except FileNotFoundError:
        print(f"[Compiler Error]: Target file '{args.compile}' not found on disk.")
        sys.exit(1)

    print("--- Launching OneLang Production Transpiler Backend ---")
    
    try:
        lexer = Lexer(code)
        parser = Parser(lexer)
        initial_ast = parser.parse()
        
        # Run dependency graph flattening pass
        script_directory = os.path.dirname(os.path.abspath(args.compile))
        unified_ast = resolve_ast_dependencies(initial_ast, script_directory)
        
        codegen = CCodeGenerator()
        c_source = codegen.generate_source(unified_ast)
        
        base_name = os.path.splitext(os.path.basename(args.compile))[0]
        output_filename = f"{base_name}.c"
        
        with open(output_filename, "w") as f:
            f.write(c_source)
            
        print(f"📦 Success! Modular dependency flattening complete. Saved: {output_filename}")

    except Exception as general_err:
        print(f"\n❌ [OneLang Modular Compilation Error]: {general_err}")
        sys.exit(1)

if __name__ == "__main__":
    main()