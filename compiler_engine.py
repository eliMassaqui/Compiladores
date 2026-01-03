import ast
import subprocess
import os
import shutil

class MiniCompiler:
    def __init__(self, port="COM5"):
        self.port = port
        
        # PONTO SEGURO: Localiza a pasta Documents de qualquer usuário no Windows
        user_documents = os.path.join(os.path.expanduser("~"), "Documents")
        
        # Reconstrói o caminho a partir de Documents
        self.arduino_tools_dir = os.path.join(user_documents, "Wandi Studio", "Engine", "arduino")
        
        # Pastas de build (onde o código será salvo antes de gravar)
        self.sketch_dir = os.path.join(self.arduino_tools_dir, "build_sketch")
        self.ino_path = os.path.join(self.sketch_dir, "build_sketch.ino")
        
        # PONTO SEGURO PARA ALTERAÇÃO: Lista de busca do executável
        self.possible_cli_paths = [
            "arduino-cli", # 1. No PATH global
            os.path.join(self.arduino_tools_dir, "arduino-cli.exe"), # 2. No caminho Wandi Studio
            os.path.join(os.getcwd(), "arduino-cli.exe"), # 3. Na pasta atual
        ]

    def _find_cli(self) -> str:
        """Busca o executável do arduino-cli de forma dinâmica."""
        for path in self.possible_cli_paths:
            if shutil.which(path) or os.path.exists(path):
                # Importante: aspas duplas para caminhos com espaços como 'Wandi Studio'
                return f'"{path}"' 
        return None

    def translate(self, py_code: str) -> str:
        try:
            tree = ast.parse(py_code)
            cpp_lines = ["// Gerado automaticamente"]
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    cpp_lines.append(f"void {node.name}() {{")
                    for stmt in node.body:
                        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                            name = stmt.value.func.id
                            args = [str(a.value) if hasattr(a, 'value') else "" for a in stmt.value.args]
                            if name == "pin_mode":
                                mode = "OUTPUT" if "OUT" in args[1].upper() else "INPUT"
                                cpp_lines.append(f"  pinMode({args[0]}, {mode});")
                            elif name == "digital_write":
                                val = "HIGH" if str(args[1]) == "1" else "LOW"
                                cpp_lines.append(f"  digitalWrite({args[0]}, {val});")
                            elif name == "delay":
                                cpp_lines.append(f"  delay({args[0]});")
                    cpp_lines.append("}\n")
            return "\n".join(cpp_lines)
        except Exception as e:
            return f"// Erro na análise: {e}"

    def upload(self, cpp_code: str):
        """Grava o código na placa usando o caminho detectado."""
        cli_bin = self._find_cli()
        
        if not cli_bin:
            return f"ERRO: arduino-cli.exe não encontrado em:\n{self.arduino_tools_dir}"

        # Cria a pasta de build se não existir
        if not os.path.exists(self.sketch_dir):
            os.makedirs(self.sketch_dir, exist_ok=True)
            
        with open(self.ino_path, "w") as f:
            f.write(cpp_code)

        # Comando com FQBN padrão para Arduino Uno
        command = f'{cli_bin} compile --upload -p {self.port} -b arduino:avr:uno "{self.sketch_dir}"'
        
        try:
            process = subprocess.run(command, shell=True, capture_output=True, text=True)
            if process.returncode == 0:
                return f"SUCESSO: Gravado na {self.port}\n{process.stdout}"
            return f"ERRO NA COMPILAÇÃO/UPLOAD:\n{process.stderr}\n{process.stdout}"
        except Exception as e:
            return f"ERRO DE SISTEMA: {e}"