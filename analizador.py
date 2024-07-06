from flask import Flask, request, jsonify, render_template
import re
import ply.lex as lex

app = Flask(__name__)

# Lista de nombres de tokens
tokens = ['PR', 'ID', 'NUM', 'SYM', 'STR', 'ERR']

# Definiciones de los tokens
t_PR = r'\b(SELECT|FROM|WHERE|INSERT|INTO|VALUES|UPDATE|SET|DELETE|CREATE|DATABASE|TABLE|USE|PRIMARY|KEY)\b'
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
    if re.match(r"^CREATE DATABASE \w+;$", code, re.IGNORECASE):
        return "Sintaxis correcta"
    elif re.match(r"^USE \w+;$", code, re.IGNORECASE):
        return "Sintaxis correcta"
    elif re.match(r"^CREATE TABLE \w+ \(\w+ \w+ PRIMARY KEY(, \w+ \w+)*\);$", code, re.IGNORECASE):
        return "Sintaxis correcta"
    elif re.match(r"^INSERT INTO \w+ \(\w+(, \w+)*\) VALUES \(.+\);$", code, re.IGNORECASE):
        return "Sintaxis correcta"
    elif re.match(r"^UPDATE \w+ SET \w+ = .+ WHERE \w+ = .+;$", code, re.IGNORECASE):
        return "Sintaxis correcta"
    elif re.match(r"^DELETE FROM \w+ WHERE \w+ = .+;$", code, re.IGNORECASE):
        return "Sintaxis correcta"
    else:
        errors.append("Estructura básica de consulta SQL no válida.")
    if not errors:
        return "Sintaxis correcta"
    else:
        return " ".join(errors)

def analyze_semantic(code):
    errors = []
    declared_tables = set(['mi_tabla'])

    tables = re.findall(r"FROM\s+(\w+)", code, re.IGNORECASE)
    for table in tables:
        if table not in declared_tables:
            errors.append(f"Tabla '{table}' no existe.")
        declared_tables.add(table)

    columns = re.findall(r"INSERT INTO \w+ \((.+?)\) VALUES", code, re.IGNORECASE)
    if columns:
        columns = columns[0].split(',')
        for col in columns:
            col = col.strip()
            if col not in ['id', 'nombre', 'edad']:
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
        results.append({
            'lexical': lexical_results,
            'syntactic': syntactic_result,
            'semantic': semantic_result,
            'valid': is_valid,
            'error': error_message
        })
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
