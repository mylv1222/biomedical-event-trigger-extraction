from keras.engine import Model

from Models.BaseModel import BaseModel
from lib.Evaluator import Evaluator
import keras
from keras.layers import Bidirectional, GRU, TimeDistributed, Dense, Dropout
from Models.util import *


class SelfAttentionModel(BaseModel):
    """
    code for bibm 2017 paper.
    """
    def __init__(self, max_len=100, class_num=73):

        super(SelfAttentionModel, self).__init__()

        self.max_len = max_len
        self.class_num = class_num

    def build_model(self):

        x = TimeDistributed(Dense(200, activation='tanh'))(self.sen_embedding)
        self_attention_embedding, self_attention = soft_attention_alignment(x, x)

        inputs = keras.layers.concatenate([self.sen_embedding, self.entity_embedding])

        encoded_sentence_embedding = Bidirectional(GRU(200,
                                                       activation="relu",
                                                       return_sequences=True,
                                                       dropout=0.3))(inputs)
        encoded_sentence_embedding = Dropout(rate=0.5)(encoded_sentence_embedding)

        x = Concatenate()([encoded_sentence_embedding, self_attention_embedding])

        predictions = TimeDistributed(Dense(self.class_num, activation='softmax'))(x)

        return [predictions, self_attention]

    def train_model(self, max_epoch=30):

        e1 = Evaluator(true_labels=self.test_labels, sentences=self.test_word_inputs, index_ids=self.index_ids)
        # e2 = Evaluator(true_labels=self.dev_labels, sentences=self.dev_word_inputs, index_ids=self.index_ids)

        for i in range(max_epoch):
            print("====== epoch " + str(i + 1) + " ======")
            self.model.fit({'sentence_input': self.train_word_inputs,
                            'entity_type_input': self.train_entity_inputs},
                           [self.train_labels, self.train_attention_labels],
                           epochs=1,
                           batch_size=32,
                           # validation_data=([self.dev_word_inputs,
                           #                   self.dev_entity_inputs], self.dev_labels),
                           verbose=2)

            # print("# -- develop set --- #")
            # results = self.model.predict({'sentence_input': self.dev_word_inputs,
            #                               'entity_type_input': self.dev_entity_inputs},
            #                              batch_size=64,
            #                              verbose=0)
            # results = e2.get_true_label(label=results)
            # results = e2.process_bie(sen_label=results)
            # e2.get_true_prf(results, epoch=i + 1)

            print("# -- test set --- #")
            results = self.model.predict({'sentence_input': self.test_word_inputs,
                                          'entity_type_input': self.test_entity_inputs},
                                         batch_size=64,
                                         verbose=0)[0]

            results = e1.get_true_label(label=results)
            results = e1.process_bie(sen_label=results)
            e1.get_true_prf(results, epoch=i + 1)

    def compile_model(self):
        self.sen_input, self.entity_type_input = self.make_input()
        self.sen_embedding, self.entity_embedding = self.embedded()

        self.output = self.build_model()

        inputs = [self.sen_input, self.entity_type_input]

        self.model = Model(inputs=inputs, outputs=self.output)
        self.model.compile(optimizer='adam',
                           loss=['categorical_crossentropy', 'mse'],
                           metrics=['acc'],
                           loss_weights=[1., 1.])


if __name__ == '__main__':

    s = SelfAttentionModel(max_len=125, class_num=73)
    for i in range(5):
        s.compile_model()
        s.train_model()
