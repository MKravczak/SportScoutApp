import sqlite3

def check_clubs():
    # Połączenie z bazą danych
    conn = sqlite3.connect('instance/scout_talent.db')
    cursor = conn.cursor()
    
    # Sprawdzenie liczby klubów w bazie
    cursor.execute("SELECT COUNT(*) FROM club")
    club_count = cursor.fetchone()[0]
    print(f"Liczba klubów w bazie: {club_count}")
    
    # Pobierz wszystkie kluby
    cursor.execute("SELECT id, name, city, description FROM club")
    clubs = cursor.fetchall()
    
    # Wypisz informacje o klubach
    print("\nLista klubów:")
    print("ID | Nazwa | Miasto | Opis")
    print("-" * 60)
    for club in clubs:
        print(f"{club[0]} | {club[1]} | {club[2]} | {club[3]}")
    
    # Sprawdź wszystkich użytkowników z rolą club_manager
    print("\nWszyscy zarządcy klubów:")
    cursor.execute("""
        SELECT u.id, u.username, u.email, u.role, u.club_id 
        FROM user u 
        WHERE u.role = 'club_manager'
    """)
    managers = cursor.fetchall()
    
    print("ID użytkownika | Nazwa użytkownika | Email | Rola | ID klubu")
    print("-" * 80)
    for manager in managers:
        print(f"{manager[0]} | {manager[1]} | {manager[2]} | {manager[3]} | {manager[4]}")
    
    # Sprawdź powiązanie między klubami a użytkownikami
    print("\nPełne powiązania klubów z zarządcami:")
    cursor.execute("""
        SELECT c.id, c.name, u.id, u.username, u.email 
        FROM club c
        LEFT JOIN user u ON c.id = u.club_id AND u.role = 'club_manager'
    """)
    connections = cursor.fetchall()
    
    print("ID klubu | Nazwa klubu | ID użytkownika | Nazwa użytkownika | Email")
    print("-" * 90)
    for conn_data in connections:
        user_id = conn_data[2] if conn_data[2] is not None else "Brak"
        username = conn_data[3] if conn_data[3] is not None else "Brak"
        email = conn_data[4] if conn_data[4] is not None else "Brak"
        print(f"{conn_data[0]} | {conn_data[1]} | {user_id} | {username} | {email}")
    
    conn.close()

if __name__ == "__main__":
    check_clubs() 