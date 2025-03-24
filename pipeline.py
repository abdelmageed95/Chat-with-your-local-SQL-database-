import ollama
import re
from langchain_community.utilities import SQLDatabase
from schema_generator import get_full_schema

class Pipeline:
    """A Retrieval-Augmented Generation pipeline for SQL queries with Ollama LLM."""

    def __init__(self, database_url: str, model_name: str = "llama3.2"):
        """
        Initialize the RAG pipeline with database and LLM configurations.

        Args:
            database_url (str): PostgreSQL connection URL.
            model_name (str, optional): Ollama model name. Defaults to "llama3.2".
        """
        self.db = SQLDatabase.from_uri(database_url, sample_rows_in_table_info=3)
        self.model_name = model_name
        self.schema = get_full_schema(database_url)

    def generate_sql_query(self, question: str, limit: int = 5) -> str:
        """
        Generate a SQL query from a natural language question.

        Args:
            question (str): User's question.
            limit (int, optional): Number of rows to limit results to. Defaults to 5.
                                   It will add LIMIT {limit} to the SQL query.

        Returns:
            str: Generated SQL query.
        """
        sql_prompt = [
            {
                "role": "user",
                "content": (
                    f"Based on the database schema below, convert the user's question into a SQL query:\n"
                    f"Schema:\n\n{self.schema}\n"
                    f"Question: {question}\n"
                    f"Limit the results to {limit} rows.\n"
                    "Return only the SQL query code, nothing else.\n"
                    "Don't include anything that is not a postgres syntax."
                )
            }
        ]
        response = ollama.chat(model=self.model_name, messages=sql_prompt)
        return response["message"]["content"].strip()

    def validate_sql_query(self, sql_query: str) -> str:
        """
        Validate and refine the SQL query using the LLM.

        Args:
            sql_query (str): Initial SQL query to validate.

        Returns:
            str: Validated SQL query.
        """
        check_prompt = [
            {
                "role": "user",
                "content": (
                    f"Check the syntax and logic of the SQL query below:\n{sql_query}\n\n"
                    f"Based on this schema:\n\n{self.schema}\n\n"
                    "Return only the SQL query code, nothing else."
                )
            }
        ]
        response = ollama.chat(model=self.model_name, messages=check_prompt)
        validated_query = response["message"]["content"].strip()
        
        # Clean the query to ensure it ends with a semicolon and captures SELECT statements
        cleaned_query = re.search(r"SELECT.*?;", validated_query, re.DOTALL)
        return cleaned_query.group(0) if cleaned_query else validated_query

    def execute_query(self, sql_query: str) -> str:
        """
        Execute the SQL query against the database.

        Args:
            sql_query (str): SQL query to execute.

        Returns:
            str: Query results as a string (table like output).
        """
        return self.db.run(sql_query)

    def generate_response(self, query_result: str, question: str) -> str:
        """
        Generate a human-readable response from query results.

        Args:
            query_result (str): Results from the SQL query.
            question (str): Original user question.

        Returns:
            str: Markdown-formatted response.
        """
        response_prompt = [
            {
                "role": "user",
                "content": (
                    f"Based on the following information: {query_result}, "
                    f"answer the user's question in a clear, natural language, concise,and well-structured markdown format.\n"
                    f"Question: {question}\n"
                    "Don't include any SQL queries or any other technical details.\n"
                    "do nt make a large font size i the markdown."
                   
                )
            }
        ]
        response = ollama.chat(model=self.model_name, messages=response_prompt)
        return response["message"]["content"]

    def run(self, question: str, max_retries: int = 10) -> str:
        """
        Run the full RAG pipeline for a given question with retry logic.

        Args:
            question (str): User's question.
            max_retries (int, optional): Maximum number of retries on failure. Defaults to 3.

        Returns:
            str: Final response or error message after retries.
        """
        attempt = 1
        last_error = None

        while attempt <= max_retries:
            try:
                sql_query = self.generate_sql_query(question)
                validated_query = self.validate_sql_query(sql_query)
                query_result = self.execute_query(validated_query)
                response = self.generate_response(query_result, question)
                return response
            except Exception as e:
                last_error = str(e)
                attempt += 1

        return f"Error: {last_error}"