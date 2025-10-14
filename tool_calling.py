from api import API
import json
import re
from sql import PostgreSQLManager
from copy import deepcopy

PROMPT_TO_COMPLETE = """\n
[System: Continue your previous response]
Your response so far was: {response}

Now you have this information: {info}

If the information is relevant for the response, then answer accordingly, if not, be honest and say you didn't find relevant information to answer.
Only mention the relevant information.
If you found the information you needed, reference some info about it even if briefly.
For example if you found some incentive, mention what incentive is, if you find a relevant company, mention its name, etc...
Now complete your response. (Do not write every thing again, just complete the previous response)
"""

database = PostgreSQLManager()
model_helper = API()

def analyze_response(response: str, messages: list, api: API):
    function_call = check_function_call(response)
    
    # Yield the first part of the response
    if function_call is None:
        yield response
        return
    
    # Remove function call from response and yield the text part
    text_part = response[:response.rfind("```json")]
    # print(f"Yielding response part: {text_part[:50]}...")
    yield text_part
    print(f"[DEBUG] Function call: {function_call}")
    # Execute function and yield the result
    function = function_call["function"]
    parameter = function_call["parameter"]
    info = execute_function(function, parameter)
    # Assuming last message is from user..
    messages[-1]["content"] += PROMPT_TO_COMPLETE.format(response=text_part, info=info)
    remaining_of_response = api.converse(messages)

    for p in analyze_response(remaining_of_response, messages, api):
        if p:
            yield p


def check_function_call(response: str) -> dict:
    # Check if there is a json on the response
    json_pattern = r'```json\n(.*?)\n```'
    json_match = re.search(json_pattern, response, re.DOTALL)
    if not json_match:
        return None
    json_string = json_match.group(1)
    json_jsn = json.loads(json_string)
    if "function" in json_jsn and "parameter" in json_jsn:
        return json_jsn
    return None

def execute_function(function: str, parameter: str) -> str:
    if   function == "get_incentive_by_id":
        return get_incentive_by_id(parameter)
    elif function == "get_incentive_by_title":
        return get_incentive_by_title(parameter)
    elif function == "get_company_by_title":
        return get_company_by_title(parameter)
    elif function == "get_companies_by_incentive":
        return get_companies_by_incentive(parameter)
    else:
        return "Function not found"

def get_incentive_by_id(id: str) -> str:
    try:
        id = int(id)
        if id < 0:
            return "Invalid ID"
        result = database.query_incentives_by_id(id)
        if result:
            return f"""
                Incentive ID: {result['incentive_id']}
                Title: {result['title']}
                Description: {result['description']}
                AI Description: {result['ai_description']}
                Document URLs: {result['document_urls']}
                Date Publication: {result['date_publication']}
                Start Date: {result['start_date']}
                End Date: {result['end_date']}
                Total Budget: {result['total_budget']}
                Source Link: {result['source_link']}
            """
        else:
            return "Incentive not found"
    except ValueError:
        return "Invalid ID"
    except Exception as e:
        print(f"Error querying database: {e}")
        return "Error querying database"

def get_incentive_by_title(title: str) -> str:
    try:
        result = database.query_incentives_by_name(title)
        if result:
            results_str = "Possible results:"
            for r in result:
                results_str += f"""\n
                    Incentive ID: {r['incentive_id']}
                    Title: {r['title']}
                    Description: {r['description']}
                    AI Description: {r['ai_description']}
                """
            return results_str
        else:
            return "Incentive not found"
    except Exception as e:
        print(f"Error querying database: {e}")
        return "Error querying database"

def get_company_by_title(title: str, top_k: int = 3) -> str:
    try:
        result = database.query_companies_with_embedding(title, top_k=top_k)
        if result:
            results_str = "Possible results:"
            for r in result:
                results_str += f"""\n
                    Company Name: {r['company_name']}
                    CAE Primary Label: {r['cae_primary_label']}
                    Trade Description Native: {r['trade_description_native']}
                    Website: {r['website']}
                """
            return results_str
        else:
            return "Company not found"
    except Exception as e:
        print(f"Error querying database: {e}")
        return "Error querying database"

def get_companies_by_incentive(incentive_id: str) -> str:
    incentive_info = get_incentive_by_id(incentive_id)
    prompt = f"""
    You have this incentive information: \n{incentive_info}\n
    Now create a small query focusing on key words of this incentive. This query will later be used to search in a database for companies that are related to this incentive.
    Examples of querys: 
        "Instituição Religiosa"
        "Padaria, empresa de produção de pães"
        "Empresas de distribuição de gás"
        "Estradas, Rodovias, Escolas"
        "Digitalização, Tecnologia, Cidadãos"
    Do not put very long queries, do not surpass 3 words on the query (excluding articles).
    Do not put any irrelevant information like "Isenção Fiscal" since its a query to find companies, and those keywords do not help on that.
    Now generate your query (in portuguese).
    Your response may only be the generated query, nothing else. NO bold, and NO prefix like "Query: ..."
    """
    query = model_helper.call(prompt, system="You are a helpful assistant to create a query for a database.")
    print(f"[DEBUG] Query: {query}")
    companies = get_company_by_title(query, 5)
    return companies


if __name__ == "__main__":
    test_string = """
        Vou procurar empresas relacionadas com distribuição de gás na base de dados.

```json
    {
    "function": "get_company_by_title",
    "parameter": "distribuição de gás"
    }
```
    """
    print(check_function_call(test_string))
