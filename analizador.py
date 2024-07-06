from flask import Flask, request, jsonify, render_template
import ply.lex as lex
import ply.yacc as yacc

app = Flask(__name__)

# Definir los tokens y las palabras reservadas
tokens = (
    'ID',
    'SEMICOLON',
    'LPAREN',
    'RPAREN',
    'COMMA',
    'INT',
    'VARCHAR',
    'PRIMARY',
    'KEY',
    'VALUES',
    'SET',
    'WHERE',
    'EQUALS',
    'STRING',
    'NUMBER',
    'FROM'
)

reserved = {
    'create': 'CREATE',
    'database': 'DATABASE',
    'use': 'USE',
    'table': 'TABLE',
    'insert': 'INSERT',
    'into': 'INTO',
    'update': 'UPDATE',
    'delete': 'DELETE',
}

tokens = tokens + tuple(reserved.values())

# Reglas de expresión regular para tokens simples
t_SEMICOLON = r';'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COMMA = r','
t_EQUALS = r'='

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'ID')
    return t

def t_STRING(t):
    r'\'[^\']*\''
    t.value = t.value[1:-1]  # Remover comillas
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

t_ignore = ' \t'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    raise SyntaxError(f"Illegal character '{t.value[0]}' at line {t.lineno}")

lexer = lex.lex()

# Reglas de análisis sintáctico
def p_statement_create_database(p):
    'statement : CREATE DATABASE ID SEMICOLON'
    p[0] = ('CREATE DATABASE', p[3])

def p_statement_use_database(p):
    'statement : USE ID SEMICOLON'
    p[0] = ('USE DATABASE', p[2])

def p_statement_create_table(p):
    'statement : CREATE TABLE ID LPAREN column_definitions RPAREN SEMICOLON'
    p[0] = ('CREATE TABLE', p[3], p[5])

def p_column_definitions(p):
    '''column_definitions : column_definitions COMMA column_definition
                          | column_definition'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_column_definition(p):
    'column_definition : ID ID constraints'
    p[0] = (p[1], p[2], p[3])

def p_constraints(p):
    '''constraints : PRIMARY KEY
                   | empty'''
    if len(p) == 3:
        p[0] = ('PRIMARY KEY',)
    else:
        p[0] = ()

def p_statement_insert_into(p):
    'statement : INSERT INTO ID LPAREN ID RPAREN VALUES LPAREN value_list RPAREN SEMICOLON'
    p[0] = ('INSERT INTO', p[3], p[5], p[9])

def p_value_list(p):
    '''value_list : value_list COMMA value
                  | value'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_value(p):
    '''value : NUMBER
             | STRING'''
    p[0] = p[1]

def p_statement_update(p):
    'statement : UPDATE ID SET ID EQUALS value WHERE ID EQUALS value SEMICOLON'
    p[0] = ('UPDATE', p[2], p[4], p[6], p[8], p[10])

def p_statement_delete(p):
    'statement : DELETE FROM ID WHERE ID EQUALS value SEMICOLON'
    p[0] = ('DELETE', p[3], p[5], p[7])

def p_empty(p):
    'empty :'
    p[0] = None

def p_error(p):
    if p:
        raise SyntaxError(f"Syntax error at '{p.value}'")
    else:
        raise SyntaxError("Syntax error at EOF")

parser = yacc.yacc()

def validate_sql(sql):
    try:
        parser.parse(sql)
        return {'valid': True}
    except SyntaxError as e:
        return {'valid': False, 'error': str(e)}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/validate', methods=['POST'])
def validate():
    sql_queries = request.json.get('queries', [])
    validation_results = []
    for query in sql_queries:
        validation_results.append(validate_sql(query))
    return jsonify(validation_results)

if __name__ == '__main__':
    app.run(debug=True)
