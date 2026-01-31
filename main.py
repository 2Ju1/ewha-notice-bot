from crawler import EwhaNoticeCrawler
from model_predictor import NoticeClassifier
from telegram_bot import TelegramNotifier


def main():
    print("=" * 50)
    print("🔔 이화여대 공지사항 자동 알림 시스템")
    print("=" * 50)
    print()
    
    # 1. 크롤링
    print("[1/3] 📥 공지사항 크롤링 중...")
    crawler = EwhaNoticeCrawler()
    new_notices = crawler.get_new_notices()
    print(f"✅ {len(new_notices)}개의 새 공지 발견\n")
    
    if not new_notices:
        print("📭 새로운 공지가 없습니다.")
        return
    
    # 2. 중요도 분류
    print(f"[2/3] 🤖 KoBERT 모델로 분류 중... ({len(new_notices)}개)")
    try:
        classifier = NoticeClassifier()
        titles = [notice['title'] for notice in new_notices]
        predictions = classifier.predict(titles)
        
        # 중요한 공지만 필터링 (pred == 1이 중요)
        important_notices = [
            notice for notice, pred in zip(new_notices, predictions)
            if pred == 1
        ]
        
        print(f"✅ 중요 공지 {len(important_notices)}개 선별 완료\n")
        
        # 중요 공지가 하나도 없으면 전체 전송
        if not important_notices:
            print("⚠️ 중요 공지가 없어 전체 공지를 전송합니다.\n")
            important_notices = new_notices
        
    except Exception as e:
        print(f"⚠️ 모델 분류 실패: {e}")
        print("   전체 공지를 전송합니다.\n")
        important_notices = new_notices
    
    # 3. 텔레그램 전송
    if important_notices:
        print(f"[3/3] 📤 텔레그램으로 {len(important_notices)}개 공지 전송 중...")
        notifier = TelegramNotifier()
        notifier.send_notices(important_notices)
    else:
        print("📭 전송할 공지가 없습니다.")
    
    print()
    print("=" * 50)
    print("✅ 작업 완료!")
    print("=" * 50)


if __name__ == "__main__":
    main()
