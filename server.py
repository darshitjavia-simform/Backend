from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import logging

# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the frontend's URL (allow dynamic port change)
frontend_url = os.getenv('FRONTEND_URL')

# CORS configuration: Handle None values properly
if frontend_url:
    CORS(app, origins=frontend_url)
else:
    CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])
    logger.warning("FRONTEND_URL not set, using default origins for development")

# Database connection function using credentials from environment variables
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            autocommit=True
        )
        return connection
    except Error as err:
        logger.error(f"Database connection error: {err}")
        raise

# Test database connection on startup
def test_db_connection():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        connection.close()
        logger.info("Database connection successful")
        return True
    except Error as err:
        logger.error(f"Database connection failed: {err}")
        return False

# GET: Retrieve all todos
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
        return jsonify({"message": "Failed to fetch todos", "error": str(err)}), 500

# GET: Retrieve a specific todo
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
        return jsonify({"message": "Failed to fetch todo", "error": str(err)}), 500

# POST: Add a new todo
@app.route('/api/todos', methods=['POST'])
def add_todo():
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'task' not in data:
            return jsonify({"message": "Task is required"}), 400
        
        task = data['task'].strip()
        if not task:
            return jsonify({"message": "Task cannot be empty"}), 400
            
        done = data.get('done', False)
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Insert new todo
        cursor.execute("INSERT INTO todos (task, done) VALUES (%s, %s)", (task, done))
        todo_id = cursor.lastrowid
        
        # Fetch the inserted todo
        cursor.execute("SELECT * FROM todos WHERE id = %s", (todo_id,))
        new_todo = cursor.fetchone()
        
        cursor.close()
        connection.close()

        return jsonify(new_todo), 201
    
    except Error as err:
        logger.error(f"Error adding todo: {err}")
        return jsonify({"message": "Failed to add todo", "error": str(err)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in add_todo: {e}")
        return jsonify({"message": "An unexpected error occurred"}), 500

# PUT: Update a todo
@app.route('/api/todos/<int:id>', methods=['PUT'])
def update_todo(id):
    try:
        data = request.get_json()
        
        # Validate input
        if not data:
            return jsonify({"message": "Request body is required"}), 400
        
        task = data.get("task")
        done = data.get("done")
        
        if task is not None:
            task = task.strip()
            if not task:
                return jsonify({"message": "Task cannot be empty"}), 400
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Check if the todo exists
        cursor.execute("SELECT * FROM todos WHERE id = %s", (id,))
        existing_todo = cursor.fetchone()

        if not existing_todo:
            cursor.close()
            connection.close()
            return jsonify({"message": "Todo not found"}), 404

        # Update fields that were provided
        if task is not None and done is not None:
            cursor.execute("UPDATE todos SET task = %s, done = %s WHERE id = %s", (task, done, id))
        elif task is not None:
            cursor.execute("UPDATE todos SET task = %s WHERE id = %s", (task, id))
        elif done is not None:
            cursor.execute("UPDATE todos SET done = %s WHERE id = %s", (done, id))
        else:
            cursor.close()
            connection.close()
            return jsonify({"message": "No fields to update"}), 400

        # Fetch the updated todo
        cursor.execute("SELECT * FROM todos WHERE id = %s", (id,))
        updated_todo = cursor.fetchone()
        
        cursor.close()
        connection.close()

        return jsonify(updated_todo)
    
    except Error as err:
        logger.error(f"Error updating todo {id}: {err}")
        return jsonify({"message": "Failed to update todo", "error": str(err)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in update_todo: {e}")
        return jsonify({"message": "An unexpected error occurred"}), 500

# DELETE: Delete a todo
@app.route('/api/todos/<int:id>', methods=['DELETE'])
def delete_todo(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Check if the todo exists
        cursor.execute("SELECT * FROM todos WHERE id = %s", (id,))
        existing_todo = cursor.fetchone()

        if not existing_todo:
            cursor.close()
            connection.close()
            return jsonify({"message": "Todo not found"}), 404

        # Delete the todo
        cursor.execute("DELETE FROM todos WHERE id = %s", (id,))
        
        cursor.close()
        connection.close()

        return jsonify({"message": "Todo deleted successfully"}), 200
    
    except Error as err:
        logger.error(f"Error deleting todo {id}: {err}")
        return jsonify({"message": "Failed to delete todo", "error": str(err)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in delete_todo: {e}")
        return jsonify({"message": "An unexpected error occurred"}), 500

# Home route
@app.route('/')
def home():
    return jsonify({
        "message": "Todo API is running!",
        "endpoints": [
            "GET /api/todos - Get all todos",
            "GET /api/todos/<id> - Get specific todo",
            "POST /api/todos - Create new todo",
            "PUT /api/todos/<id> - Update todo",
            "DELETE /api/todos/<id> - Delete todo"
        ]
    })

# Health check endpoint
@app.route('/health')
def health_check():
    try:
        # Test database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        connection.close()
        
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "message": "API is running normally"
        }), 200
    except Error as err:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(err)
        }), 500

if __name__ == '__main__':
    # Test database connection before starting the app
    if test_db_connection():
        logger.info("Starting Flask application...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        logger.error("Failed to connect to database. Please check your database credentials.")
        print("\nPlease verify your .env file contains correct database credentials:")
        print("DB_HOST=localhost")
        print("DB_USER=your_mysql_username") 
        print("DB_PASSWORD=your_mysql_password")
        print("DB_NAME=your_database_name")