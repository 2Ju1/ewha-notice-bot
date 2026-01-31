import torch
from torch import nn
import gluonnlp as nlp
from kobert_tokenizer import KoBERTTokenizer
from transformers import BertModel

# KoBERT 모델 정의 (노트북과 동일한 구조)
class BERTClassifier(nn.Module):
    def __init__(self, bert, hidden_size=768, num_classes=2, dr_rate=None, params=None):
        super(BERTClassifier, self).__init__()
        self.bert = bert
        self.dr_rate = dr_rate
                 
        self.classifier = nn.Linear(hidden_size, num_classes)
        if dr_rate:
            self.dropout = nn.Dropout(p=dr_rate)
    
    def gen_attention_mask(self, token_ids, valid_length):
        attention_mask = torch.zeros_like(token_ids)
        for i, v in enumerate(valid_length):
            attention_mask[i][:v] = 1
        return attention_mask.float()

    def forward(self, token_ids, valid_length, segment_ids):
        attention_mask = self.gen_attention_mask(token_ids, valid_length)
        
        _, pooler = self.bert(
            input_ids=token_ids, 
            token_type_ids=segment_ids.long(), 
            attention_mask=attention_mask.float().to(token_ids.device)
        )
        if self.dr_rate:
            out = self.dropout(pooler)
        else:
            out = pooler
        return self.classifier(out)


class NoticeClassifier:
    def __init__(self, model_path='models/kobert_llrd.pth'):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🔧 디바이스: {self.device}")
        
        # KoBERT 토크나이저 & 모델 로드 (노트북과 동일)
        self.tokenizer = KoBERTTokenizer.from_pretrained('skt/kobert-base-v1')
        bertmodel = BertModel.from_pretrained('skt/kobert-base-v1', return_dict=False)
        self.vocab = nlp.vocab.BERTVocab.from_sentencepiece(
            self.tokenizer.vocab_file, 
            padding_token='[PAD]'
        )
        
        # 모델 초기화 (dr_rate=0.5는 학습 시 사용한 값)
        self.model = BERTClassifier(bertmodel, dr_rate=0.5)
        
        # 학습된 가중치 로드
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()
        
        self.tok = nlp.data.BERTSPTokenizer(self.tokenizer, self.vocab, lower=False)
        
        print("✅ KoBERT 모델 로드 완료")
    
    def predict(self, titles):
        """공지 제목들을 분류 (0: 불필요, 1: 필요)"""
        predictions = []
        
        for title in titles:
            # 토큰화
            tokens = self.tok(title)
            
            # 패딩
            max_len = 128
            if len(tokens) > max_len:
                tokens = tokens[:max_len]
            
            token_ids = [self.vocab[token] for token in tokens]
            
            # 패딩 추가
            if len(token_ids) < max_len:
                token_ids = token_ids + [self.vocab.token_to_idx['[PAD]']] * (max_len - len(token_ids))
            
            # 텐서 변환
            token_ids_tensor = torch.tensor([token_ids]).to(self.device)
            valid_length = torch.tensor([len(tokens)]).to(self.device)
            segment_ids = torch.zeros_like(token_ids_tensor).to(self.device)
            
            # 예측
            with torch.no_grad():
                out = self.model(token_ids_tensor, valid_length, segment_ids)
                pred = torch.argmax(out, dim=1).cpu().numpy()[0]
                predictions.append(pred)
        
        return predictions