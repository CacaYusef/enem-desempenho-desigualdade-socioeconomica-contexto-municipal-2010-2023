# Dados brutos

Este diretório é imutável. O conteúdo binário/volumoso é ignorado pelo Git; este
arquivo registra o inventário necessário para reconhecê-lo.

## ENEM 2023

Diretório recebido: `microdados_enem_2023/`

- 83 arquivos; 1.923.184.307 bytes no total na inspeção inicial.
- Fonte declarada pelo pacote: microdados do ENEM 2023/INEP.
- Data e URL de aquisição: não documentadas.
- CSV principal: delimitador `;`, 76 colunas e codificação Windows-1252
  validada na amostra inicial; não é UTF-8.

Arquivos centrais e SHA-256:

| Arquivo | Bytes | SHA-256 |
|---|---:|---|
| `DADOS/MICRODADOS_ENEM_2023.csv` | 1.777.162.429 | `C8B1FAE0A97B6AC826D950D16696EFA3D89C133B0165128AADD2997C2315B666` |
| `DADOS/ITENS_PROVA_2023.csv` | 330.709 | `27B19A80C78071A3EF49B87AA3B89B17CFBEFFCF1FA4F1899913D36A54652468` |
| `DICIONÁRIO/Dicionário_Microdados_Enem_2023.xlsx` | 32.897 | `1411AD89784F7F960DC1C1FC13B0D22EEE696E2613CB762072665FA547AE6CF6` |

Os caminhos acima são relativos ao diretório interno
`microdados_enem_2023/microdados_enem_2023/`.

## Fontes adquiridas depois da inicialização

Os pacotes ENEM 2010–2022 estão em `enem/ANO/` e as fontes IBGE, INEP e
Ipeadata em `municipal/`. O inventário autoritativo não é duplicado neste
arquivo: cada aquisição possui URL, data, tamanho, SHA-256 e, para ZIPs,
inventário/CRC em `../../docs/sources/manifests/`. Os catálogos de consultas
municipais ficam em `../../docs/sources/municipal_catalog.json` e
`../../docs/sources/supplement_catalog.json`.

Os arquivos nesta árvore não devem ser alterados ou sobrescritos. Os scripts
validam o hash de um raw já registrado e interrompem diante de divergência.
