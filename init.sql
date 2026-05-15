CREATE TABLE IF NOT EXISTS projetos (
    id                  SERIAL PRIMARY KEY,
    numero              VARCHAR(20)  NOT NULL UNIQUE,
    titulo              VARCHAR(500) NOT NULL,
    data_inicio         DATE,
    data_fim            DATE,
    situacao            VARCHAR(100),
    resumo              TEXT,
    url                 VARCHAR(500),
    responsavel         VARCHAR(255),
    classificacao_cnpq  VARCHAR(255),
    linha_pesquisa      VARCHAR(255),
    tipo_orientacao     VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS topicos (
    id      SERIAL PRIMARY KEY,
    nome    VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS projeto_topicos (
    id          SERIAL PRIMARY KEY,
    projeto_id  INT NOT NULL REFERENCES projetos(id) ON DELETE CASCADE,
    topico_id   INT NOT NULL REFERENCES topicos(id)  ON DELETE CASCADE,
    UNIQUE (projeto_id, topico_id)
);

CREATE INDEX IF NOT EXISTS idx_projetos_numero       ON projetos(numero);
CREATE INDEX IF NOT EXISTS idx_topicos_nome          ON topicos(nome);
CREATE INDEX IF NOT EXISTS idx_projeto_topicos_proj  ON projeto_topicos(projeto_id);
CREATE INDEX IF NOT EXISTS idx_projeto_topicos_top   ON projeto_topicos(topico_id);