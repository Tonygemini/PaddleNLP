# Copyright (c) 2022 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys

import paddle
import paddle.nn as nn

from paddlenlp.transformers.model_utils import PretrainedModel, register_base_model

sys.path.append("../..")
from task.transformer import TransformerEncoder, TransformerEncoderLayer  # noqa: E402

sys.path.remove("../..")

__all__ = [
    "RobertaModel",
    "RobertaPretrainedModel",
    "RobertaForSequenceClassification",
    "RobertaForTokenClassification",
    "RobertaForQuestionAnswering",
]


class RobertaEmbeddings(nn.Layer):
    r"""
    Include embeddings from word, position and token_type embeddings.
    """

    def __init__(
        self,
        vocab_size,
        hidden_size=768,
        hidden_dropout_prob=0.1,
        max_position_embeddings=512,
        type_vocab_size=16,
        pad_token_id=0,
    ):
        super(RobertaEmbeddings, self).__init__()
        self.word_embeddings = nn.Embedding(vocab_size, hidden_size, padding_idx=pad_token_id)
        self.position_embeddings = nn.Embedding(max_position_embeddings, hidden_size)
        self.token_type_embeddings = nn.Embedding(type_vocab_size, hidden_size)
        self.layer_norm = nn.LayerNorm(hidden_size)
        self.dropout = nn.Dropout(hidden_dropout_prob)

    def forward(self, input_ids, token_type_ids=None, position_ids=None):
        if position_ids is None:
            # maybe need use shape op to unify static graph and dynamic graph
            ones = paddle.ones_like(input_ids, dtype="int64")
            seq_length = paddle.cumsum(ones, axis=-1)
            position_ids = seq_length - ones
            position_ids.stop_gradient = True
        if token_type_ids is None:
            token_type_ids = paddle.zeros_like(input_ids, dtype="int64")

        input_embedings = self.word_embeddings(input_ids)
        position_embeddings = self.position_embeddings(position_ids)
        token_type_embeddings = self.token_type_embeddings(token_type_ids)

        embeddings = input_embedings + position_embeddings + token_type_embeddings
        embeddings = self.layer_norm(embeddings)
        embeddings = self.dropout(embeddings)
        return embeddings


class RobertaPooler(nn.Layer):
    def __init__(self, hidden_size):
        super(RobertaPooler, self).__init__()
        self.dense = nn.Linear(hidden_size, hidden_size)
        self.activation = nn.Tanh()

    def forward(self, hidden_states):
        # We "pool" the model by simply taking the hidden state corresponding
        # to the first token.
        first_token_tensor = hidden_states[:, 0]
        pooled_output = self.dense(first_token_tensor)
        pooled_output = self.activation(pooled_output)
        return pooled_output


