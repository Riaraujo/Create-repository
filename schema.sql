-- Esquema do banco de dados para o sistema de provas

-- Tabela de pastas
CREATE TABLE pastas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de provas
CREATE TABLE provas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    pasta_id INTEGER REFERENCES pastas(id) ON DELETE SET NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de questões
CREATE TABLE questoes (
    id SERIAL PRIMARY KEY,
    prova_id INTEGER NOT NULL REFERENCES provas(id) ON DELETE CASCADE,
    disciplina VARCHAR(100) NOT NULL,
    materia VARCHAR(100) NOT NULL,
    assunto VARCHAR(100) NOT NULL,
    conteudo VARCHAR(100),
    topico VARCHAR(100),
    ano INTEGER,
    instituicao VARCHAR(100),
    resposta CHAR(1) NOT NULL,
    estrutura_json JSONB NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para melhorar a performance
CREATE INDEX idx_questoes_prova_id ON questoes(prova_id);
CREATE INDEX idx_provas_pasta_id ON provas(pasta_id);
CREATE INDEX idx_questoes_disciplina ON questoes(disciplina);
CREATE INDEX idx_questoes_materia ON questoes(materia);
CREATE INDEX idx_questoes_assunto ON questoes(assunto);

