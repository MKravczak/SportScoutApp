import requests
from bs4 import BeautifulSoup

def test_login():
    # Utwórz sesję, aby obsługiwać ciasteczka i przekierowania
    session = requests.Session()
    
    # Najpierw pobierz stronę logowania, aby uzyskać token CSRF
    try:
        response = session.get('http://127.0.0.1:5000/auth/login')
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
        
        print("CSRF token pobrany:", csrf_token)
        
        # Dane testowego użytkownika (wcześniej zarejestrowanego)
        login_data = {
            'csrf_token': csrf_token,
            'username': 'testuser123',
            'password': 'Test123!',
            'remember_me': 'y',
            'submit': 'Zaloguj się'
        }
        
        # Wysłanie formularza logowania
        response = session.post('http://127.0.0.1:5000/auth/login', data=login_data, allow_redirects=True)
        
        # Sprawdzenie odpowiedzi
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Szukaj komunikatów flash
        flash_messages = soup.select('.flash-message')
        if flash_messages:
            for message in flash_messages:
                print(f"Komunikat flash: {message.text}")
        
        # Szukaj komunikatów o błędach
        error_messages = soup.select('.error')
        if error_messages:
            for error in error_messages:
                print(f"Błąd: {error.text}")
        
        # Sprawdź, czy jesteśmy zalogowani - sprawdzając czy navbar pokazuje wylogowanie
        navbar = soup.select('.nav-menu')
        if navbar and 'Wyloguj' in str(navbar[0]):
            print("Zalogowano pomyślnie!")
        else:
            print("Logowanie nieudane - nie widać opcji wylogowania w menu.")
            
        print("\nStatus odpowiedzi:", response.status_code)
        print("URL odpowiedzi:", response.url)
        
    except Exception as e:
        print(f"Wystąpił błąd: {e}")

if __name__ == "__main__":
    test_login() 