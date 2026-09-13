# Modelo entidade-relacionamento

Atualizado em 13/09/2026, junto com a migração `001_titular_sem_documento.sql`.

```mermaid
erDiagram
    tb_fontes ||--o{ tb_projetos : referencia
    tb_fontes ||--o{ tb_intensidade_energetica : referencia
    tb_fontes ||--o{ tb_projecoes : referencia
    tb_empresas ||--o{ tb_projetos : titular_de
    tb_minerais ||--o{ tb_projetos : substancia_de
    tb_minerais ||--o{ tb_intensidade_energetica : tem
    tb_minerais ||--o{ tb_projecoes : projeta
    tb_projetos ||--o{ tb_projeto_poligono : delimitado_por
    tb_projetos ||--o{ tb_projeto_municipio : localizado_em
    tb_municipios ||--o{ tb_projeto_municipio : contem
    tb_projetos ||--o{ tb_projecoes : gera

    tb_fontes {
        varchar source_id PK
        varchar titulo
        varchar instituicao
        varchar cobertura
    }
    tb_municipios {
        varchar codigo_ibge PK
        varchar nome_municipio
    }
    tb_minerais {
        int mineral_id PK
        int id_substancia_anm UK "dicionário oficial da ANM"
        varchar mineral_name
    }
    tb_empresas {
        int empresa_id PK
        varchar nome_empresa_normalizado UK "chave: as fontes dão o nome, não o documento"
        varchar documento_cnpj_cpf UK "opcional; ausente ou mascarado na origem"
    }
    tb_projetos {
        varchar processo_anm PK
        int empresa_id FK "nulo quando a fonte não nomeia titular"
        varchar titular_nome "como veio da origem"
        int mineral_id FK
        varchar fase
        int poligonos "quantos polígonos o processo tem"
        decimal area_ha "só quando há um único polígono"
    }
    tb_projeto_poligono {
        int poligono_id PK
        varchar processo_anm FK
        varchar id_poligono_origem "repete na origem; atributo, nunca chave"
        decimal area_ha
    }
    tb_projecoes {
        int id PK
        varchar processo_anm FK
        int year
        enum scenario
        decimal projected_production
        varchar unidade_producao
    }
```

## Três decisões que o diagrama registra

**A empresa é chaveada pelo nome normalizado.** O shapefile cadastral traz o titular só pelo nome, e o CSV de rodadas traz CPF/CNPJ mascarado. Exigir documento obrigaria a inventá-lo para carregar qualquer linha real.

**Polígono tem tabela própria.** Um processo pode ter mais de cem polígonos. Usar o processo como chave única descartaria 772 das 17.428 linhas do shapefile de Goiás.

**`area_ha` do processo só é preenchida com um único polígono.** Polígonos podem se sobrepor, então somá-los produziria superfície inexistente. Com vários, a área fica em `tb_projeto_poligono` e o total não é declarado.
