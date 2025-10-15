import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
import pandas as pd
import sys
from embedder import OpenAIEmbeder
import tiktoken
from tqdm import tqdm
import time
import os
import json


DATABASE_NAME = "augusta_labs_db"

class PostgreSQLManager:
    def __init__(self, host=os.getenv('DB_HOST', 'localhost'), user='postgres', password='123', port=5432):
        self.connection_params = {
            'host': host,
            'user': user,
            'password': password,
            'port': port
        }
        # print(f"Connection parameters: \n{json.dumps(self.connection_params, indent=4)}")
        self.embedder = OpenAIEmbeder()
    
    def get_connection(self, database='postgres', autocommit=False):
        """Establish connection to PostgreSQL database"""
        try:
            conn_params = self.connection_params.copy()
            conn_params['database'] = database
            
            conn = psycopg2.connect(**conn_params)
            if autocommit:
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            return conn
        except psycopg2.Error as e:
            print(f"Connection error: {e}")
            return None
    
    def database_exists(self):
        """Check if database already exists"""
        conn = self.get_connection(autocommit=True)
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                (DATABASE_NAME,)
            )
            exists = cursor.fetchone() is not None
            cursor.close()
            return exists
        except psycopg2.Error as e:
            print(f"Error checking database existence: {e}")
            return False
        finally:
            conn.close()
    
    def create_database(self):
        """Create a new database"""
        if self.database_exists(DATABASE_NAME):
            print(f"Database '{DATABASE_NAME}' already exists.")
            return True
        
        conn = self.get_connection(autocommit=True)
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            create_query = sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(DATABASE_NAME)
            )
            cursor.execute(create_query)
            print(f"✅ Database '{DATABASE_NAME}' created successfully!")
            return True
        except psycopg2.Error as e:
            print(f"❌ Error creating database: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def create_table(self, table_name, table_schema):
        """Create a table in the specified database"""
        conn = self.get_connection(database=DATABASE_NAME)
        if not conn:
            return False
        # Check if table already exists
        try:
            cursor = conn.cursor()
            cursor.execute(table_schema)
            conn.commit()
            print(f"✅ Table '{table_name}' created successfully!")
            return True
        except psycopg2.Error as e:
            print(f"❌ Error creating table: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def verify_database(self):
        """Verify database creation and contents"""
        conn = self.get_connection(database=DATABASE_NAME)
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = cursor.fetchall()
            print(f"📊 Tables in database: {[table[0] for table in tables]}")
            # Count incentives
            cursor.execute("SELECT COUNT(*) FROM incentives")
            incentive_count = cursor.fetchone()[0]
            print(f"👥 Number of incentives: {incentive_count}")

            # Show sample incentives
            cursor.execute("SELECT * FROM incentives LIMIT 5")
            incentives = cursor.fetchall()
            print("Sample incentives:")
            for incentive in incentives:
                print(f"  - ID: {incentive[0]}, Title: {incentive[1]}, Description: {incentive[2]}")

            return True
        except psycopg2.Error as e:
            print(f"❌ Error verifying database: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def insert_csv_incentives(self, file_path: str):
        """Insert multiple incentives from a CSV file into the incentives table"""
        incentives = read_csv(file_path)
        if not incentives:
            print("No incentives to insert.")
            return False
        
        conn = self.get_connection(database=DATABASE_NAME)
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            insert_query = """
                INSERT INTO incentives (incentive_id, title, description, ai_description, document_urls, date_publication, start_date, end_date, total_budget, source_link)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            for data in incentives:
                cursor.execute(insert_query, (
                    data.get("incentive_project_id"),
                    data.get("title"),
                    data.get("description"), 
                    data.get("ai_description") if not isinstance(data.get("ai_description"), float) else None,
                    data.get("document_urls") if not isinstance(data.get("document_urls"), float) else None,
                    data.get("date_publication") if not isinstance(data.get("date_publication"), float) else None,
                    data.get("start_date") if data.get("start_date") else None,
                    data.get("end_date") if data.get("end_date") else None,
                    data.get("total_budget") if data.get("total_budget") else None,
                    data.get("source_link") if data.get("source_link") else None
                ))
            conn.commit()
            print(f"✅ Inserted {len(incentives)} incentives from CSV successfully!")
            return True
        except psycopg2.Error as e:
            print(f"❌ Error inserting CSV data: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def insert_csv_companies(self, file_path: str, chunk_size: int = 1000):
        """Insert multiple companies from a CSV file into the companies table in chunks"""
        companies = read_csv(file_path)
        if not companies:
            print("No companies to insert.")
            return False
        
        conn = self.get_connection(database=DATABASE_NAME)
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            
            # Get existing company names to skip them
            existing_companies = self.get_existing_company_names(cursor)
            print(f"Found {len(existing_companies)} existing companies in database")
            
            # Filter out companies that already exist
            companies_to_insert = [
                c for c in companies 
                if c.get("company_name") not in existing_companies
            ]
            
            if not companies_to_insert:
                print("✅ All companies already exist in database!")
                return True
                
            print(f"Will insert {len(companies_to_insert)} new companies in chunks of {chunk_size}")
            
            # Process in chunks
            total_inserted = 0
            for i in range(0, len(companies_to_insert), chunk_size):
                chunk = companies_to_insert[i:i + chunk_size]
                chunk_num = (i // chunk_size) + 1
                total_chunks = (len(companies_to_insert) + chunk_size - 1) // chunk_size
                
                print(f"\n📦 Processing chunk {chunk_num}/{total_chunks} ({len(chunk)} companies)...")
                
                # Add embeddings for this chunk only
                self.add_embeddings_companies(chunk)
                # Insert this chunk
                insert_query = """
                    INSERT INTO companies (company_name, cae_primary_label, trade_description_native, website, embeddings)
                    VALUES (%s, %s, %s, %s, %s)
                """
                for data in chunk:
                    cursor.execute(insert_query, (
                        data.get("company_name"),
                        data.get("cae_primary_label"), 
                        data.get("trade_description_native") if not isinstance(data.get("trade_description_native"), float) else None,
                        data.get("website") if not isinstance(data.get("website"), float) else None,
                        data.get("embeddings") if not isinstance(data.get("embeddings"), float) else None
                    ))
                
                conn.commit()
                total_inserted += len(chunk)
                print(f"✅ Chunk {chunk_num}/{total_chunks} inserted successfully! (Total: {total_inserted}/{len(companies_to_insert)})")
            
            print(f"\n🎉 All done! Inserted {total_inserted} companies total.")
            return True
            
        except psycopg2.Error as e:
            print(f"❌ Error inserting chunk: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def get_existing_company_names(self, cursor) -> set:
        """Get set of company names that already exist in database"""
        try:
            cursor.execute("SELECT company_name FROM companies")
            return {row[0] for row in cursor.fetchall()}
        except psycopg2.Error as e:
            print(f"⚠️ Could not fetch existing companies: {e}")
            return set()

    def add_embeddings_companies(self, companies: list):
        """Add embeddings to a list of companies (modifies in place)"""
        docs_to_embed = []
        for company in companies:
            primary_label = company.get('cae_primary_label') if not isinstance(company.get('cae_primary_label'), float) else ''
            trade_description = company.get('trade_description_native') if not isinstance(company.get('trade_description_native'), float) else ''
            doc = f"{company['company_name']}\n{primary_label}\n{trade_description}"
            docs_to_embed.append(doc)
        
        embeddings_response = self.embedder.get_embedding(docs_to_embed, model="text-embedding-3-small")
        embeddings = embeddings_response['embedding']
        
        for i, company in enumerate(companies):
            company["embeddings"] = embeddings[i].embedding
        
        print(f"✅ Added embeddings to {len(companies)} companies in this chunk.")
        return companies


    def check_pgvector(self):
        query = "SELECT * FROM pg_available_extensions WHERE name = 'vector';"
        conn = self.get_connection(database=DATABASE_NAME)
        if not conn:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            result = cursor.fetchone()
            if result:
                print("✅ pgvector is installed.")
            else:
                print("❌ pgvector is not installed.")
            return result is not None
        except psycopg2.Error as e:
            print(f"Error checking pgvector: {e}")
            return False

    def query_companies_with_embedding(self, user_query: str, top_k: int = 5):
        """Query companies based on embedding similarity with the query string"""
        time_start = time.time()
        conn = self.get_connection(database=DATABASE_NAME)
        
        # embedding for the query
        embedding_query = self.embedder.get_embedding(user_query, model="text-embedding-3-small")['embedding'][0].embedding
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            # Assuming the embedding is stored as a string in the database
            # Adjust the query to use the embedding column and the L2 distance function
            query = """
                SELECT 
                    company_name, 
                    cae_primary_label, 
                    trade_description_native, 
                    website,
                    embeddings <-> %s::vector as distance_score
                FROM companies
                ORDER BY distance_score ASC
                LIMIT %s
            """
            cursor.execute(query, (embedding_query, top_k))
            results = cursor.fetchall()
            print(f"✅ Query executed successfully!")

            # ✅ Convert to list/dict with similarity score
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'company_name': row[0],
                    'cae_primary_label': row[1],
                    'trade_description_native': row[2],
                    'website': row[3],
                    'distance_score': row[4]
                })
            time_end = time.time() - time_start
            # print(f"🕒 Query took {time_end:.2f} seconds.")
            return formatted_results
        except psycopg2.Error as e:
            print(f"❌ Error executing query: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def query_incentives_by_id(self, id: int):
        """Query incentives by ID"""
        conn = self.get_connection(database=DATABASE_NAME)
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    incentive_id,
                    title,
                    description,
                    ai_description,
                    document_urls,
                    date_publication,
                    start_date,
                    end_date,
                    total_budget,
                    source_link
                FROM incentives
                WHERE incentive_id = %s
            """
            cursor.execute(query, (id,))
            result = cursor.fetchone()
            if result:
                print(f"✅ Query executed successfully!")
                return {
                    'incentive_id': result[0],
                    'title': result[1],
                    'description': result[2],
                    'ai_description': result[3],
                    'document_urls': result[4],
                    'date_publication': result[5],
                    'start_date': result[6],
                    'end_date': result[7],
                    'total_budget': result[8],
                    'source_link': result[9]
                }
            else:
                print(f"❌ No incentive found with ID {id}")
                return None
        except psycopg2.Error as e:
            print(f"❌ Error executing query: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def query_incentives_by_name(self, incentive_title: str, threshold: float = 0.0):
        """Query incentives by name using fuzzy matching with trigram similarity"""
        conn = self.get_connection(database=DATABASE_NAME)
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            
            query = """
                SELECT
                    incentive_id,
                    title,
                    description,
                    ai_description,
                    document_urls,
                    date_publication,
                    start_date,
                    end_date,
                    total_budget,
                    source_link,
                    similarity(title, %s) as similarity_score
                FROM incentives
                WHERE similarity(title, %s) > %s
                ORDER BY similarity_score DESC
                LIMIT 10
            """
            
            cursor.execute(query, (incentive_title, incentive_title, threshold))
            results = cursor.fetchall()
            if results:
                print(f"✅ Query executed successfully!")
                formatted_results = []
                for row in results:
                    formatted_results.append({
                        "incentive_id": row[0],
                        "title": row[1],
                        "description": row[2], 
                        "ai_description": row[3],
                        "document_urls": row[4],
                        "date_publication": row[5],
                        "start_date": row[6],
                        "end_date": row[7],
                        "total_budget": row[8],
                        "source_link": row[9],
                        "similarity_score": row[-1]
                    })
                return formatted_results
            else:
                print(f"❌ No incentive found with name {incentive_title}")
                return None
        except psycopg2.Error as e:
            print(f"❌ Error executing query: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def general_query(self, query: str):
        """Execute a general query on the database"""
        conn = self.get_connection(database=DATABASE_NAME)
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            print(f"✅ Query executed successfully!")
            return results
        except psycopg2.Error as e:
            print(f"❌ Error executing query: {e}")
            return False
        finally:
            cursor.close()
            conn.close()


TEST_COMPANIES_N = 1000
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': 'postgres',
    'password': '123',
    'port': 5432
}
# print(f"📊 Database configuration:\n{json.dumps(DB_CONFIG, indent=4)}")
    

def read_csv(file_path: str, test: bool = False) -> list:
    """Read values from a CSV file and return as a list of dictionaries"""
    try:
        df = pd.read_csv(file_path)
        values = df.to_dict(orient='records')
        if test:
            values = values[:TEST_COMPANIES_N]  # Limit to first N records for testing
        print(f"📥 Loaded {len(values)} values from CSV.")
        return values
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return []

def check_token_number_companies():
    companies = read_csv('csvs/companies.csv')
    encoding = tiktoken.encoding_for_model("text-embedding-3-small")
    all_tokens = 0
    tokens = []
    max_company = ""
    max_tokens = 0
    min_tokens = 0
    min_company = ""
    for company in tqdm(companies):
        primary_label = company.get('cae_primary_label') if not isinstance(company.get('cae_primary_label'), float) else ''
        trade_description = company.get('trade_description_native') if not isinstance(company.get('trade_description_native'), float) else ''
        doc = f"{company['company_name']}\n{primary_label}\n{trade_description}"
        tokens_value = encoding.encode(doc)
        tokens.append(len(tokens_value))
        all_tokens += len(tokens_value)
        if len(tokens_value) > max_tokens:
            max_tokens = len(tokens_value)
            max_company = company['company_name']
        if min_tokens == 0 or len(tokens_value) < min_tokens:
            min_tokens = len(tokens_value)
            min_company = company['company_name']


    tokens.sort()
    print(f"Total tokens for all companies: {all_tokens}")
    print(f"Estimated cost for embeddings: ${all_tokens * 0.02 / 1_000_000:.6f}")
    print(f"Average tokens per company: {all_tokens / len(companies)}")
    # Min and Max
    print(f"Min tokens for a company: {min(tokens)}")
    print(f"Company with min tokens ({min_tokens}): {min_company}")
    print(f"Max tokens for a company: {max(tokens)}")
    print(f"Company with max tokens ({max_tokens}): {max_company}")

    # Print percentiles from 10 to 100
    for p in range(10, 100, 10):
        print(f"{p}th percentile: {tokens[int(len(tokens) * p / 100)]}")

def add_incentives_table(db_manager: PostgreSQLManager):
    # Table schema
    TABLE_INCENTIVES_SCHEMA = """
        CREATE TABLE IF NOT EXISTS incentives (
            incentive_id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            ai_description JSONB,
            document_urls TEXT,
            date_publication DATE,
            start_date DATE,
            end_date DATE,
            total_budget NUMERIC(15,2),
            source_link TEXT
        )
        """
    
    if not db_manager.create_table(DATABASE_NAME, 'incentives', TABLE_INCENTIVES_SCHEMA):
        print("Failed to create table. Exiting.")
        sys.exit(1)
    
    if not db_manager.insert_csv_incentives(DATABASE_NAME, 'csvs/incentives.csv'):
        print("Failed to insert sample data. Exiting.")
        sys.exit(1)

def add_companies_table(db_manager: PostgreSQLManager):
    # Table schema
    TABLE_COMPANIES_SCHEMA = """
        CREATE TABLE IF NOT EXISTS companies (
            company_id SERIAL PRIMARY KEY,
            company_name TEXT NOT NULL,
            cae_primary_label TEXT,
            trade_description_native TEXT,
            website TEXT,
            embeddings VECTOR(1536)
        )
        """

    if not db_manager.create_table(DATABASE_NAME, 'companies', TABLE_COMPANIES_SCHEMA):
        print("Failed to create table. Exiting.")
        sys.exit(1)

    if not db_manager.insert_csv_companies(DATABASE_NAME, 'csvs/companies.csv'):
        print("Failed to insert sample data. Exiting.")
        sys.exit(1)

def main():

    # Initialize database manager
    db_manager = PostgreSQLManager(**DB_CONFIG)
    
    print("🚀 Starting PostgreSQL Database Setup...")
    
    # Step 1: Create database
    if not db_manager.create_database(DATABASE_NAME):
        print("Failed to create database. Exiting.")
        sys.exit(1)

    add_incentives_table(db_manager)
    add_companies_table(db_manager)
    
    # Step 4: Verify everything worked
    print("\n🔍 Verifying database setup...")
    db_manager.verify_database(DATABASE_NAME)
    
    print(f"\n🎉 Database '{DATABASE_NAME}' setup completed successfully!")

def drop_database(db_name, connection_params):
    """Drop a database (use with caution!)"""
    db_manager = PostgreSQLManager(**connection_params)
    
    if not db_manager.database_exists(db_name):
        print(f"Database '{db_name}' does not exist.")
        return
    
    confirm = input(f"⚠️  Are you sure you want to drop database '{db_name}'? (yes/no): ")
    if confirm.lower() == 'yes':
        conn = db_manager.get_connection(autocommit=True)
        if conn:
            try:
                cursor = conn.cursor()
                # Terminate existing connections first
                cursor.execute("""
                    SELECT pg_terminate_backend(pid) 
                    FROM pg_stat_activity 
                    WHERE datname = %s AND pid <> pg_backend_pid()
                """, (db_name,))
                
                # Drop database
                cursor.execute(sql.SQL("DROP DATABASE {}").format(
                    sql.Identifier(db_name)
                ))
                print(f"✅ Database '{db_name}' dropped successfully!")
            except psycopg2.Error as e:
                print(f"❌ Error dropping database: {e}")
            finally:
                cursor.close()
                conn.close()

def drop_all_tables(db_name, connection_params):
    """Drop all tables in the specified database (use with caution!)"""
    db_manager = PostgreSQLManager(**connection_params)
    conn = db_manager.get_connection(database=db_name)
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = cursor.fetchall()
            for table in tables:
                cursor.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
                    sql.Identifier(table[0])
                ))
            conn.commit()
            print(f"✅ All tables in database '{db_name}' dropped successfully!")
        except psycopg2.Error as e:
            print(f"❌ Error dropping tables: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

def drop_table(db_name, table_name, connection_params):
    """Drop a specific table in the specified database (use with caution!)"""
    db_manager = PostgreSQLManager(**connection_params)
    conn = db_manager.get_connection(database=db_name)

    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(
                sql.Identifier(table_name)
            ))
            conn.commit()
            print(f"✅ Table '{table_name}' dropped successfully!")
        except psycopg2.Error as e:
            print(f"❌ Error dropping table: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

def list_databases(connection_params):
    """List all databases"""
    db_manager = PostgreSQLManager(**connection_params)
    conn = db_manager.get_connection(autocommit=True)
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT datname 
                FROM pg_database 
                WHERE datistemplate = false 
                ORDER BY datname
            """)
            databases = cursor.fetchall()
            print("📁 Available databases:")
            for db in databases:
                print(f"  - {db[0]}")
        except psycopg2.Error as e:
            print(f"Error listing databases: {e}")
        finally:
            cursor.close()
            conn.close()

def list_elements_in_table(db_name, table_name, connection_params, limit=5):
    """List elements in a specified table"""
    db_manager = PostgreSQLManager(**connection_params)
    conn = db_manager.get_connection(database=db_name)
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(sql.SQL("SELECT * FROM {} LIMIT %s").format(
                sql.Identifier(table_name)
            ), (limit,))
            rows = cursor.fetchall()
            print(f"📋 Sample data from '{table_name}' table:")
            for row in rows:
                print(row)
        except psycopg2.Error as e:
            print(f"Error listing elements in table: {e}")
        finally:
            cursor.close()
            conn.close()

def query_companies(database: PostgreSQLManager, user_query: str):
    results = database.query_companies_with_embedding("augusta_labs_db", user_query, top_k=5)
    if results:
        for res in results:
            print(res['company_name'], res['distance_score'])

def query_incentives_by_name(database: PostgreSQLManager, user_query: str):
    results = database.query_incentives_by_name("augusta_labs_db", user_query)
    if results:
        for res in results:
            print(res['title'], res['similarity_score'])



if __name__ == "__main__":
    database = PostgreSQLManager(**DB_CONFIG)
    query_incentives_by_name(database, "Ensino")
