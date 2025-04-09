import requests
from bs4 import BeautifulSoup

def test_registration():
    # Utwórz sesję, aby obsługiwać ciasteczka i przekierowania
    session = requests.Session()
    
    # Najpierw pobierz stronę rejestracji, aby uzyskać token CSRF
    try:
        response = session.get('http://127.0.0.1:5000/auth/register')
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
        
        print("CSRF token pobrany:", csrf_token)
        
        # Dane testowego użytkownika
        user_data = {
            'csrf_token': csrf_token,
            'username': 'testuser123',
            'email': 'testuser123@example.com',
            'password': 'Test123!',
            'password2': 'Test123!',
            'role': 'user',
            'submit': 'Zarejestruj się'
        }
        
        # Wysłanie formularza rejestracji
        response = session.post('http://127.0.0.1:5000/auth/register', data=user_data)
        
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
        
        # Sprawdź, czy jesteśmy przekierowani do strony logowania
        login_title = soup.find('h2')
        if login_title and 'Logowanie' in login_title.text:
            print("Przekierowano do strony logowania - rejestracja udana!")
        else:
            print("Nie przekierowano do strony logowania - rejestracja nieudana.")
            
        print("\nStatus odpowiedzi:", response.status_code)
        print("URL odpowiedzi:", response.url)
        
    except Exception as e:
        print(f"Wystąpił błąd: {e}")

if __name__ == "__main__":
    test_registration() 