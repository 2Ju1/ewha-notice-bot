import torch
from torch import nn
from transformers import BertModel, AutoTokenizer


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
            attention_mask=attention_mask.float().to(token_ids.device),
            return_dict=False
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
        
        # use_fast=False 추가 (tiktoken 없이 사용)
        self.tokenizer = AutoTokenizer.from_pretrained(
            'skt/kobert-base-v1',
            use_fast=False
        )
        bertmodel = BertModel.from_pretrained('skt/kobert-base-v1', return_dict=False)
        
        # 모델 초기화
        self.model = BERTClassifier(bertmodel, dr_rate=0.5)
        
        # 학습된 가중치 로드
        self.model.load_state_dict(torch.load(model_path, map_location=self.device), strict=False))
        self.model.to(self.device)
        self.model.eval()
        
        print("✅ KoBERT 모델 로드 완료")
    
    def predict(self, titles):
        """공지 제목들을 분류 (0: 불필요, 1: 필요)"""
        predictions = []
        max_len = 128
        
        for title in titles:
            # AutoTokenizer로 토큰화
            encoded = self.tokenizer.encode_plus(
                title,
                add_special_tokens=True,
                max_length=max_len,
                padding='max_length',
                truncation=True,
                return_tensors='pt'
            )
            
            token_ids = encoded['input_ids'].to(self.device)
            
            # segment_ids를 0으로 초기화 (수정된 부분)
            segment_ids = torch.zeros_like(token_ids).to(self.device)
            
            # valid_length 계산
            valid_length = torch.tensor([(token_ids != 0).sum().item()])
            
            # 예측
            with torch.no_grad():
                out = self.model(token_ids, valid_length, segment_ids)
                pred = torch.argmax(out, dim=1).cpu().numpy()[0]
                predictions.append(pred)
        
        return predictions
