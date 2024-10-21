from app import create_app, db
from models import User


def check_and_update_users():
    app = create_app()
    with app.app_context():
        # Check Kkscreener
        kkscreener = User.query.filter_by(username='Kkscreener').first()
        if kkscreener:
            print(f'Kkscreener exists. Admin status: {kkscreener.is_admin}')
            if not kkscreener.is_admin:
                kkscreener.is_admin = True
                db.session.commit()
                print('Updated Kkscreener to admin')
        else:
            print('Kkscreener does not exist')

        # Check Jmichelle
        jmichelle = User.query.filter_by(
            email='mrs.jmichelle@gmail.com').first()
        if jmichelle:
            print(
                f'Jmichelle exists. Instructor status: {jmichelle.is_instructor}'
            )
            if not jmichelle.is_instructor:
                jmichelle.is_instructor = True
                db.session.commit()
                print('Updated Jmichelle to instructor')
        else:
            print('Jmichelle does not exist')

        print('Final status:')
        print(
            f'Kkscreener: {User.query.filter_by(username="Kkscreener").first().is_admin}'
        )
        print(
            f'Jmichelle: {User.query.filter_by(email="mrs.jmichelle@gmail.com").first().is_instructor}'
        )


if __name__ == '__main__':
    check_and_update_users()