class RobertaPretrainedModel(PretrainedModel):
    r"""
    An abstract class for pretrained RoBerta models. It provides RoBerta related
    `model_config_file`, `pretrained_resource_files_map`, `resource_files_names`,
    `pretrained_init_configuration`, `base_model_prefix` for downloading and
    loading pretrained models.
    Refer to :class:`~paddlenlp.transformers.model_utils.PretrainedModel` for more details.

    """

    model_config_file = "model_config.json"
    pretrained_init_configuration = {
        "roberta-wwm-ext": {
            "attention_probs_dropout_prob": 0.1,
            "hidden_act": "gelu",
            "hidden_dropout_prob": 0.1,
            "hidden_size": 768,
            "initializer_range": 0.02,
            "intermediate_size": 3072,
            "max_position_embeddings": 512,
            "num_attention_heads": 12,
            "num_hidden_layers": 12,
            "type_vocab_size": 2,
            "vocab_size": 21128,
            "pad_token_id": 0,
        },
        "roberta-wwm-ext-large": {
            "attention_probs_dropout_prob": 0.1,
            "hidden_act": "gelu",
            "hidden_dropout_prob": 0.1,
            "hidden_size": 1024,
            "initializer_range": 0.02,
            "intermediate_size": 4096,
            "max_position_embeddings": 512,
            "num_attention_heads": 16,
            "num_hidden_layers": 24,
            "type_vocab_size": 2,
            "vocab_size": 21128,
            "pad_token_id": 0,
        },
        "rbt3": {
            "attention_probs_dropout_prob": 0.1,
            "hidden_act": "gelu",
            "hidden_dropout_prob": 0.1,
            "hidden_size": 768,
            "initializer_range": 0.02,
            "intermediate_size": 3072,
            "max_position_embeddings": 512,
            "num_attention_heads": 12,
            "num_hidden_layers": 3,
            "type_vocab_size": 2,
            "vocab_size": 21128,
            "pad_token_id": 0,
        },
        "rbtl3": {
            "attention_probs_dropout_prob": 0.1,
            "hidden_act": "gelu",
            "hidden_dropout_prob": 0.1,
            "hidden_size": 1024,
            "initializer_range": 0.02,
            "intermediate_size": 4096,
            "max_position_embeddings": 512,
            "num_attention_heads": 16,
            "num_hidden_layers": 3,
            "type_vocab_size": 2,
            "vocab_size": 21128,
            "pad_token_id": 0,
        },
    }
    resource_files_names = {"model_state": "model_state.pdparams"}
    pretrained_resource_files_map = {
        "model_state": {
            "roberta-wwm-ext": "https://paddlenlp.bj.bcebos.com/models/transformers/roberta_base/roberta_chn_base.pdparams",
            "roberta-wwm-ext-large": "https://paddlenlp.bj.bcebos.com/models/transformers/roberta_large/roberta_chn_large.pdparams",
            "rbt3": "https://paddlenlp.bj.bcebos.com/models/transformers/rbt3/rbt3_chn_large.pdparams",
            "rbtl3": "https://paddlenlp.bj.bcebos.com/models/transformers/rbtl3/rbtl3_chn_large.pdparams",
        }
    }
    base_model_prefix = "roberta"

    def _init_weights(self, layer):
        """Initialization hook"""
        if isinstance(layer, (nn.Linear, nn.Embedding)):
            # only support dygraph, use truncated_normal and make it inplace
            # and configurable later
            layer.weight.set_value(
                paddle.tensor.normal(
                    mean=0.0,
                    std=self.initializer_range
                    if hasattr(self, "initializer_range")
                    else self.roberta.config["initializer_range"],
                    shape=layer.weight.shape,
                )
            )
        elif isinstance(layer, nn.LayerNorm):
            layer._epsilon = 1e-12


