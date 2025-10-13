import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
import pandas as pd

class PostgreSQLManager:
    def __init__(self, host='localhost', user='postgres', password='123', port=5432):
        self.connection_params = {
            'host': host,
            'user': user,
            'password': password,
            'port': port
        }
    
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
    
    def database_exists(self, db_name):
        """Check if database already exists"""
        conn = self.get_connection(autocommit=True)
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                (db_name,)
            )
            exists = cursor.fetchone() is not None
            cursor.close()
            return exists
        except psycopg2.Error as e:
            print(f"Error checking database existence: {e}")
            return False
        finally:
            conn.close()
    
    def create_database(self, db_name):
        """Create a new database"""
        if self.database_exists(db_name):
            print(f"Database '{db_name}' already exists.")
            return True
        
        conn = self.get_connection(autocommit=True)
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            create_query = sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(db_name)
            )
            cursor.execute(create_query)
            print(f"✅ Database '{db_name}' created successfully!")
            return True
        except psycopg2.Error as e:
            print(f"❌ Error creating database: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def create_table(self, db_name, table_name, table_schema):
        """Create a table in the specified database"""
        conn = self.get_connection(database=db_name)
        if not conn:
            return False
        
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
    
    def verify_database(self, db_name):
        """Verify database creation and contents"""
        conn = self.get_connection(database=db_name)
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

    def insert_csv_incentives(self, db_name: str, file_path: str):
        """Insert multiple incentives from a CSV file into the incentives table"""
        incentives = read_csv_incentives(file_path)
        if not incentives:
            print("No incentives to insert.")
            return False
        
        conn = self.get_connection(database=db_name)
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            insert_query = """
                INSERT INTO incentives (title, description, ai_description, document_urls, date_publication, start_date, end_date, total_budget, source_link)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            for data in incentives:
                cursor.execute(insert_query, (
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

    def insert_csv_companies(self, db_name: str, file_path: str):
        """Insert multiple companies from a CSV file into the companies table"""
        companies = read_csv_incentives(file_path)
        if not companies:
            print("No companies to insert.")
            return False
        
        conn = self.get_connection(database=db_name)
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            insert_query = """
                INSERT INTO companies (company_name, cae_primary_label, trade_description_native, website)
                VALUES (%s, %s, %s, %s)
            """
            for data in companies:
                cursor.execute(insert_query, (
                    data.get("company_name"),
                    data.get("cae_primary_label"), 
                    data.get("trade_description_native") if not isinstance(data.get("trade_description_native"), float) else None,
                    data.get("website") if not isinstance(data.get("website"), float) else None
                ))
            conn.commit()
            print(f"✅ Inserted {len(companies)} companies from CSV successfully!")
            return True
        except psycopg2.Error as e:
            print(f"❌ Error inserting CSV data: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

def read_csv_incentives(file_path: str):
    """Read incentives from a CSV file and return as a list of dictionaries"""
    try:
        df = pd.read_csv(file_path)
        incentives = df.to_dict(orient='records')
        print(f"📥 Loaded {len(incentives)} incentives from CSV.")
        return incentives
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return []
    

def main():
    # Configuration
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'postgres',
        'password': '123',
        'port': 5432
    }
    
    DATABASE_NAME = "augusta_labs_db"
    
    # Table schema
    TABLE_SCHEMA = """
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

    TABLE_COMPANIES_SCHEMA = """
        CREATE TABLE IF NOT EXISTS companies (
            company_id SERIAL PRIMARY KEY,
            company_name TEXT NOT NULL,
            cae_primary_label TEXT,
            trade_description_native TEXT,
            website TEXT
        )
    """

    # Initialize database manager
    db_manager = PostgreSQLManager(**DB_CONFIG)
    
    print("🚀 Starting PostgreSQL Database Setup...")
    
    # Step 1: Create database
    if not db_manager.create_database(DATABASE_NAME):
        print("Failed to create database. Exiting.")
        sys.exit(1)

    # Step 2: Create incentives and companies table
    if not db_manager.create_table(DATABASE_NAME, 'incentives', TABLE_SCHEMA):
        print("Failed to create table. Exiting.")
        sys.exit(1)
    
    if not db_manager.create_table(DATABASE_NAME, 'companies', TABLE_COMPANIES_SCHEMA):
        print("Failed to create companies table. Exiting.")
        sys.exit(1)

    # Step 3: Insert sample data
    if not db_manager.insert_csv_incentives(DATABASE_NAME, 'csvs/incentives.csv'):
        print("Failed to insert sample data. Exiting.")
        sys.exit(1)
    
    if not db_manager.insert_csv_companies(DATABASE_NAME, 'csvs/companies.csv'):
        print("Failed to insert companies data. Exiting.")
        sys.exit(1)
    
    # Step 4: Verify everything worked
    print("\n🔍 Verifying database setup...")
    db_manager.verify_database(DATABASE_NAME)
    
    print(f"\n🎉 Database '{DATABASE_NAME}' setup completed successfully!")


# Additional utility functions
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



if __name__ == "__main__":
    DB_CONFIG = {'host': 'localhost', 'user': 'postgres', 'password': '123'}
    drop_database("augusta_labs_db", DB_CONFIG)

    main()
