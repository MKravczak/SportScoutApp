import sqlite3

def clean_test_data():
    # Połączenie z bazą danych
    conn = sqlite3.connect('instance/scout_talent.db')
    cursor = conn.cursor()
    
    # Sprawdzenie, czy istnieje testowy klub
    cursor.execute("SELECT id FROM club WHERE name = 'Test Football Club'")
    club = cursor.fetchone()
    
    if club:
        club_id = club[0]
        print(f"Znaleziono testowy klub z ID: {club_id}")
        
        # Sprawdzenie, czy istnieje testowy zarządca klubu
        cursor.execute("SELECT id FROM user WHERE username = 'Test Football Club'")
        user = cursor.fetchone()
        
        if user:
            user_id = user[0]
            print(f"Znaleziono testowego zarządcę klubu z ID: {user_id}")
            
            # Usunięcie użytkownika
            cursor.execute("DELETE FROM user WHERE id = ?", (user_id,))
            print(f"Usunięto użytkownika z ID: {user_id}")
        
        # Usunięcie klubu
        cursor.execute("DELETE FROM club WHERE id = ?", (club_id,))
        print(f"Usunięto klub z ID: {club_id}")
        
        # Zapisanie zmian
        conn.commit()
        print("Zmiany zostały zapisane w bazie danych")
    else:
        print("Nie znaleziono testowego klubu w bazie danych")
    
    conn.close()

if __name__ == "__main__":
    clean_test_data() 