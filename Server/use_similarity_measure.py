import os
import tensorflow as tf
import tensorflow_hub as hub
import scipy.spatial.distance as sp
import numpy as np

USE_MODEL_DIR = os.path.join(os.getcwd(), 'universal_sentence_encoder_large_3')
Q_PLAIN_TEXT_PATH = os.path.join(os.getcwd(), 'data/questions.txt')

class USESimilarityMeasure:
    """Retrieves top-k contextually similar questions"""

    def __init__(self):

        def embed_useT(module):
            with tf.Graph().as_default():
                sentences = tf.placeholder(tf.string)
                embed = hub.Module(module)
                embeddings = embed(sentences)
                session = tf.train.MonitoredSession()
            return lambda x: session.run(embeddings, {sentences: x})
        self.embed_fn = embed_useT(USE_MODEL_DIR)

        with open(Q_PLAIN_TEXT_PATH, 'r', encoding='utf-8') as q_data:
            self.questions_db = [line.rstrip() for line in q_data]
        
        self.encoding_matrix = None
        self.question_embedding = None
    
    def __enter__(self):
        return self
    
    def encode_question(self, user_question, encoding_matrix):
        self.question_embedding = self.embed_fn([user_question])
        self.encoding_matrix = encoding_matrix
    
    def get_results(self, top_k):

        cosine_score = sp.cdist(self.question_embedding, self.encoding_matrix, 'cosine')[0]
        cosine_idx = np.argsort(cosine_score)[:top_k]
        print("Using cosine similarity:")
        topk_results = []
        for idx in cosine_idx:
            topk_results.append(self.questions_db[idx])
        return topk_results
    
    def __exit__(self, exc_type, exc_value, traceback):
        tf.reset_default_graph()