@register_base_model
class RobertaModel(RobertaPretrainedModel):
    r"""
    The bare Roberta Model outputting raw hidden-states.

    This model inherits from :class:`~paddlenlp.transformers.model_utils.PretrainedModel`.
    Refer to the superclass documentation for the generic methods.

    This model is also a Paddle `paddle.nn.Layer <https://www.paddlepaddle.org.cn/documentation
    /docs/zh/api/paddle/nn/Layer_cn.html>`__ subclass. Use it as a regular Paddle Layer
    and refer to the Paddle documentation for all matter related to general usage and behavior.

    Args:
        vocab_size (int):
            Vocabulary size of `inputs_ids` in `RobertaModel`. Also is the vocab size of token embedding matrix.
            Defines the number of different tokens that can be represented by the `inputs_ids` passed when calling `RobertaModel`.
        hidden_size (int, optional):
            Dimensionality of the embedding layer, encoder layers and pooler layer. Defaults to `768`.
        num_hidden_layers (int, optional):
            Number of hidden layers in the Transformer encoder. Defaults to `12`.
        num_attention_heads (int, optional):
            Number of attention heads for each attention layer in the Transformer encoder.
            Defaults to `12`.
        intermediate_size (int, optional):
            Dimensionality of the feed-forward (ff) layer in the encoder. Input tensors
            to ff layers are firstly projected from `hidden_size` to `intermediate_size`,
            and then projected back to `hidden_size`. Typically `intermediate_size` is larger than `hidden_size`.
            Defaults to `3072`.
        hidden_act (str, optional):
            The non-linear activation function in the feed-forward layer.
            ``"gelu"``, ``"relu"`` and any other paddle supported activation functions
            are supported. Defaults to ``"gelu"``.
        hidden_dropout_prob (float, optional):
            The dropout probability for all fully connected layers in the embeddings and encoder.
            Defaults to `0.1`.
        attention_probs_dropout_prob (float, optional):
            The dropout probability used in MultiHeadAttention in all encoder layers to drop some attention target.
            Defaults to `0.1`.
        max_position_embeddings (int, optional):
            The maximum value of the dimensionality of position encoding, which dictates the maximum supported length of an input
            sequence. Defaults to `512`.
        type_vocab_size (int, optional):
            The vocabulary size of the `token_type_ids` passed when calling `~transformers.RobertaModel`.
            Defaults to `2`.
        initializer_range (float, optional):
            The standard deviation of the normal initializer. Defaults to 0.02.

            .. note::
                A normal_initializer initializes weight matrices as normal distributions.
                See :meth:`RobertaPretrainedModel._init_weights()` for how weights are initialized in `RobertaModel`.

        pad_token_id(int, optional):
            The index of padding token in the token vocabulary.
            Defaults to `0`.
    """

    def __init__(
        self,
        vocab_size,
        hidden_size=768,
        num_hidden_layers=12,
        num_attention_heads=12,
        intermediate_size=3072,
        hidden_act="gelu",
        hidden_dropout_prob=0.1,
        attention_probs_dropout_prob=0.1,
        max_position_embeddings=512,
        type_vocab_size=16,
        initializer_range=0.02,
        layer_norm_eps=1e-12,
        pad_token_id=0,
    ):
        super(RobertaModel, self).__init__()
        self.pad_token_id = pad_token_id
        self.initializer_range = initializer_range
        self.embeddings = RobertaEmbeddings(
            vocab_size, hidden_size, hidden_dropout_prob, max_position_embeddings, type_vocab_size, pad_token_id
        )
        encoder_layer = TransformerEncoderLayer(
            hidden_size,
            num_attention_heads,
            intermediate_size,
            dropout=hidden_dropout_prob,
            activation=hidden_act,
            attn_dropout=attention_probs_dropout_prob,
            act_dropout=0,
        )
        self.encoder = TransformerEncoder(encoder_layer, num_hidden_layers)
        self.pooler = RobertaPooler(hidden_size)

    def forward(
        self,
        input_ids,
        token_type_ids=None,
        position_ids=None,
        attention_mask=None,
        noise=None,
        i=None,
        n_samples=None,
    ):
        r"""
        Args:
            input_ids (Tensor):
                Indices of input sequence tokens in the vocabulary. They are
                numerical representations of tokens that build the input sequence.
                It's data type should be `int64` and has a shape of [batch_size, sequence_length].
            token_type_ids (Tensor, optional):
                Segment token indices to indicate first and second portions of the inputs.
                Indices can be either 0 or 1:

                - 0 corresponds to a **sentence A** token,
                - 1 corresponds to a **sentence B** token.

                It's data type should be `int64` and has a shape of [batch_size, sequence_length].
                Defaults to None, which means no segment embeddings is added to token embeddings.
            position_ids (Tensor, optional):
                Indices of positions of each input sequence tokens in the position embeddings.
                Selected in the range ``[0, max_position_embeddings - 1]``.
                It's data type should be `int64` and has a shape of [batch_size, sequence_length].
                Defaults to `None`.
            attention_mask (Tensor, optional):
                Mask used in multi-head attention to avoid performing attention to some unwanted positions,
                usually the paddings or the subsequent positions.
                Its data type can be int, float and bool.
                When the data type is bool, the `masked` tokens have `False` values and the others have `True` values.
                When the data type is int, the `masked` tokens have `0` values and the others have `1` values.
                When the data type is float, the `masked` tokens have `-INF` values and the others have `0` values.
                It is a tensor with shape broadcasted to `[batch_size, num_attention_heads, sequence_length, sequence_length]`.
                For example, its shape can be  [batch_size, sequence_length], [batch_size, sequence_length, sequence_length],
                [batch_size, num_attention_heads, sequence_length, sequence_length].
                Defaults to `None`, which means nothing needed to be prevented attention to.

        Returns:
            tuple: Returns tuple (`sequence_output`, `pooled_output`).

            With the fields:

            - sequence_output (Tensor):
                Sequence of hidden-states at the last layer of the model.
                It's data type should be float32 and its shape is [batch_size, sequence_length, hidden_size].

            - pooled_output (Tensor):
                The output of first token (`[CLS]`) in sequence.
                We "pool" the model by simply taking the hidden state corresponding to the first token.
                Its data type should be float32 and its shape is [batch_size, hidden_size].

        Example:
            .. code-block::

                import paddle
                from paddlenlp.transformers import RobertaModel, RobertaTokenizer

                tokenizer = RobertaTokenizer.from_pretrained('roberta-wwm-ext')
                model = RobertaModel.from_pretrained('roberta-wwm-ext')

                inputs = tokenizer("Welcome to use PaddlePaddle and PaddleNLP!")
                inputs = {k:paddle.to_tensor([v]) for (k, v) in inputs.items()}
                sequence_output, pooled_output = model(**inputs)

        """
        if attention_mask is None:
            attention_mask = paddle.unsqueeze(
                (input_ids == self.pad_token_id).astype(self.pooler.dense.weight.dtype) * -1e9, axis=[1, 2]
            )
        # CLS: 101; SEP: 102; PAD: 0
        baseline_ids = paddle.to_tensor(
            [101] + [0] * (input_ids.shape[1] - 2) + [102],
            dtype=input_ids.dtype,
            place=input_ids.place,
            stop_gradient=input_ids.stop_gradient,
        )

        embedding_output = self.embeddings(
            input_ids=input_ids, position_ids=position_ids, token_type_ids=token_type_ids
        )
        baseline_embedding_output = self.embeddings(
            input_ids=baseline_ids, position_ids=position_ids, token_type_ids=token_type_ids
        )

        if noise is not None:
            if noise.upper() == "GAUSSIAN":
                pass
                # stdev_spread = 0.15
                # stdev = stdev_spread * (orig_embedded.max() - orig_embedded.min()).numpy()
                # noise = paddle.to_tensor(np.random.normal(0, stdev, orig_embedded.shape).astype(np.float32),
                #                     stop_gradient=False)
                # orig_embedded = orig_embedded + noise
            if noise.upper() == "INTEGRATED":
                embedding_output = baseline_embedding_output + i / (n_samples - 1) * (
                    embedding_output - baseline_embedding_output
                )
            else:
                raise ValueError("unsupported noise method: %s" % (noise))

        # encoder_outputs = self.encoder(embedding_output, attention_mask)
        encoder_outputs, att_weights_list = self.encoder(embedding_output, attention_mask)  # interpret
        sequence_output = encoder_outputs
        pooled_output = self.pooler(sequence_output)
        return sequence_output, pooled_output, att_weights_list, embedding_output


