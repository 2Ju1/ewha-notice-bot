# main.py

import os
import sys
from crawler import EwhaNoticeCrawler
from model_predictor import NoticeClassifier
from telegram_bot import TelegramBot

def main():
    print("="*50)
    print("🚀 이화여대 공지사항 알림 시스템")
    print("="*50)
    
    # 환경 변수 확인
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    MODEL_PATH = 'models/kobert_llrd.pth'  # KoBERT 모델로 변경
    
    # 필수 설정 확인
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN 환경변수가 설정되지 않았습니다")
        sys.exit(1)
    
    if not CHAT_ID:
        print("❌ TELEGRAM_CHAT_ID 환경변수가 설정되지 않았습니다")
        sys.exit(1)
    
    if not os.path.exists(MODEL_PATH):
        print(f"❌ 모델 파일을 찾을 수 없습니다: {MODEL_PATH}")
        sys.exit(1)
    
    try:
        # 텔레그램 봇 초기화
        bot = TelegramBot(BOT_TOKEN, CHAT_ID)
        
        # 1단계: 크롤링
        print("\n[1/3] 🕷️ 공지사항 크롤링 중...")
        crawler = EwhaNoticeCrawler()
        new_notices = crawler.get_new_notices()
        
        if not new_notices:
            print("📭 새 공지가 없습니다")
            bot.send_message("📭 이화여대 새 공지사항이 없습니다")
            return
        
        # 2단계: ML 분류
        print(f"\n[2/3] 🤖 KoBERT 모델로 분류 중... ({len(new_notices)}개)")
        classifier = NoticeClassifier(model_path=MODEL_PATH)
        titles = [notice['title'] for notice in new_notices]
        predictions = classifier.predict(titles)
        
        # 학생에게 중요한 공지만 필터 (label=1)
        important_notices = []
        for notice, pred in zip(new_notices, predictions):
            notice['ml_prediction'] = int(pred)
            if pred == 1:
                important_notices.append(notice)
        
        print(f"✅ {len(new_notices)}개 중 {len(important_notices)}개가 중요 공지로 분류됨")
        
        # 통계 출력
        by_category = {}
        for notice in important_notices:
            cat = notice['category']
            by_category[cat] = by_category.get(cat, 0) + 1
        
        print(f"\n📊 카테고리별 분포:")
        for cat, count in by_category.items():
            print(f"   - {cat}: {count}개")
        
        # 3단계: 텔레그램 발송
        print(f"\n[3/3] 📤 텔레그램 전송 중...")
        if important_notices:
            bot.send_notices(important_notices)
            print(f"✅ {len(important_notices)}개 공지 전송 완료!")
        else:
            bot.send_message("📭 새 공지가 있지만 학생 관련 중요 공지는 없습니다")
            print("📭 중요 공지 없음")
        
        print("\n✅ 모든 작업 완료!")
        
    except Exception as e:
        error_msg = f"❌ 오류 발생: {str(e)}"
        print(error_msg)
        
        # 에러도 텔레그램으로 알림
        try:
            bot = TelegramBot(BOT_TOKEN, CHAT_ID)
            bot.send_message(f"⚠️ 시스템 오류\n\n{error_msg}")
        except:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()