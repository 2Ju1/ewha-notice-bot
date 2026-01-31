import torch
from transformers import BertTokenizer, BertModel
import torch.nn as nn


class BERTClassifier(nn.Module):
    def __init__(self, bert_model, num_classes=2, hidden_size=768, dropout_rate=0.1):
        super(BERTClassifier, self).__init__()
        self.bert = bert_model
        self.dropout = nn.Dropout(dropout_rate)
        self.classifier = nn.Linear(hidden_size, num_classes)
    
    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        return logits


class NoticeClassifier:
    def __init__(self, model_path='models/kobert_llrd.pth'):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"🔧 디바이스: {self.device}")
        
        # KoBERT 토크나이저 및 모델 로드
        self.tokenizer = BertTokenizer.from_pretrained('monologg/kobert')
        bert_model = BertModel.from_pretrained('monologg/kobert')
        
        # 분류 모델 초기화
        self.model = BERTClassifier(bert_model, num_classes=2).to(self.device)
        
        # 모델 가중치 로드 (strict=False로 position_ids 무시)
        try:
            state_dict = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(state_dict, strict=False)
            self.model.eval()
            print("✅ KoBERT 모델 로드 완료")
        except Exception as e:
            raise RuntimeError(f"모델 로드 실패: {e}")
    
    def predict(self, titles, max_length=128):
        """공지 제목 리스트를 입력받아 중요도 예측"""
        predictions = []
        
        self.model.eval()
        with torch.no_grad():
            for title in titles:
                # 토크나이징
                encoded = self.tokenizer.encode_plus(
                    title,
                    add_special_tokens=True,
                    max_length=max_length,
                    padding='max_length',
                    truncation=True,
                    return_attention_mask=True,
                    return_tensors='pt'
                )
                
                input_ids = encoded['input_ids'].to(self.device)
                attention_mask = encoded['attention_mask'].to(self.device)
                
                # 예측
                logits = self.model(input_ids, attention_mask)
                pred = torch.argmax(logits, dim=1).item()
                predictions.append(pred)
        
        return predictions


# 테스트용 코드
if __name__ == "__main__":
    classifier = NoticeClassifier()
    
    test_titles = [
        "[회계팀] 2026학년도 학부 신입생 및 편입생 등록금 납부 안내",
        "[학사지원팀] 2026-1학기 수강시뮬레이션 안내",
        "[조교모집] 2026-1학기 조교 모집"
    ]
    
    predictions = classifier.predict(test_titles)
    
    print("\n제목 -> 예측 결과:")
    for title, pred in zip(test_titles, predictions):
        status = "✅ 중요" if pred == 1 else "❌ 불필요"
        print(f"  {status}: {title}")
