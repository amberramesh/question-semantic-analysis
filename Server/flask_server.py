import os
from flask import Flask, render_template, request
import tensorflow as tf
from flask_cors import CORS
import json
from use_similarity_measure import USESimilarityMeasure
from bert_classifier import BertClassifier
from glove_classifier import SentenceClassifier
from numpy import loadtxt

Q_VECTORS_PATH = os.path.join(os.getcwd(), 'data/vectors.out')
app = Flask(__name__)
CORS(app)

@app.route('/Dataset', methods=['POST'])
def switch_dataset():
    global table, classifier, model, embeddings_index, graph

    if request.form.get("dataset") != None:
        table = request.form["dataset"]
        classifier = SentenceClassifier()
        model, embeddings_index = classifier.setup_classifier(table, load_saved=1)
        graph = tf.get_default_graph()

    return ""

@app.route('/Semantics/Labels', methods=['GET'])
def get_labels():
    question = str(request.args['q'])
    with graph.as_default():
        possible_tags = classifier.tag_question(model, question)
    return json.dumps(possible_tags)

@app.route('/Semantics/Similarity', methods=['GET'])
def get_similar_questions():
	global usm, encoding_matrix, context_results

	user_question = request.args['q']
	top_k = int(request.args['fetchSize'])

	if user_question != '':
		usm.encode_question(user_question, encoding_matrix)
		results = usm.get_results(top_k)
		context_results['user_question'] = user_question
		context_results['topk_results'] = results[:10]
		return json.dumps(results)
	return json.dumps([])

@app.route('/Semantics/Duplicates', methods=['GET'])
def get_duplicates():
	global bc, bc_session, context_results

	user_question = request.args['q']

	if user_question != '' and context_results['user_question'] == user_question:
		topk_results = context_results['topk_results']
		bc.build_features(user_question, topk_results)
		duplicates = bc.predict(bc_session)
		return json.dumps(duplicates)
	return json.dumps([])

if __name__ == "__main__":
	table = 'compiled' # Load the 'compiled' dataset as the default dataset.
	classifier = SentenceClassifier()
	model, embeddings_index = classifier.setup_classifier(table, load_saved=1)
	graph = tf.get_default_graph()

	context_results = dict()
	context_results['user_question'] = ''
	context_results['topk_results'] = []

	print('Loading Universal Sentence Encoder')
	usm = USESimilarityMeasure()
	print('Finished loading Universal Sentence Encoder')
	print('\nLoading vectors.out...')
	encoding_matrix = loadtxt(
		Q_VECTORS_PATH,
		delimiter=',',
		encoding="utf-8")
	print('Finished loading vectors.out')

	print('Loading BERT Classifier')
	bc = BertClassifier()
	bc_session = bc.getSession()
	print('Finished loading BERT')

	app.run(port=5001)
