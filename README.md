# RAG Application - Augusta Labs Challenge

## Prerequisites

* [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running

## Installation / Usage

```bash
# 1. Clone the repository
git clone https://github.com/tessimago/AugustaLabsChallenge.git
cd AugustaLabsChallenge

# 2. Run
docker-compose -f docker-compose.production.yml up

# 3. IMPORTANT - Wait for the message: "rag_postgres  | PostgreSQL init process complete; ready for start up." (this should take between 1 to 2 minutes)

# 4. Open a local terminal in the project’s root folder and run
python testing.py

  # 4.5 If it doesn’t work, you probably need to run pip install -r requirements.txt. In that case, I recommend creating a .venv first.

# 5. Done! You can now ask about incentives, companies, or which companies benefit from a specific incentive.
```

* The chatbot calls functions within the conversation when necessary. In rare cases, it might get stuck in an infinite loop of function calls — that’s easy to fix, but I don’t have the patience for it right now.
* The chatbot can answer questions like:

  * “What is incentive <ID>?” — and it provides info about that incentive.
  * “Which incentives are about <something>?” — it lists some incentives related to that topic along with their IDs (based on word similarity with the incentive title).
  * “Which companies do <X>” or similar — it searches for companies using embedding similarity and returns some results.
  * “Which companies benefit from <X> incentive?” or similar — it looks for companies that benefit (also via embeddings) from the incentive with that ID. If it doesn’t have the ID yet, it first searches for it.

## Other Information

* The CSV containing companies and incentives is named **“incentivos_com_empresas.csv”**.
* The file **“timeline.txt”** documents everything I did and thought during each stage of this project.
* It’s probably not 100% the way I wanted — the database searches might’ve been more accurate if I had used the “all_data” column from the incentives CSV, but at the time I didn’t include it because I thought I couldn’t (I only did this in roughtly 2 days so).
* Regardless of the outcome, this project was fun to make — I found it really interesting and enjoyed re-learning some RAG concepts. It’s kinda fun, honestly.
* It was also nice to revisit PostgreSQL since it’s pretty important out there in the job market, I suppose.
* What *wasn’t* nice was dealing with Docker again — I know it’s important, but I never get along with setups like these. It always throws errors that take me forever to fix..
