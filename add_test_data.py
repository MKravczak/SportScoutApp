#!/usr/bin/env python3
# Skrypt dodający przykładowe testy sportowe dla dyscyplin

from app import create_app
from app.models import Sport, SportTest

def add_test_data():
    app = create_app()
    with app.app_context():
        from app import db
        # Sprawdzamy istniejące dyscypliny
        sports = Sport.query.all()
        print(f"Znalezione dyscypliny: {[s.name for s in sports]}")
        
        # Dla każdej dyscypliny dodajemy odpowiednie testy
        for sport in sports:
            tests_count = SportTest.query.filter_by(sport_id=sport.id).count()
            print(f"Dyscyplina {sport.name} ma {tests_count} testów")
            
            if tests_count == 0:
                if "piłka nożna" in sport.name.lower():
                    print(f"Dodaję testy dla piłki nożnej (ID: {sport.id})...")
                    tests = [
                        SportTest(
                            name="Sprint 30m", 
                            description="Test szybkości na 30 metrów", 
                            type="szybkość", 
                            unit="sekundy", 
                            is_lower_better=True, 
                            sport_id=sport.id
                        ),
                        SportTest(
                            name="Strzały na bramkę", 
                            description="Test celności strzałów", 
                            type="technika", 
                            unit="punkty", 
                            is_lower_better=False, 
                            sport_id=sport.id
                        ),
                        SportTest(
                            name="Podania celne", 
                            description="Test celności podań", 
                            type="technika", 
                            unit="procent", 
                            is_lower_better=False, 
                            sport_id=sport.id
                        ),
                    ]
                    db.session.add_all(tests)
                    
                elif "koszykówka" in sport.name.lower():
                    print(f"Dodaję testy dla koszykówki (ID: {sport.id})...")
                    tests = [
                        SportTest(
                            name="Rzuty za 3 punkty", 
                            description="Test celności rzutów za 3", 
                            type="technika", 
                            unit="procent", 
                            is_lower_better=False, 
                            sport_id=sport.id
                        ),
                        SportTest(
                            name="Rzuty osobiste", 
                            description="Test rzutów osobistych", 
                            type="technika", 
                            unit="procent", 
                            is_lower_better=False, 
                            sport_id=sport.id
                        ),
                        SportTest(
                            name="Sprint z piłką", 
                            description="Test szybkości z piłką", 
                            type="szybkość", 
                            unit="sekundy", 
                            is_lower_better=True, 
                            sport_id=sport.id
                        ),
                    ]
                    db.session.add_all(tests)
                    
                else:
                    # Dodajemy domyślne testy dla innych dyscyplin
                    print(f"Dodaję domyślne testy dla dyscypliny {sport.name} (ID: {sport.id})...")
                    tests = [
                        SportTest(
                            name="Test szybkości", 
                            description="Ogólny test szybkości", 
                            type="szybkość", 
                            unit="sekundy", 
                            is_lower_better=True, 
                            sport_id=sport.id
                        ),
                        SportTest(
                            name="Test siły", 
                            description="Ogólny test siły", 
                            type="siła", 
                            unit="kilogramy", 
                            is_lower_better=False, 
                            sport_id=sport.id
                        ),
                        SportTest(
                            name="Test wytrzymałości", 
                            description="Ogólny test wytrzymałości", 
                            type="wytrzymałość", 
                            unit="punkty", 
                            is_lower_better=False, 
                            sport_id=sport.id
                        ),
                    ]
                    db.session.add_all(tests)
        
        db.session.commit()
        
        # Wypisujemy liczbę testów po dodaniu
        for sport in sports:
            tests = SportTest.query.filter_by(sport_id=sport.id).all()
            print(f"Dyscyplina {sport.name} ma teraz {len(tests)} testów: {[t.name for t in tests]}")

if __name__ == "__main__":
    add_test_data()
    print("Przykładowe testy zostały dodane do bazy danych!") 