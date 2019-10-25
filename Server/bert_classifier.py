import os
import tensorflow as tf
import numpy as np
from bert.tokenization import FullTokenizer
import bert.modeling as modeling
from bert.run_classifier import InputExample, input_fn_builder, convert_examples_to_features

tf.logging.set_verbosity(tf.logging.INFO)	

BERT_MODEL = 'uncased_L-12_H-768_A-12'
FINE_TUNED_MODEL = 'qqp_outputs'
BERT_PRETRAINED_DIR = os.path.join(os.getcwd(), 'bert', BERT_MODEL)
FINE_TUNED_DIR = os.path.join(os.getcwd(), 'bert', FINE_TUNED_MODEL)

TRAIN_BATCH_SIZE = 32
EVAL_BATCH_SIZE = 8
PREDICT_BATCH_SIZE = 8
MAX_SEQ_LENGTH = 128
USE_TPU = False

SAVE_CHECKPOINTS_STEPS = 1000
ITERATIONS_PER_LOOP = 1000
VOCAB_FILE = os.path.join(BERT_PRETRAINED_DIR, 'vocab.txt')
CONFIG_FILE = os.path.join(BERT_PRETRAINED_DIR, 'bert_config.json')
INIT_CHECKPOINT = os.path.join(BERT_PRETRAINED_DIR, 'bert_model.ckpt')
QQP_CHECKPOINT = os.path.join(FINE_TUNED_DIR, 'model.ckpt-22740')
SAVED_MODEL = os.path.join(FINE_TUNED_DIR, 'saved_model')
DO_LOWER_CASE = BERT_MODEL.startswith('uncased')

