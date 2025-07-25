from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import logging
import boto3
import json

# Load environment variables first
load_dotenv()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
REGION = os.getenv("AWS_REGION", "us-east-2")
SECRET_ID = os.getenv("DB_SECRET_ID", "dev-db-credentials-1")
FRONTEND_URL = os.getenv("FRONTEND_URL")
DB_HOST = os.getenv("DB_HOST")

# AWS SecretsManager client
def get_db_secrets():
    try:
        client = boto3.client('secretsmanager', region_name=REGION)
        response = client.get_secret_value(SecretId=SECRET_ID)
        secrets = json.loads(response['SecretString'])
        return secrets
    except Exception as e:
        logger.error(f"Failed to retrieve DB secrets: {e}")
        raise

# Get DB credentials
secrets = get_db_secrets()
DB_USER = secrets['db_user']
DB_PASSWORD = secrets['db_password']
DB_NAME = secrets['db_name']

app = Flask(__name__)

# Setup CORS
if FRONTEND_URL:
    CORS(app, origins=[FRONTEND_URL])
else:
    CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])
    logger.warning("FRONTEND_URL not set, using default localhost origins")


# Reusable DB connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            autocommit=True,
            connection_timeout=10
        )
        return connection
    except Error as err:
        logger.error(f"Database connection error: {err}")
        raise


# Check DB on startup
def test_db_connection():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        connection.close()
        logger.info("✅ Database connection successful.")
        return True
    except Error as err:
        logger.error(f"❌ Database test connection failed: {err}")
        return False


@app.route('/api/todos', methods=['GET'])
def get_todos():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM todos ORDER BY id DESC")
        todos = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(todos)
    except Error as err:
        logger.error(f"Error fetching todos: {err}")
        return jsonify({"message": "Failed to fetch todos"}), 500


@app.route('/api/todos/<int:id>', methods=['GET'])
def get_todo(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM todos WHERE id = %s", (id,))
        todo = cursor.fetchone()
        cursor.close()
        connection.close()

        if not todo:
            return jsonify({"message": "Todo not found"}), 404

        return jsonify(todo)
    except Error as err:
        logger.error(f"Error fetching todo {id}: {err}")
        return jsonify({"message": "Failed to fetch todo"}), 500


@app.route('/api/todos', methods=['POST'])
def add_todo():
    try:
        data = request.get_json()
        if not data or 'task' not in data:
            return jsonify({"message": "Task is required"}), 400

        task = data['task'].strip()
        if not task:
            return jsonify({"message": "Task cannot be empty"}), 400

        done = data.get('done', False)

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("INSERT INTO todos (task, done) VALUES (%s, %s)", (task, done))
        todo_id = cursor.lastrowid
        cursor.execute("SELECT * FROM todos WHERE id = %s", (todo_id,))
        new_todo = cursor.fetchone()
        cursor.close()
        connection.close()

        return jsonify(new_todo), 201
    except Exception as e:
        logger.exception("Unexpected error adding todo")
        return jsonify({"message": "Failed to add todo"}), 500


@app.route('/api/todos/<int:id>', methods=['PUT'])
def update_todo(id):
    try:
        data = request.get_json()
        task = data.get('task')
        done = data.get('done')

        if task is not None:
            task = task.strip()
            if not task:
                return jsonify({"message": "Task cannot be empty"}), 400

        if task is None and done is None:
            return jsonify({"message": "No fields to update"}), 400

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM todos WHERE id = %s", (id,))
        existing_todo = cursor.fetchone()

        if not existing_todo:
            cursor.close()
            connection.close()
            return jsonify({"message": "Todo not found"}), 404

        # Update logic
        if task is not None and done is not None:
            cursor.execute("UPDATE todos SET task = %s, done = %s WHERE id = %s", (task, done, id))
        elif task is not None:
            cursor.execute("UPDATE todos SET task = %s WHERE id = %s", (task, id))
        elif done is not None:
            cursor.execute("UPDATE todos SET done = %s WHERE id = %s", (done, id))

        cursor.execute("SELECT * FROM todos WHERE id = %s", (id,))
        updated_todo = cursor.fetchone()
        cursor.close()
        connection.close()

        return jsonify(updated_todo)

    except Exception as e:
        logger.exception(f"Error updating todo {id}")
        return jsonify({"message": "Failed to update todo"}), 500


@app.route('/api/todos/<int:id>', methods=['DELETE'])
def delete_todo(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM todos WHERE id = %s", (id,))
        todo = cursor.fetchone()

        if not todo:
            cursor.close()
            connection.close()
            return jsonify({"message": "Todo not found"}), 404

        cursor.execute("DELETE FROM todos WHERE id = %s", (id,))
        cursor.close()
        connection.close()

        return jsonify({"message": "Todo deleted successfully"})

    except Exception as e:
        logger.exception(f"Error deleting todo {id}")
        return jsonify({"message": "Failed to delete todo"}), 500


@app.route('/')
def home():
    return jsonify({
        "message": "Todo API is running",
        "endpoints": [
            "GET /api/todos",
            "GET /api/todos/<id>",
            "POST /api/todos",
            "PUT /api/todos/<id>",
            "DELETE /api/todos/<id>",
            "GET /health"
        ]
    })


@app.route('/health')
def health_check():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        connection.close()
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


if __name__ == '__main__':
    if test_db_connection():
        logger.info("🚀 Starting Flask server...")
        app.run(debug=False, host='0.0.0.0', port=5000)
    else:
        logger.error("❌ Database connection failed. Check .env and Secrets Manager.")
