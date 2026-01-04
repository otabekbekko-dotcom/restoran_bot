import sqlite3
import json

class Database:
    def __init__(self, db_file="restaurant.db"):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()
        self.create_tables()
        self.add_sample_data()
    
    def create_tables(self):
        # Kategoriyalar jadvali
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        ''')
        
        # Mahsulotlar jadvali
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                category_id INTEGER,
                description TEXT,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')
        
        # Buyurtmalar jadvali
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                items TEXT NOT NULL,
                total INTEGER NOT NULL,
                payment_method TEXT,
                status TEXT DEFAULT 'yangi',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.connection.commit()
    
    def add_sample_data(self):
        # Agar ma'lumotlar bo'lsa, qayta qo'shmaslik
        self.cursor.execute("SELECT COUNT(*) FROM categories")
        if self.cursor.fetchone()[0] > 0:
            return
        
        # Demo kategoriyalar
        categories = [
            ('🍕 Pitsa',),
            ('🍔 Burger',),
            ('🥤 Ichimliklar',),
            ('🍰 Desertlar',)
        ]
        self.cursor.executemany("INSERT INTO categories (name) VALUES (?)", categories)
        
        # Demo mahsulotlar
        products = [
            ('Margarita', 45000, 1, 'Klassik italyan pitsasi'),
            ('Pepperoni', 55000, 1, 'Pepperoni kolbasa bilan'),
            ('Tovuqli pitsa', 50000, 1, 'Tovuq go\'shti va zaytun'),
            
            ('Klassik burger', 35000, 2, 'Mol go\'shti, pomidor, salat'),
            ('Chizburger', 40000, 2, 'Ikki qavat go\'sht va pishloq'),
            ('Tovuqli burger', 38000, 2, 'Qovurilgan tovuq filesi'),
            
            ('Cola 0.5L', 8000, 3, 'Sovuq cola'),
            ('Fanta 0.5L', 8000, 3, 'Apelsinli ichimlik'),
            ('Suv 0.5L', 3000, 3, 'Toza ichimlik suvi'),
            
            ('Shokoladli tort', 25000, 4, 'Yumshoq shokoladli'),
            ('Cheesecake', 30000, 4, 'Klassik cheesecake'),
        ]
        self.cursor.executemany(
            "INSERT INTO products (name, price, category_id, description) VALUES (?, ?, ?, ?)", 
            products
        )
        
        self.connection.commit()
    
    def get_categories(self):
        self.cursor.execute("SELECT * FROM categories")
        return self.cursor.fetchall()
    
    def get_products_by_category(self, category_id):
        self.cursor.execute(
            "SELECT * FROM products WHERE category_id = ?", 
            (category_id,)
        )
        return self.cursor.fetchall()
    
    def get_product(self, product_id):
        self.cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        return self.cursor.fetchone()
    
    def create_order(self, user_id, username, full_name, phone, items, total, payment_method):
        self.cursor.execute('''
            INSERT INTO orders (user_id, username, full_name, phone, items, total, payment_method)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, full_name, phone, json.dumps(items), total, payment_method))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def get_all_orders(self):
        self.cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
        return self.cursor.fetchall()
    
    def close(self):
        self.connection.close()