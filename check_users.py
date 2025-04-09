import sqlite3

def check_users():
    # Połączenie z bazą danych
    conn = sqlite3.connect('instance/scout_talent.db')
    cursor = conn.cursor()
    
    # Sprawdzenie liczby użytkowników w bazie
    cursor.execute("SELECT COUNT(*) FROM user")
    user_count = cursor.fetchone()[0]
    print(f"Liczba użytkowników w bazie: {user_count}")
    
    # Pobierz wszystkich użytkowników
    cursor.execute("SELECT id, username, email, role FROM user")
    users = cursor.fetchall()
    
    # Wypisz informacje o użytkownikach
    print("\nLista użytkowników:")
    print("ID | Nazwa użytkownika | Email | Rola")
    print("-" * 60)
    for user in users:
        print(f"{user[0]} | {user[1]} | {user[2]} | {user[3]}")
    
    conn.close()

if __name__ == "__main__":
    check_users() 