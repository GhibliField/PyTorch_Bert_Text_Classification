# @Author : bamtercelboo
# @Datetime : 2018/8/17 16:06
# @File : BiLSTM.py
# @Last Modify Time : 2018/8/17 16:06
# @Contact : bamtercelboo@{gmail.com, 163.com}

"""
    FILE :  BiLSTM.py
    FUNCTION : None
"""

import torch.nn.functional as F
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence
import random
from DataUtils.Common import *
from models.Text_Classification.initialize import *
from models.Text_Classification.modelHelp import prepare_pack_padded_sequence
torch.manual_seed(seed_num)
random.seed(seed_num)


class BiLSTM(nn.Module):
    """
        BiLSTM
    """

    def __init__(self, **kwargs):
        super(BiLSTM, self).__init__()
        for k in kwargs:
            self.__setattr__(k, kwargs[k])

        V = self.embed_num
        D = self.embed_dim
        C = self.label_num
        paddingId = self.paddingId

        self.embed = nn.Embedding(V, D, padding_idx=paddingId)

        if self.pretrained_embed:
            self.embed.weight.data.copy_(self.pretrained_weight)
        else:
            init_embedding(self.embed.weight)

        self.dropout_embed = nn.Dropout(self.dropout_emb)
        self.dropout = nn.Dropout(self.dropout)

        self.bilstm = nn.LSTM(input_size=D, hidden_size=self.lstm_hiddens, num_layers=self.lstm_layers,
                              bidirectional=True, batch_first=True, bias=True)

        self.linear = nn.Linear(in_features=self.lstm_hiddens * 2 + self.bert_out_dim,
                                out_features=C, bias=True)
        # init_linear_weight_bias(self.linear)
        init_linear(self.linear)

    def forward(self, word, bert_fea, sentence_length):
        """
        :param word:
        :param bert_fea:
        :param sentence_length:
        :return:
        """
        word, sentence_length, desorted_indices = prepare_pack_padded_sequence(word, sentence_length, device=self.device)
        x = self.embed(word)  # (N,W,D)
        x = self.dropout_embed(x)
        packed_embed = pack_padded_sequence(x, sentence_length, batch_first=True)
        x, _ = self.bilstm(packed_embed)
        x, _ = pad_packed_sequence(x, batch_first=True)
        x = x[desorted_indices]
        x = x.permute(0, 2, 1)
        x = self.dropout(x)
        x = F.max_pool1d(x, x.size(2)).squeeze(2)
        x = torch.cat((x, bert_fea), 1)
        x = torch.tanh(x)
        logit = self.linear(x)
        return logit
