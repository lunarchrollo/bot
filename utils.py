from db import Session, User

def get_or_create_user(telegram_id, referrer_id=None):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, referrer_id=referrer_id)
        session.add(user)
        session.commit()
    session.close()
    return user
