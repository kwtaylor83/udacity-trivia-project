import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category
from models import db

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample
     route after completing the TODOs
    '''
    cors = CORS(app, resources={r"/*": {"origins": "*"}})

    '''
    @TODO: Use the after_request decorator to set Access-Control-Allow
    '''
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, DELETE, POST')
        return response

    def paginate_questions(request, selection):
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE

        questions = [question.format() for question in selection]
        current_questions = questions[start:end]

        return current_questions

    '''
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    '''
    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.all()
        categories_dict = {}
        for category in categories:
            categories_dict[category.id] = category.type

        if len(categories_dict) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'categories': categories_dict
        })

    '''
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of
     the screen for three pages.

    Clicking on the page numbers should update the questions.
    '''

    @app.route('/questions', methods=['GET'])
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        total_questions = len(Question.query.all())

        current_questions = paginate_questions(request, selection)

        categories = Category.query.all()
        categories_dict = {}
        for category in categories:
            categories_dict[category.id] = category.type

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': total_questions,
            'categories': categories_dict,
            'current_category': None
        })

    '''
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question,
    the question will be removed.

    This removal will persist in the database and when you refresh the page.
    '''
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        question = Question.query.get(question_id)
        if question is None:
            abort(404)

        question = Question.query.get(question_id).delete()

        return jsonify({
            'success': True,
            'deleted_id': question_id
        })

    '''
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear
    at the end of the last page     of the questions list in the "List" tab.
    '''
    @app.route('/questions', methods=['POST'])
    def add_question():
        req_data = request.get_json()

        question = req_data.get('question', None)
        answer = req_data.get('answer', None)
        difficulty = int(req_data.get('difficulty', None))
        category = int(req_data.get('category', None))

        if not question:
            abort(400)
        if not answer:
            abort(400)
        if not 1 <= difficulty <= 5:
            abort(400)
        test_category = Category.query.get(category)
        if test_category is None:
            abort(400)

        try:
            new_question = Question(question=question,
                                    answer=answer,
                                    difficulty=difficulty,
                                    category=category)
            db.session.add(new_question)
            db.session.commit()
            new_question = Question.query.filter(
                Question.question == question).first()
            new_question_id = new_question.id
        except: # noqa
            abort(422)

        return jsonify({
            'success': True,
            'new_question_id': new_question_id
        })

    '''
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    '''

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        req_data = request.get_json()

        searchTerm = req_data.get('searchTerm', None)

        if searchTerm is None:
            abort(422)

        selection = Question.query.filter(
            Question.question.ilike('%' + searchTerm + '%'))
        total_questions = len(Question.query.all())

        current_questions = paginate_questions(request, selection)

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': total_questions
        })

    '''
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
        '''

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
        selection = Question.query.filter(Question.category == category_id)
        total_questions = selection.count()

        if total_questions == 0:
            abort(404)

        current_questions = paginate_questions(request, selection)

        categories = Category.query.all()
        categories_dict = {}
        for category in categories:
            categories_dict[category.id] = category.type

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': total_questions,
            'categories': categories_dict,
            'current_category': category_id
        })

    '''
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    '''

    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        req_data = request.get_json()
        quiz_category = req_data.get('quiz_category', None)
        previous_questions = req_data.get('previous_questions', None)

        if not quiz_category:
            abort(400)

        if int(quiz_category['id']) >= 1:
            check_category = Category.query.filter(
                Category.id == quiz_category['id']).first()
            if not check_category:
                abort(400)

        if int(quiz_category['id']) >= 1:
            question = Question.query.filter(
                Question.category == quiz_category['id'],
                ~Question.id.in_(previous_questions)).first()
        else:
            question = Question.query.filter(
                ~Question.id.in_(previous_questions)).first()

        if not question:
            return jsonify({
                "question": False,
                "success": True
            })
        else:
            return jsonify({
                "question": {
                    "answer": question.answer,
                    "id": question.id,
                    "question": question.question
                },
                "success": True
            })

    '''
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    '''
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def not_processable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "server error"
        }), 500

    return app
