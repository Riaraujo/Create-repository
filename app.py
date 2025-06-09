from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import json
import os

app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas

# Configuração do banco de dados
DB_CONFIG = {
    'dbname': 'railway',
    'user': 'postgres',
    'password': 'IAPnZRQzdcmnUAsxGhIlfgjnRAtYccba',
    'host': 'mainline.proxy.rlwy.net',
    'port': '18484'
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    return conn

# Inicializar o banco de dados se necessário
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar se as tabelas já existem
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'pastas'
        );
    """)
    
    if not cursor.fetchone()[0]:
        # Criar tabelas
        with open('schema.sql', 'r') as f:
            cursor.execute(f.read())
        
        print("Banco de dados inicializado com sucesso!")
    else:
        print("Banco de dados já inicializado.")
    
    cursor.close()
    conn.close()

# Rotas para pastas
@app.route('/api/pastas', methods=['GET'])
def get_pastas():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM pastas ORDER BY nome")
    pastas = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(pastas)

@app.route('/api/pastas', methods=['POST'])
def create_pasta():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "INSERT INTO pastas (nome) VALUES (%s) RETURNING *",
        (data['nome'],)
    )
    nova_pasta = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(nova_pasta)

@app.route('/api/pastas/<int:pasta_id>', methods=['DELETE'])
def delete_pasta(pasta_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Atualizar provas para remover referência à pasta
    cursor.execute(
        "UPDATE provas SET pasta_id = NULL WHERE pasta_id = %s",
        (pasta_id,)
    )
    # Excluir a pasta
    cursor.execute(
        "DELETE FROM pastas WHERE id = %s",
        (pasta_id,)
    )
    cursor.close()
    conn.close()
    return jsonify({"message": "Pasta excluída com sucesso"})

# Rotas para provas
@app.route('/api/provas', methods=['GET'])
def get_provas():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT p.*, 
               (SELECT COUNT(*) FROM questoes q WHERE q.prova_id = p.id) as questoes_count
        FROM provas p
        ORDER BY p.nome
    """)
    provas = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(provas)

@app.route('/api/provas/pasta/<int:pasta_id>', methods=['GET'])
def get_provas_by_pasta(pasta_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT p.*, 
               (SELECT COUNT(*) FROM questoes q WHERE q.prova_id = p.id) as questoes_count
        FROM provas p
        WHERE p.pasta_id = %s
        ORDER BY p.nome
    """, (pasta_id,))
    provas = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(provas)

@app.route('/api/provas', methods=['POST'])
def create_prova():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "INSERT INTO provas (nome, descricao, pasta_id) VALUES (%s, %s, %s) RETURNING *",
        (data['nome'], data.get('descricao', ''), data.get('pasta_id'))
    )
    nova_prova = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(nova_prova)

@app.route('/api/provas/<int:prova_id>', methods=['PUT'])
def update_prova(prova_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "UPDATE provas SET nome = %s, descricao = %s, pasta_id = %s WHERE id = %s RETURNING *",
        (data['nome'], data.get('descricao', ''), data.get('pasta_id'), prova_id)
    )
    prova_atualizada = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(prova_atualizada)

@app.route('/api/provas/<int:prova_id>', methods=['DELETE'])
def delete_prova(prova_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM provas WHERE id = %s",
        (prova_id,)
    )
    cursor.close()
    conn.close()
    return jsonify({"message": "Prova excluída com sucesso"})

# Rotas para questões
@app.route('/api/questoes/prova/<int:prova_id>', methods=['GET'])
def get_questoes_by_prova(prova_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT * FROM questoes WHERE prova_id = %s ORDER BY id",
        (prova_id,)
    )
    questoes = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(questoes)

@app.route('/api/questoes', methods=['POST'])
def create_questao():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Converter estrutura_json para string JSON se necessário
    estrutura_json = data.get('estrutura_json')
    if isinstance(estrutura_json, dict):
        estrutura_json = json.dumps(estrutura_json)
    
    cursor.execute(
        """
        INSERT INTO questoes 
        (prova_id, disciplina, materia, assunto, conteudo, topico, ano, instituicao, resposta, estrutura_json) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
        RETURNING *
        """,
        (
            data['prova_id'], 
            data['disciplina'], 
            data['materia'], 
            data['assunto'], 
            data.get('conteudo', ''), 
            data.get('topico', ''), 
            data.get('ano'), 
            data.get('instituicao', ''), 
            data['resposta'], 
            estrutura_json
        )
    )
    nova_questao = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(nova_questao)

@app.route('/api/questoes/<int:questao_id>', methods=['PUT'])
def update_questao(questao_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Converter estrutura_json para string JSON se necessário
    estrutura_json = data.get('estrutura_json')
    if isinstance(estrutura_json, dict):
        estrutura_json = json.dumps(estrutura_json)
    
    cursor.execute(
        """
        UPDATE questoes SET 
        disciplina = %s, materia = %s, assunto = %s, conteudo = %s, 
        topico = %s, ano = %s, instituicao = %s, resposta = %s, estrutura_json = %s
        WHERE id = %s 
        RETURNING *
        """,
        (
            data['disciplina'], 
            data['materia'], 
            data['assunto'], 
            data.get('conteudo', ''), 
            data.get('topico', ''), 
            data.get('ano'), 
            data.get('instituicao', ''), 
            data['resposta'], 
            estrutura_json,
            questao_id
        )
    )
    questao_atualizada = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(questao_atualizada)

@app.route('/api/questoes/<int:questao_id>', methods=['DELETE'])
def delete_questao(questao_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM questoes WHERE id = %s",
        (questao_id,)
    )
    cursor.close()
    conn.close()
    return jsonify({"message": "Questão excluída com sucesso"})

if __name__ == '__main__':
    # Inicializar o banco de dados
    init_db()
    # Iniciar o servidor Flask
    app.run(host='0.0.0.0', port=5000, debug=True)

