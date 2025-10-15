from tool_calling import get_companies_by_incentive
from sql import PostgreSQLManager, DB_CONFIG
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_incentive(incentive):
    """Processa um único incentivo, obtendo empresas e retornando dados formatados."""
    incentive_id, title = incentive
    companies = get_companies_by_incentive(incentive_id, on_string=False)
    company_names = [c['company_name'] for c in companies[:5]]  # Limita a 5 empresas
    company_names.extend([''] * (5 - len(company_names)))  # Preenche com vazios, se necessário
    return [incentive_id, title] + company_names

if __name__ == "__main__":
    db = PostgreSQLManager(**DB_CONFIG)
    
    # Obter todos os incentivos
    results = db.general_query("SELECT incentive_id, title FROM incentives")
    print(len(results))
    exit()
    # Inicializar uma lista de dados a serem processados
    incentives = [(result[0], result[1]) for result in results]
    
    # Criar uma lista para armazenar os resultados
    data = []
    
    # Usar ThreadPoolExecutor para paralelizar o processo
    with ThreadPoolExecutor(max_workers=5) as executor:  # Ajuste o número de workers conforme necessário
        futures = {executor.submit(process_incentive, incentive): incentive for incentive in incentives}
        
        # Barra de progresso com tqdm
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processando incentivos"):
            data.append(future.result())
    
    # Criar o DataFrame e salvar como CSV
    df = pd.DataFrame(data, columns=['incentive_id', 'title', 'company_1', 'company_2', 'company_3', 'company_4', 'company_5'])
    df.to_csv('incentivos_com_empresas.csv', index=False)

    print("CSV gerado com sucesso!")
