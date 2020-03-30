from openvqa.models.mfb.mfb import CoAtt
from openvqa.models.mfb.adapter import Adapter
# from openvqa.models.mfb.tda import CoAtt_vis
import torch
import torch.nn as nn
import numpy as np
import torch.nn.functional as F
from torch.nn.utils.weight_norm import weight_norm
import math
from openvqa.ops.fc import FC, MLP

# -------------------------------------------------------
# ---- Main MFB/MFH model with Co-Attention Learning ----
# -------------------------------------------------------

def grad_reverse(x):
    return GradReverse.apply(x)

class Net(nn.Module):
    def __init__(self, __C, pretrained_emb, token_size, answer_size, pretrain_emb_ans, token_size_ans):
        super(Net, self).__init__()
        self.__C = __C
        '''
        if pretrain_emb_ans is None:
            #print("there is some error in this code\n\n")
            print("Evaluation______________________________")
            self.eval_flag = True
        else:
            print("Training________________________________")
            self.eval_flag = False
        '''

        self.embedding = nn.Embedding(
            num_embeddings=token_size,
            embedding_dim=__C.WORD_EMBED_SIZE
        )
        # Loading the GloVe embedding weights if __C.USE_GLOVE:
        self.embedding.weight.data.copy_(torch.from_numpy(pretrained_emb))

        self.lstm = nn.LSTM(
            input_size=__C.WORD_EMBED_SIZE,
            hidden_size=__C.LSTM_OUT_SIZE,
            num_layers=1,
            batch_first=True
        )
        self.dropout = nn.Dropout(__C.DROPOUT_R)
        self.dropout_lstm = nn.Dropout(__C.DROPOUT_R)
        
        '''
        self.adapter = Adapter(__C)
        self.ans_backbone = CoAtt(__C) 
        # this adapter will be used in answer part processing,
        # so it does not require gradients
        for params in self.adapter.parameters():
            params.requires_grad = False
        # will be used in the ans part, does not require grads
        for params in self.ans_backbone.parameters():
            params.requires_grad = False
        '''
        self.img_adapter = Adapter(__C)
        self.backbone = CoAtt(__C)

        
       # classification/projection layers
       # for the time being keep the decoder trainable
        if __C.HIGH_ORDER:      # MFH
            '''
            self.decoder_mlp_1 = MLP(
                in_size=2*__C.MFB_O,
                mid_size=2*__C.MFB_O,
                out_size= 4*__C.MFB_O,
                dropout_r=0,
                use_relu=True
            )
            
            self.decoder_mlp_2 = MLP(
                in_size=4*__C.MFB_O,
                mid_size=2*__C.MFB_O,
                out_size=answer_size,
                dropout_r=0,
                use_relu=True
            )
            '''
            self.proj = nn.Linear(2*__C.MFB_O, answer_size)
            
        else:                   # MFB
            '''
            self.decoder_mlp_1 = MLP(
                in_size=__C.MFB_O,
                mid_size=__C.MFB_O,
                out_size= 2*__C.MFB_O,
                dropout_r=0,
                use_relu=True
            )
            
            self.decoder_mlp_2 = MLP(
                in_size=2*__C.MFB_O,
                mid_size=__C.MFB_O,
                out_size=answer_size,
                dropout_r=0,
                use_relu=True
            )
            '''
            self.proj = nn.Linear(__C.MFB_O, answer_size)
            
        '''
        for params in self.proj.parameters():
            params.requires_grad = False

        # no grads ---- fixed decoder

        '''
        '''
        for params in self.decoder_mlp_1.parameters():
            params.requires_grad = False
        for params in self.decoder_mlp_2.parameters():
            params.requires_grad = False
        '''
        '''
        # With Answer
        #if(self.__C.WITH_ANSWER):

        self.ans_embedding = nn.Embedding(
            num_embeddings=token_size_ans,
            embedding_dim=__C.WORD_EMBED_SIZE
        )
        # will be used in the ans part, does not require grads
        for params in self.ans_embedding.parameters():
            params.requires_grad = False
        
        # Loading the GloVe embedding weights
        if __C.USE_GLOVE:
            if not self.eval_flag:
                print("EVAL_FLAG: ", self.eval_flag)
                self.ans_embedding.weight.data.copy_(torch.from_numpy(pretrain_emb_ans))
    
        if __C.HIGH_ORDER:
            self.ans_lstm = nn.LSTM(
                input_size=__C.WORD_EMBED_SIZE,
                hidden_size=__C.LSTM_OUT_SIZE,
                num_layers=1,
                batch_first=True
            )
        else:
            self.ans_lstm = nn.LSTM(
                input_size=__C.WORD_EMBED_SIZE,
                hidden_size=__C.LSTM_OUT_SIZE,
                num_layers=1,
                batch_first=True
            )
        
        self.ans_dropout = nn.Dropout(__C.DROPOUT_R)
        self.ans_dropout_lstm = nn.Dropout(__C.DROPOUT_R)
        # will be used in the ans part, does not require grads
        for params in self.ans_lstm.parameters():
            params.requires_grad = False

        for params in self.ans_dropout.parameters():
            params.requires_grad = False
        for params in self.ans_dropout_lstm.parameters():
            params.requires_grad = False
        
        # parameters for storing npy arrays
        self.batch_size = int(__C.SUB_BATCH_SIZE/__C.N_GPU)
        self.num = math.ceil(1000/self.batch_size) #313

        # storing npy arrays
        if __C.HIGH_ORDER:
            self.shape = (self.num * self.batch_size, int(2*__C.MFB_O))
        else:
            self.shape = (self.num * self.batch_size, int(__C.MFB_O))
        self.z_proj = np.zeros(shape=self.shape)
        self.z_ans = np.zeros(shape=self.shape)
        self.z_fused = np.zeros(shape=self.shape)

        '''

    def forward(self, ques_list, frcn_feat, grid_feat, bbox_feat, ques_ix, ans_ix, step, epoch):

        '''
        ans_img_feat, _ = self.adapter(frcn_feat, grid_feat, bbox_feat)  # (N, C, FRCN_FEAT_SIZE)
        # pre-process the ans features
        self.ans_lstm.flatten_parameters()
        ans_feat = self.ans_embedding(ans_ix)
        ans_feat = self.ans_dropout(ans_feat)
        ans_feat, _ = self.ans_lstm(ans_feat)
        ans_feat = self.ans_dropout_lstm(ans_feat)
        ans_feat = self.ans_backbone(ans_img_feat, ans_feat)
        # (batch_size, answer_size)
        ans_feat = self.proj(ans_feat)
        return ans_feat
        '''
        
        img_feat, _ = self.img_adapter(frcn_feat, grid_feat, bbox_feat)  # (N, C, FRCN_FEAT_SIZE)
        # Pre-process Language Feature
        self.lstm.flatten_parameters()
        lang_feat = self.embedding(ques_ix)     # (N, T, WORD_EMBED_SIZE)
        lang_feat = self.dropout(lang_feat)
        lang_feat, _ = self.lstm(lang_feat)     # (N, T, LSTM_OUT_SIZE)
        lang_feat = self.dropout_lstm(lang_feat)
        
        #######################################################
        ########## Using bbox feat for attention vis ##########

        
        #Backbone to combine the image and the Question
        proj_feat = self.backbone(img_feat, lang_feat,bbox_feat)  # MFH:(N, 2*O) / MFB:(N, O)


        if (self.__C.WITH_ANSWER == False or self.eval_flag == True):
            # use the decoder
            # change: do not use the decoder gru
            #proj_feat = self.decoder_mlp_1(proj_feat)
            #proj_feat = self.decoder_mlp_2(proj_feat)

            proj_feat = self.proj(proj_feat)

            if (self.__C.WITH_ANSWER == True and self.eval_flag == True):
                #hack because test_engine expects multiple returns from net but only uses the first
                return proj_feat, None 


            return proj_feat
        
        ############ WITH ANSWER ##############
        else:

            # --------------------------- #
            # ---- Answer embeddings ---- #
            # --------------------------- #

            ans_img_feat, _ = self.adapter(frcn_feat, grid_feat, bbox_feat)  # (N, C, FRCN_FEAT_SIZE)
            # pre-process the ans features
            self.ans_lstm.flatten_parameters()
            ans_feat = self.ans_embedding(ans_ix)
            ans_feat = self.ans_dropout(ans_feat)
            ans_feat, _ = self.ans_lstm(ans_feat)
            ans_feat = self.ans_dropout_lstm(ans_feat)

            ans_feat = self.ans_backbone(ans_img_feat, ans_feat,bbox_feat)
           
            # ---------------------- #
            # ---- Adding noise ---- #
            # ---------------------- #

            # randomly sample a number 'u' between zero and one
            u = torch.rand(1).cuda()

            proj_noise = self.__C.PROJ_STDDEV * torch.randn(proj_feat.shape).cuda()
            ans_noise = self.__C.ANS_STDDEV * torch.randn(ans_feat.shape).cuda()
            
            #ans_feat += ans_noise
            #proj_feat += proj_noise

            # now we can fuse the vector
            # (batch_size, (1 or 2) * __C.MFB_O)
            fused_feat = torch.add(torch.mul(u, proj_feat), torch.mul(1-u, ans_feat))

            # --------------------------- #
            # ---- SAVE THE FEATURES ---- #
            # --------------------------- #

            # For calculating Fusion Loss in train_engine
            # also normalize the vectors before calculating loss
            z_proj = F.normalize(proj_feat.clone(), p=2, dim=1)
            z_ans = F.normalize(ans_feat.clone(), p=2, dim=1)
            z_fused = F.normalize(fused_feat.clone(), p=2, dim=1)

            if (step < self.num):
                self.z_proj[ (step * self.batch_size) : ((step+1) * self.batch_size) ] = proj_feat.clone().detach().cpu().numpy()
                self.z_ans[ (step * self.batch_size) : ((step+1) * self.batch_size) ] = ans_feat.clone().detach().cpu().numpy()
                self.z_fused[ (step * self.batch_size) : ((step+1) * self.batch_size) ] = fused_feat.clone().detach().cpu().numpy()


            elif (step == self.num):
                np.save(self.__C.SAVED_PATH + '/' + self.__C.VERSION + '/z_proj_' + str(epoch) + '.npy', self.z_proj)
                np.save(self.__C.SAVED_PATH + '/' + self.__C.VERSION + '/z_ans_' + str(epoch) + '.npy', self.z_ans)
                np.save(self.__C.SAVED_PATH + '/' + self.__C.VERSION + '/z_fused_' + str(epoch) + '.npy', self.z_fused)

            elif (step == (self.num + 1)):
                self.z_proj = np.zeros(shape=self.shape)
                self.z_ans = np.zeros(shape=self.shape)
                self.z_fused = np.zeros(shape=self.shape)

            # ----------------- #
            # ---- DECODER ---- #
            # ----------------- #

            # (batch_size, answer_size)
            #proj_feat = self.decoder_mlp_1(proj_feat)
            #proj_feat = self.decoder_mlp_2(proj_feat)
            proj_feat = self.proj(proj_feat)

            ## (batch_size, answer_size)
            #ans_feat = self.decoder_mlp_1(ans_feat)
            #ans_feat = self.decoder_mlp_2(ans_feat)
            ans_feat = self.proj(ans_feat)
            #
            ## (batch_size, answer_size)
            #fused_feat = self.decoder_mlp_1(fused_feat)
            #fused_feat = self.decoder_mlp_2(fused_feat)
            fused_feat = self.proj(fused_feat)

            return proj_feat, ans_feat, fused_feat, z_proj, z_ans, z_fused