class BertClassifier:
	"""Retrieves duplicates for a given question among a set of questions"""
	def __init__(self):
		self.labels = [0, 1]
		self.features = None

		self.run_config = tf.contrib.tpu.RunConfig(
			model_dir=FINE_TUNED_DIR)
			
		self.model_fn = self.model_fn_builder(
			bert_config=modeling.BertConfig.from_json_file(CONFIG_FILE),
			init_checkpoint=INIT_CHECKPOINT,
			num_labels=len(self.labels),
			use_tpu=USE_TPU,
			use_one_hot_embeddings=True)

		self.estimator = tf.contrib.tpu.TPUEstimator(
			use_tpu=USE_TPU,
			model_fn=self.model_fn,
			model_dir=FINE_TUNED_DIR,
			config=self.run_config,
			train_batch_size=TRAIN_BATCH_SIZE,
			eval_batch_size=EVAL_BATCH_SIZE,
			predict_batch_size=PREDICT_BATCH_SIZE
		)

	def build_features(self, user_question, topk_results):

		self.user_question = user_question
		self.topk_results = topk_results
		q_pairs = []
		for i, similar_q in enumerate(topk_results):
			input_example = InputExample(guid=i, text_a=user_question, text_b=similar_q, label=0)
			q_pairs.append(input_example)
			
		tokenizer = FullTokenizer(
			vocab_file=VOCAB_FILE, do_lower_case=DO_LOWER_CASE)
			
		self.features = convert_examples_to_features(q_pairs, self.labels, MAX_SEQ_LENGTH, tokenizer)

	def getSession(self):
		sess = tf.InteractiveSession()

		def serving_input_fn():
			label_ids = tf.placeholder(tf.int32, [None], name='label_ids')
			input_ids = tf.placeholder(tf.int32, [None, MAX_SEQ_LENGTH], name='input_ids')
			input_mask = tf.placeholder(tf.int32, [None, MAX_SEQ_LENGTH], name='input_mask')
			segment_ids = tf.placeholder(tf.int32, [None, MAX_SEQ_LENGTH], name='segment_ids')
			with tf.variable_scope("qqp"):
				input_fn = tf.estimator.export.build_raw_serving_input_receiver_fn({
					'label_ids': label_ids,
					'input_ids': input_ids,
					'input_mask': input_mask,
					'segment_ids': segment_ids,
				})()
				return input_fn
		
		# self.estimator._export_to_tpu = False
		# self.estimator.export_savedmodel(FINE_TUNED_DIR, serving_input_fn)

		tf.saved_model.loader.load(sess, [tf.saved_model.tag_constants.SERVING], SAVED_MODEL)
		graph = tf.get_default_graph()
		self.tensor_input_ids = graph.get_tensor_by_name('qqp/input_ids:0')
		self.tensor_input_mask = graph.get_tensor_by_name('qqp/input_mask:0')
		self.tensor_label_ids = graph.get_tensor_by_name('qqp/label_ids:0')
		self.tensor_segment_ids = graph.get_tensor_by_name('qqp/segment_ids:0')
		self.tensor_outputs = graph.get_tensor_by_name('loss/Softmax:0')
		
		return sess
	
	def predict(self, sess):
		results = []
		for feature in self.features:
			result = sess.run(self.tensor_outputs, feed_dict={
				self.tensor_input_ids: np.reshape(feature.input_ids, (1, MAX_SEQ_LENGTH)),
				self.tensor_input_mask: np.reshape(feature.input_mask, (1, MAX_SEQ_LENGTH)),
				self.tensor_label_ids: np.array([feature.label_id]),
				self.tensor_segment_ids: np.reshape(feature.segment_ids, (1, MAX_SEQ_LENGTH))
			})
			results.append(result)
			
		duplicates = []

		for q_i in range(len(self.topk_results)):
			if np.argmax(results[q_i]) == 1:
				duplicates.append(self.topk_results[q_i])
		
		return duplicates
	
	def create_model(self, bert_config, input_ids, input_mask, segment_ids,
							labels, num_labels, use_one_hot_embeddings):
		"""Creates a classification model."""
		model = modeling.BertModel(
			config=bert_config,
			is_training=False,
			input_ids=input_ids,
			input_mask=input_mask,
			token_type_ids=segment_ids,
			use_one_hot_embeddings=use_one_hot_embeddings)

		output_layer = model.get_pooled_output()

		hidden_size = output_layer.shape[-1].value

		output_weights = tf.get_variable(
				"output_weights", [num_labels, hidden_size],
				initializer=tf.truncated_normal_initializer(stddev=0.02))

		output_bias = tf.get_variable(
				"output_bias", [num_labels], initializer=tf.zeros_initializer())

		with tf.variable_scope("loss"):

			logits = tf.matmul(output_layer, output_weights, transpose_b=True)
			logits = tf.nn.bias_add(logits, output_bias)
			probabilities = tf.nn.softmax(logits, axis=-1)
			log_probs = tf.nn.log_softmax(logits, axis=-1)

			one_hot_labels = tf.one_hot(labels, depth=num_labels, dtype=tf.float32)

			per_example_loss = -tf.reduce_sum(one_hot_labels * log_probs, axis=-1)
			loss = tf.reduce_mean(per_example_loss)

			return (loss, per_example_loss, logits, probabilities)
		
	def model_fn_builder(self, bert_config, init_checkpoint, num_labels, use_tpu,
							use_one_hot_embeddings):
		"""Returns `model_fn` closure for TPUEstimator."""

		def model_fn(features, labels, mode, params):
			"""The `model_fn` for TPUEstimator."""

			input_ids = features["input_ids"]
			input_mask = features["input_mask"]
			segment_ids = features["segment_ids"]
			label_ids = features["label_ids"]
					
			(total_loss, per_example_loss, logits, probabilities) = self.create_model(
			bert_config, input_ids, input_mask, segment_ids, label_ids,
			num_labels, use_one_hot_embeddings)

			tvars = tf.trainable_variables()
			initialized_variable_names = {}
			scaffold_fn = None
			if init_checkpoint:
				(assignment_map, initialized_variable_names
				) = modeling.get_assignment_map_from_checkpoint(tvars, init_checkpoint)
				tf.train.init_from_checkpoint(init_checkpoint, assignment_map)

			tf.logging.info("**** Trainable Variables ****")
			for var in tvars:
				init_string = ""
				if var.name in initialized_variable_names:
					init_string = ", *INIT_FROM_CKPT*"
				tf.logging.info("	name = %s, shape = %s%s", var.name, var.shape,
								init_string)
			
			output_spec = None

			if mode != tf.estimator.ModeKeys.PREDICT:
				raise ValueError("Only PREDICT modes are supported: %s" % (mode))
			
			output_spec = tf.contrib.tpu.TPUEstimatorSpec(
				mode=mode,
				predictions={"probabilities": probabilities},
				scaffold_fn=scaffold_fn)
			return output_spec

		return model_fn