class RobertaForQuestionAnswering(RobertaPretrainedModel):
    r"""
    Roberta Model with a linear layer on top of the hidden-states output to
    compute `span_start_logits` and `span_end_logits`, designed for question-answering tasks like SQuAD.

    Args:
        roberta (:class:`RobertaModel`):
            An instance of RobertaModel.
        dropout (float, optional):
            The dropout probability for output of Roberta.
            If None, use the same value as `hidden_dropout_prob` of `RobertaModel`
            instance `roberta`. Defaults to `None`.
    """

    def __init__(self, roberta, dropout=None):
        super(RobertaForQuestionAnswering, self).__init__()
        self.roberta = roberta  # allow roberta to be config
        self.classifier = nn.Linear(self.roberta.config["hidden_size"], 2)

    def forward(self, input_ids, token_type_ids=None):
        r"""
        Args:
            input_ids (Tensor):
                See :class:`RobertaModel`.
            token_type_ids (Tensor, optional):
                See :class:`RobertaModel`.
            position_ids (Tensor, optional):
                See :class:`RobertaModel`.
            attention_mask (Tensor, optional):
                See :class:`RobertaModel`.

        Returns:
            tuple: Returns tuple (`start_logits`, `end_logits`).

            With the fields:

            - `start_logits` (Tensor):
                A tensor of the input token classification logits, indicates the start position of the labelled span.
                Its data type should be float32 and its shape is [batch_size, sequence_length].

            - `end_logits` (Tensor):
                A tensor of the input token classification logits, indicates the end position of the labelled span.
                Its data type should be float32 and its shape is [batch_size, sequence_length].

        Example:
            .. code-block::

                import paddle
                from paddlenlp.transformers import RobertaForSequenceClassification, RobertaTokenizer

                tokenizer = RobertaTokenizer.from_pretrained('roberta-wwm-ext')
                model = RobertaForSequenceClassification.from_pretrained('roberta-wwm-ext')

                inputs = tokenizer("Welcome to use PaddlePaddle and PaddleNLP!")
                inputs = {k:paddle.to_tensor([v]) for (k, v) in inputs.items()}
                logits = model(**inputs)

        """
        sequence_output, _ = self.roberta(
            input_ids, token_type_ids=token_type_ids, position_ids=None, attention_mask=None
        )

        logits = self.classifier(sequence_output)
        logits = paddle.transpose(logits, perm=[2, 0, 1])
        start_logits, end_logits = paddle.unstack(x=logits, axis=0)

        return start_logits, end_logits


