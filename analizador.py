from flask import Flask, request, jsonify, render_template
import re
import ply.lex as lex

app = Flask(__name__)

# Lista de nombres de tokens
tokens = ['PR', 'ID', 'NUM', 'SYM', 'STR', 'ERR']

# Definiciones de los tokens
t_PR = r'\b(SELECT|FROM|WHERE|INSERT|INTO|VALUES|UPDATE|SET|DELETE)\b'
t_ID = r'\b[a-zA-Z_][a-zA-Z_0-9]*\b'
t_NUM = r'\b\d+\b'
t_SYM = r'[;,*=<>!+-/*]'
t_STR = r'\'[^\']*\''
t_ERR = r'.'

def t_error(t):
    print(f"Carácter ilegal '{t.value[0]}'")
    t.lexer.skip(1)

lexer = lex.lex()

def analyze_lexical(code):
    results = {'PR': 0, 'ID': 0, 'NUM': 0, 'STR': 0, 'SYM': 0, 'ERR': 0}
    lexer.input(code)
    while True:
        tok = lexer.token()
        if not tok:
            break
        token_name = tok.type
        results[token_name] += 1
    return results

def analyze_syntactic(code):
    errors = []
    # Verificar estructura básica de una consulta SQL
    if not re.match(r"SELECT .* FROM .*;", code, re.IGNORECASE):
        errors.append("Estructura básica de consulta SQL no válida. Debe contener 'SELECT ... FROM ...;'")
    if "WHERE" in code.upper() and not re.search(r"WHERE\s+.+", code, re.IGNORECASE):
        errors.append("Estructura básica de 'WHERE' no válida.")
    if "INSERT INTO" in code.upper() and not re.search(r"INSERT INTO\s+\w+\s*\(.+\)\s*VALUES\s*\(.+\);", code, re.IGNORECASE):
        errors.append("Estructura básica de 'INSERT INTO' no válida.")
    if "UPDATE" in code.upper() and not re.search(r"UPDATE\s+\w+\s+SET\s+.+\s+WHERE\s+.+;", code, re.IGNORECASE):
        errors.append("Estructura básica de 'UPDATE' no válida.")
    if "DELETE FROM" in code.upper() and not re.search(r"DELETE FROM\s+\w+\s+WHERE\s+.+;", code, re.IGNORECASE):
        errors.append("Estructura básica de 'DELETE FROM' no válida.")

    if not errors:
        return "Sintaxis correcta"
    else:
        return " ".join(errors)

def analyze_semantic(code):
    errors = []
    declared_tables = set()

    # Verificar que las tablas mencionadas en FROM existan (simulado)
    tables = re.findall(r"FROM\s+(\w+)", code, re.IGNORECASE)
    for table in tables:
        declared_tables.add(table)

    # Verificar columnas en SELECT
    columns = re.findall(r"SELECT\s+(.+?)\s+FROM", code, re.IGNORECASE)
    if columns:
        columns = columns[0].split(',')
        for col in columns:
            col = col.strip()
            # Simular la verificación de que las columnas existan en las tablas mencionadas
            if col != '*' and col not in declared_tables:
                errors.append(f"Columna '{col}' no existe en las tablas declaradas.")

    if not errors:
        return "Uso correcto de las estructuras semánticas"
    else:
        return " ".join(errors)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validate', methods=['POST'])
def validate():
    data = request.json
    queries = data.get('queries', [])
    results = []
    for query in queries:
        lexical_results = analyze_lexical(query)
        syntactic_result = analyze_syntactic(query)
        semantic_result = analyze_semantic(query)
        is_valid = syntactic_result == "Sintaxis correcta" and semantic_result == "Uso correcto de las estructuras semánticas"
        error_message = ''
        if not is_valid:
            error_message = syntactic_result if syntactic_result != "Sintaxis correcta" else semantic_result
        results.append({'valid': is_valid, 'error': error_message})
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
