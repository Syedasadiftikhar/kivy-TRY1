from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
import sqlite3
import random

DB_NAME = 'users.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS sensor_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nitrogen REAL,
        phosphorus REAL,
        potassium REAL,
        humidity REAL,
        moisture REAL,
        temperature REAL,
        user_id INTEGER)''')
    conn.commit()
    conn.close()

# Custom Popup
def show_popup(title, message):
    box = BoxLayout(orientation='vertical', padding=10, spacing=10)
    box.add_widget(Label(text=message, font_size=16))
    close_btn = Button(text='Close', size_hint=(1, 0.3))
    box.add_widget(close_btn)
    popup = Popup(title=title, content=box, size_hint=(0.7, 0.4))
    close_btn.bind(on_press=popup.dismiss)
    popup.open()

# Login Screen
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)

        self.username = TextInput(hint_text='Username', multiline=False, size_hint=(1, 0.15))
        self.password = TextInput(hint_text='Password', password=True, multiline=False, size_hint=(1, 0.15))
        login_btn = Button(text='Login', size_hint=(1, 0.2), background_color=(0.2, 0.6, 0.4, 1))
        signup_btn = Button(text='Go to Signup', size_hint=(1, 0.2))
        self.message = Label(size_hint=(1, 0.1), color=(1, 0, 0, 1))

        login_btn.bind(on_press=self.login)
        signup_btn.bind(on_press=self.go_to_signup)

        layout.add_widget(Label(text="Login", font_size=28, size_hint=(1, 0.2)))
        layout.add_widget(self.username)
        layout.add_widget(self.password)
        layout.add_widget(login_btn)
        layout.add_widget(signup_btn)
        layout.add_widget(self.message)
        self.add_widget(layout)

    def go_to_signup(self, instance):
        self.manager.current = 'signup'

    def login(self, instance):
        if not self.username.text or not self.password.text:
            self.message.text = "Please fill both fields!"
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (self.username.text, self.password.text))
        user = c.fetchone()
        conn.close()
        if user:
            App.get_running_app().current_user = user[0]
            self.manager.current = 'home'
        else:
            self.message.text = "Invalid credentials!"

# Signup Screen
class SignupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)

        self.username = TextInput(hint_text='Choose Username', multiline=False, size_hint=(1, 0.15))
        self.password = TextInput(hint_text='Choose Password', password=True, multiline=False, size_hint=(1, 0.15))
        signup_btn = Button(text='Sign Up', size_hint=(1, 0.2), background_color=(0.3, 0.5, 0.7, 1))
        login_btn = Button(text='Back to Login', size_hint=(1, 0.2))
        self.message = Label(size_hint=(1, 0.1), color=(1, 0, 0, 1))

        signup_btn.bind(on_press=self.signup)
        login_btn.bind(on_press=self.go_to_login)

        layout.add_widget(Label(text="Create Account", font_size=28, size_hint=(1, 0.2)))
        layout.add_widget(self.username)
        layout.add_widget(self.password)
        layout.add_widget(signup_btn)
        layout.add_widget(login_btn)
        layout.add_widget(self.message)
        self.add_widget(layout)

    def go_to_login(self, instance):
        self.manager.current = 'login'

    def signup(self, instance):
        if not self.username.text or not self.password.text:
            self.message.text = "All fields are required!"
            return
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (self.username.text, self.password.text))
            user_id = c.lastrowid
            c.execute("""INSERT INTO sensor_data (nitrogen, phosphorus, potassium, humidity, moisture, temperature, user_id)
                         VALUES (?, ?, ?, ?, ?, ?, ?)""",
                      (random.uniform(10, 90), random.uniform(5, 60), random.uniform(10, 80),
                       random.uniform(30, 90), random.uniform(20, 50), random.uniform(20, 40), user_id))
            conn.commit()
            conn.close()
            show_popup("Success", "Account created successfully!")
            self.manager.current = 'login'
        except sqlite3.IntegrityError:
            self.message.text = "Username already taken!"

# Home Screen
class HomeScreen(Screen):
    def on_enter(self):
        self.display_data()

    def display_data(self):
        self.clear_widgets()
        user_id = App.get_running_app().current_user

        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        title = Label(text="Your Sensor Data", font_size=26, bold=True, size_hint=(1, 0.1))
        main_layout.add_widget(title)

        # Scrollable grid for sensor data
        scrollview = ScrollView(size_hint=(1, 0.6))
        data_grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        data_grid.bind(minimum_height=data_grid.setter('height'))

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM sensor_data WHERE user_id=?", (user_id,))
        data = c.fetchone()
        conn.close()

        if data:
            labels = ['Nitrogen (mg/kg)', 'Phosphorus (mg/kg)', 'Potassium (mg/kg)',
                      'Humidity (%)', 'Moisture (%)', 'Temperature (°C)']
            for i, value in enumerate(data[1:7]):
                data_grid.add_widget(Label(text=f"{labels[i]}: {round(value, 2)}", font_size=18, size_hint_y=None, height=30))
        else:
            data_grid.add_widget(Label(text="No sensor data found.", font_size=16, size_hint_y=None, height=30))

        scrollview.add_widget(data_grid)
        main_layout.add_widget(scrollview)

        # Buttons
        btn_layout = BoxLayout(size_hint=(1, 0.15), spacing=10)
        logout_btn = Button(text='Logout', background_color=(0.6, 0.2, 0.2, 1))
        refresh_btn = Button(text='Refresh Data', background_color=(0.2, 0.5, 0.7, 1))
        delete_btn = Button(text='Delete Account', background_color=(0.5, 0.1, 0.1, 1))

        logout_btn.bind(on_press=self.logout)
        refresh_btn.bind(on_press=self.display_data)
        delete_btn.bind(on_press=self.delete_account)

        btn_layout.add_widget(logout_btn)
        btn_layout.add_widget(refresh_btn)
        btn_layout.add_widget(delete_btn)

        main_layout.add_widget(btn_layout)
        self.add_widget(main_layout)

    def logout(self, instance):
        App.get_running_app().current_user = None
        self.manager.current = 'login'

    def delete_account(self, instance):
        user_id = App.get_running_app().current_user
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM sensor_data WHERE user_id=?", (user_id,))
        c.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        conn.close()
        App.get_running_app().current_user = None
        show_popup("Deleted", "Your account has been deleted.")
        self.manager.current = 'login'

# Main App
class MyApp(App):
    current_user = None

    def build(self):
        init_db()
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(SignupScreen(name='signup'))
        sm.add_widget(HomeScreen(name='home'))
        return sm

if __name__ == '__main__':
    MyApp().run()
