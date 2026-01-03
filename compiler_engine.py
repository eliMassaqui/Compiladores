import ast
import subprocess
import os
import shutil

class MiniCompiler:
    def __init__(self, port="COM5"):
        self.port = port
        user_documents = os.path.join(os.path.expanduser("~"), "Documents")
        self.arduino_tools_dir = os.path.join(user_documents, "Wandi Studio", "Engine", "arduino")
        self.sketch_dir = os.path.join(self.arduino_tools_dir, "build_sketch")
        self.ino_path = os.path.join(self.sketch_dir, "build_sketch.ino")
        
        self.possible_cli_paths = [
            "arduino-cli",
            os.path.join(self.arduino_tools_dir, "arduino-cli.exe"),
            os.path.join(os.getcwd(), "arduino-cli.exe"),
        ]

    def _find_cli(self) -> str:
        for path in self.possible_cli_paths:
            if shutil.which(path) or os.path.exists(path):
                return f'"{path}"' 
        return None

    def translate(self, py_code: str) -> str:
        """Traduz Python para C++ seguindo rigorosamente a sintaxe Wiring."""
        try:
            tree = ast.parse(py_code)
            cpp_lines = ["// Gerado automaticamente via Wandi Engine", ""]
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    cpp_lines.append(f"void {node.name}() {{")
                    
                    for stmt in node.body:
                        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                            # Captura o nome da função exatamente como escrita no Python
                            name = stmt.value.func.id
                            
                            # Extração de argumentos (Suporta: 13, OUTPUT, HIGH, etc)
                            args = []
                            for a in stmt.value.args:
                                if isinstance(a, ast.Constant):
                                    args.append(a.value)
                                elif isinstance(a, ast.Name):
                                    args.append(a.id)

                            # --- TRADUÇÃO DIRETA PARA WIRING ---
                            
                            if name == "pinMode":
                                mode = str(args[1]).upper()
                                cpp_lines.append(f"  pinMode({args[0]}, {mode});")
                                
                            elif name == "digitalWrite":
                                val = str(args[1]).upper()
                                # Converte lógica booleana/numérica para HIGH/LOW se necessário
                                status = "HIGH" if val in ["1", "TRUE", "HIGH"] else "LOW"
                                cpp_lines.append(f"  digitalWrite({args[0]}, {status});")
                                
                            elif name == "delay":
                                cpp_lines.append(f"  delay({args[0]});")
                                
                    cpp_lines.append("}\n")
            
            return "\n".join(cpp_lines)
        except Exception as e:
            # ALERTAR SOBRE IDENTAÇÃO (Regra de prioridade)
            return f"// ERRO DE SINTAXE/IDENTAÇÃO: {e}"

    def upload(self, cpp_code: str):
        cli_bin = self._find_cli()
        if not cli_bin: return "ERRO: arduino-cli não encontrado."
        if not os.path.exists(self.sketch_dir): os.makedirs(self.sketch_dir, exist_ok=True)
        with open(self.ino_path, "w") as f: f.write(cpp_code)
        
        command = f'{cli_bin} compile --upload -p {self.port} -b arduino:avr:uno "{self.sketch_dir}"'
        try:
            process = subprocess.run(command, shell=True, capture_output=True, text=True)
            return f"SUCESSO: Gravado na {self.port}\n{process.stdout}" if process.returncode == 0 else f"ERRO:\n{process.stderr}"
        except Exception as e: return f"ERRO DE SISTEMA: {e}"

    def upload(self, cpp_code: str):
        """Grava o código na placa usando o caminho detectado."""
        cli_bin = self._find_cli()
        
        if not cli_bin:
            return f"ERRO: arduino-cli.exe não encontrado em:\n{self.arduino_tools_dir}"

        if not os.path.exists(self.sketch_dir):
            os.makedirs(self.sketch_dir, exist_ok=True)
            
        with open(self.ino_path, "w") as f:
            f.write(cpp_code)

        command = f'{cli_bin} compile --upload -p {self.port} -b arduino:avr:uno "{self.sketch_dir}"'
        
        try:
            process = subprocess.run(command, shell=True, capture_output=True, text=True)
            if process.returncode == 0:
                return f"SUCESSO: Gravado na {self.port}\n{process.stdout}"
            return f"ERRO NA COMPILAÇÃO/UPLOAD:\n{process.stderr}\n{process.stdout}"
        except Exception as e:
            return f"ERRO DE SISTEMA: {e}"

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