class RobertaForSequenceClassification(RobertaPretrainedModel):
    r"""
    Roberta Model with a linear layer on top of the output layer,
    designed for sequence classification/regression tasks like GLUE tasks.

    Args:
        roberta (:class:`RobertaModel`):
            An instance of `RobertaModel`.
        num_classes (int, optional):
            The number of classes. Defaults to `2`.
        dropout (float, optional):
            The dropout probability for output of Roberta.
            If None, use the same value as `hidden_dropout_prob`
            of `RobertaModel` instance `roberta`. Defaults to `None`.
    """

    def __init__(self, roberta, num_classes=2, dropout=None):
        super(RobertaForSequenceClassification, self).__init__()
        self.num_classes = num_classes
        self.roberta = roberta  # allow roberta to be config
        self.dropout = nn.Dropout(dropout if dropout is not None else self.roberta.config["hidden_dropout_prob"])
        self.classifier = nn.Linear(self.roberta.config["hidden_size"], num_classes)
        self.softmax = nn.Softmax()

    def forward(self, input_ids, token_type_ids=None, position_ids=None, attention_mask=None):
        r"""
        Args:
            input_ids (Tensor):
                See :class:`RobertaModel`.
            token_type_ids (Tensor, optional):
                See :class:`RobertaModel`.
            position_ids (Tensor, optional):
                See :class:`RobertaModel`.
            attention_mask (Tensor, optional):
                See :class:`RobertaModel`.

        Returns:
            Tensor: Returns tensor `logits`, a tensor of the input text classification logits.
            Its data type should be float32 and it has a shape of [batch_size, num_classes].

        Example:
            .. code-block::

                import paddle
                from paddlenlp.transformers import RobertaForSequenceClassification, RobertaTokenizer

                tokenizer = RobertaTokenizer.from_pretrained('roberta-wwm-ext')
                model = RobertaForSequenceClassification.from_pretrained('roberta-wwm-ext')

                inputs = tokenizer("Welcome to use PaddlePaddle and PaddleNLP!")
                inputs = {k:paddle.to_tensor([v]) for (k, v) in inputs.items()}
                logits = model(**inputs)

        """
        _, pooled_output, _, _ = self.roberta(
            input_ids, token_type_ids=token_type_ids, position_ids=position_ids, attention_mask=attention_mask
        )

        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        return logits

    def forward_interpet(
        self,
        input_ids,
        token_type_ids=None,
        position_ids=None,
        attention_mask=None,
        noise=None,
        i=None,
        n_samples=None,
    ):
        _, pooled_output, att_weights_list, embedding_output = self.roberta(
            input_ids,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            attention_mask=attention_mask,
            noise=noise,
            i=i,
            n_samples=n_samples,
        )

        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        probs = self.softmax(logits)

        return probs, att_weights_list, embedding_output


class RobertaForTokenClassification(RobertaPretrainedModel):
    r"""
    Roberta Model with a linear layer on top of the hidden-states output layer,
    designed for token classification tasks like NER tasks.

    Args:
        roberta (:class:`RobertaModel`):
            An instance of `RobertaModel`.
        num_classes (int, optional):
            The number of classes. Defaults to `2`.
        dropout (float, optional):
            The dropout probability for output of Roberta.
            If None, use the same value as `hidden_dropout_prob`
            of `RobertaModel` instance `roberta`. Defaults to `None`.
    """

    def __init__(self, roberta, num_classes=2, dropout=None):
        super(RobertaForTokenClassification, self).__init__()
        self.num_classes = num_classes
        self.roberta = roberta  # allow roberta to be config
        self.dropout = nn.Dropout(dropout if dropout is not None else self.roberta.config["hidden_dropout_prob"])
        self.classifier = nn.Linear(self.roberta.config["hidden_size"], num_classes)

    def forward(self, input_ids, token_type_ids=None, position_ids=None, attention_mask=None):
        r"""
        Args:
            input_ids (Tensor):
                See :class:`RobertaModel`.
            token_type_ids (Tensor, optional):
                See :class:`RobertaModel`.
            position_ids (Tensor, optional):
                See :class:`RobertaModel`.
            attention_mask (Tensor, optional):
                See :class:`RobertaModel`.

        Returns:
            Tensor: Returns tensor `logits`, a tensor of the input token classification logits.
            Shape as `[batch_size, sequence_length, num_classes]` and dtype as `float32`.

        Example:
            .. code-block::

                import paddle
                from paddlenlp.transformers import RobertaForTokenClassification, RobertaTokenizer

                tokenizer = RobertaTokenizer.from_pretrained('roberta-wwm-ext')
                model = RobertaForTokenClassification.from_pretrained('roberta-wwm-ext')

                inputs = tokenizer("Welcome to use PaddlePaddle and PaddleNLP!")
                inputs = {k:paddle.to_tensor([v]) for (k, v) in inputs.items()}
                logits = model(**inputs)

        """
        sequence_output, _ = self.roberta(
            input_ids, token_type_ids=token_type_ids, position_ids=position_ids, attention_mask=attention_mask
        )

        sequence_output = self.dropout(sequence_output)
        logits = self.classifier(sequence_output)
        return logits
