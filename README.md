# RAG Application - Augusta Labs Challenge

## Pré-requisitos
- [Docker Desktop](https://www.docker.com/products/docker-desktop) instalado e em execução

## Instalação / Uso
```bash
# 1. Clone o repositório
git clone https://github.com/tessimago/AugustaLabsChallenge.git
cd AugustaLabsChallenge

# 2. Execute
docker-compose -f docker-compose.production.yml up

# 3. IMPORTANTE - Aguarde a mensagem: "rag_postgres  | PostgreSQL init process complete; ready for start up." (deve demorar entre 1 a 2 minutos)

# 4. Abre um terminal local na pasta fonte do projeto, e roda
python testing.py

  # 4.5 Se nao funcionar, provavelmente tens que fazer pip install -r requirements.txt, se for o caso, recomendo criar um .venv

# 5. Done, podes perguntar sobre incentivos, sobre empresas, e sobre empresas que beneficiam de algum incentivo especifico
```

- O Chat bot chama funcoes dentro da conversa quando necessario, em casos raros ele pode ficar eternamente a chamar funcoes, isso era facil de dar fix mas n tou com paciencia agora
- O Chat bot responde a perguntas como:
  -  "Qual é o incentivo <ID>", e dá info sobre esse incentivo
  -  "Que incentivos são sobre <something>?" e da alguns exemplos de incentivos, junto com os seus IDs que sejam daquilo (fazendo distancia entre as palavras com o titulo do incentivo)
  -  "Que empresas fazem <X>" ou semelhante, vai procurar empresas com similarity search dos embedings, e devolve algumas
  -  "Que empresas beneficiam de <X> incentivo?" ou semelhante, vai fazer a busca das empresas que beneficiam (tambem pelos embedings) do incentivo com o id do incentivo, se ele nao tiver o id, ele vai buscar o id primeiro

## Outras informaçoes
- o CSV das empresas e incentivos chama-se "incentivos_com_empresas.csv"
- a "timeline.txt" relata tudo o que fiz e pensei durante cada momento em que trabalhei neste projeto
- Provavelmente não está tudo 100% como queria que estivesse, talvez as pesquisas na db seriam mais precisas se eu fizesse o uso da "all_data" do csv dos incentivos, mas na altura eu nao o inclui porque achei que nao podia.
- Independente do resultado, foi divertido fazer este projeto, achei bem interessante, gostei de re-aprender um pouco de RAG, é kinda divertido.
- Foi interessante rever Postgres, porque é bem importante lá fora no mundo do trabalho I suppose
- E nao foi interessante rever docker, eu sei que é importante mas eu nunca me dou bem com setup destas coisas assim, dá me sempre erros que acabo por demorar imenso a resolver..
