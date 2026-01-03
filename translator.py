import ast

class DeepBlueTranslator:
    def __init__(self):
        self.cpp_lines = []

    def translate(self, py_code: str) -> str:
        try:
            tree = ast.parse(py_code)
            self.cpp_lines = ["// Gerado via Wandi Engine - DEEP BLUE SYSTEM", ""]
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    self.cpp_lines.append(f"void {node.name}() {{")
                    for stmt in node.body:
                        self._parse_statement(stmt)
                    self.cpp_lines.append("}\n")
            return "\n".join(self.cpp_lines)
        except Exception as e:
            return f"// ERRO DE SISTEMA: Verifique a IDENTAÇÃO.\n// Detalhe: {e}"

    def _parse_statement(self, stmt):
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
            if isinstance(call.func, ast.Name):
                name = call.func.id
                args = [a.value if isinstance(a, ast.Constant) else a.id for a in call.args]
                if name == "pinMode":
                    self.cpp_lines.append(f"  pinMode({args[0]}, {str(args[1]).upper()});")
                elif name == "digitalWrite":
                    status = "HIGH" if str(args[1]).upper() in ["1", "TRUE", "HIGH"] else "LOW"
                    self.cpp_lines.append(f"  digitalWrite({args[0]}, {status});")
                elif name == "delay":
                    self.cpp_lines.append(f"  delay({args[0]});")
                elif name == "serial_begin":
                    self.cpp_lines.append(f"  Serial.begin({args[0]});")
                elif name == "print":
                    content = f'"{args[0]}"' if isinstance(args[0], str) else args[0]
                    self.cpp_lines.append(f"  Serial.println({content});")