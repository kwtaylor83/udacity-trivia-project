import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgresql://{}:{}@{}/{}".format(
            'postgres', 'postgres', 'localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for
    successful operation and for expected errors.
    """

    def test_get_categories(self):
        ''' Test resource: return all available categories. '''
        res = self.client().get('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['categories']))

    def test_get_paginated_questions(self):
        ''' Test resource: return a list of paginated questions,
         number of total questions, current category, categories.  '''
        res = self.client().get('/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertTrue(data['total_questions'] >= 1)
        self.assertTrue(len(data['categories']) >= 1)

    def test_send_404_on_request_for_invalid_page(self):
        res = self.client().get('/questions?page=1000')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_send_404_on_request_to_delete_invalid_page(self):
        res = self.client().delete('/questions/9999')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    # def test_delete_question(self):
    #     res = self.client().delete('/questions/9')
    #     data = json.loads(res.data)

    #     self.assertEqual(data['success'], True)
    #     self.assertEqual(data['deleted_id'], 9)

    def test_post_new_question(self):
        test_post_json = {
            'question': 'What is the question?',
            'answer': 'This is',
            'category': 3,
            'difficulty': 1
        }
        res = self.client().post('/questions', json=test_post_json)
        data = json.loads(res.data)
        question = Question.query.filter(
            Question.question == 'What is the question?').first()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertIsNotNone(question)
        self.assertIsNotNone(data['new_question_id'], True)
        self.assertEqual(question.answer, "This is")
        self.assertEqual(question.category, 3)
        self.assertEqual(question.difficulty, 1)

    def test_bad_request_for_question(self):
        test_post_json = {
            'question': None,
            'answer': 'Answer',
            'category': 3,
            'difficulty': 1
        }
        res = self.client().post('/questions', json=test_post_json)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 400)
        self.assertEqual(data['message'], "bad request")

        test_post_json = {
            'question': 'Question',
            'answer': '',
            'category': 3,
            'difficulty': 1
        }
        res = self.client().post('/questions', json=test_post_json)
        data = json.loads(res.data)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 400)
        self.assertEqual(data['message'], "bad request")

    def test_search_questions(self):
        searchTerm = 'world'
        test_post_json = {
            'searchTerm': searchTerm
        }
        res = self.client().post('/questions/search', json=test_post_json)
        data = json.loads(res.data)

        matching_questions = Question.query.filter(
            Question.question.ilike('%' + searchTerm + '%'))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(matching_questions.count(), 2)

    def test_get_questions_by_categories(self):
        res = self.client().get('/categories/3/questions')
        data = json.loads(res.data)

        questions_in_category = Question.query.filter(Question.category == 3)
        num_questions_in_category = questions_in_category.count()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['total_questions'], num_questions_in_category)
        self.assertEqual(data['current_category'], 3)

    def test_play_quiz_by_category(self):
        test_quiz_json = {
            "previous_questions": [],
            "quiz_category": {"type": "Science", "id": 1}
        }
        res = self.client().post('/quizzes', json=test_quiz_json)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

    def test_play_quiz_no_category(self):
        test_quiz_json = {
            "previous_questions": [],
            "quiz_category": {"type": "click", "id": 0}
        }
        res = self.client().post('/quizzes', json=test_quiz_json)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)

    def test_play_quiz_invalid_category(self):
        test_quiz_json = {
            "previous_questions": [],
            "quiz_category": {"type": "Science", "id": 14}
        }
        res = self.client().post('/quizzes', json=test_quiz_json)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
