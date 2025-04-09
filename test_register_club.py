import requests
from bs4 import BeautifulSoup

def test_club_registration():
    # Utwórz sesję, aby obsługiwać ciasteczka i przekierowania
    session = requests.Session()
    
    # Najpierw pobierz stronę rejestracji klubu, aby uzyskać token CSRF
    try:
        response = session.get('http://127.0.0.1:5000/clubs/register')
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
        
        print("CSRF token pobrany:", csrf_token)
        
        # Dane testowego klubu
        club_data = {
            'csrf_token': csrf_token,
            'name': 'Test Football Club',
            'email': 'testclub@example.com',
            'password': 'ClubTest123!',
            'password2': 'ClubTest123!',
            'city': 'Warszawa',
            'description': 'Testowy klub piłkarski do celów testowych',
            'submit': 'Zarejestruj klub'
        }
        
        # Wysłanie formularza rejestracji
        response = session.post('http://127.0.0.1:5000/clubs/register', data=club_data)
        
        # Sprawdzenie odpowiedzi
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Szukaj komunikatów flash
        flash_messages = soup.select('.flash-message')
        if flash_messages:
            for message in flash_messages:
                print(f"Komunikat flash: {message.text}")
        
        # Szukaj komunikatów o błędach
        error_messages = soup.select('.error-msg')
        if error_messages:
            for error in error_messages:
                print(f"Błąd: {error.text}")
        
        # Sprawdź, czy jesteśmy przekierowani do strony logowania klubu
        login_title = soup.find('h2')
        if login_title and 'Logowanie do Panelu Klubu' in login_title.text:
            print("Przekierowano do strony logowania klubu - rejestracja udana!")
        else:
            print("Nie przekierowano do strony logowania klubu - rejestracja nieudana.")
            
        print("\nStatus odpowiedzi:", response.status_code)
        print("URL odpowiedzi:", response.url)
        
    except Exception as e:
        print(f"Wystąpił błąd: {e}")

if __name__ == "__main__":
    test_club_registration() 