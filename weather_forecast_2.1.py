import tkinter as tk
from tkinter import ttk, font
import requests
import pandas as pd
from datetime import datetime, timedelta

# OpenWeatherMap API key
API_KEY = 'af2479c82028a6d549704387827d2600'
BASE_URL = 'http://api.openweathermap.org/data/2.5/forecast'

TEMP_DISPLAY_OPTIONS = ["Season", "Summer (High Temps)", "Winter (Low Temps)"]

def get_weather_data(zip_code):
    zip_code = str(zip_code).zfill(5)
    params = {
        'zip': zip_code,
        'appid': API_KEY,
        'units': 'imperial'
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data for zip code {zip_code}: {response.status_code}")
        return None

def extract_high_and_low_temps(weather_data):
    if 'list' not in weather_data:
        return ['N/A'] * 7, ['N/A'] * 7, []

    forecast = weather_data['list']
    daily_highs = {}
    daily_lows = {}

    for entry in forecast:
        date = entry['dt_txt'].split(' ')[0]
        temp_max = entry['main']['temp_max']
        temp_min = entry['main']['temp_min']
        if date not in daily_highs:
            daily_highs[date] = temp_max
            daily_lows[date] = temp_min
        else:
            daily_highs[date] = max(daily_highs[date], temp_max)
            daily_lows[date] = min(daily_lows[date], temp_min)

    sorted_dates = sorted(daily_highs.keys())[:7]
    highs = [daily_highs[date] for date in sorted_dates] + ['N/A'] * (7 - len(sorted_dates))
    lows = [daily_lows[date] for date in sorted_dates] + ['N/A'] * (7 - len(sorted_dates))

    return highs, lows, sorted_dates

def fetch_and_display_weather():
    try:
        names = text_names.get("1.0", tk.END).strip().split('\n')
        zip_codes = text_zip_codes.get("1.0", tk.END).strip().split('\n')

        if not (len(names) == len(zip_codes)):
            result_label.config(text="Input Error: The number of names and ZIP codes must be the same.", fg="red")
            return

        zip_codes = [str(zip_code).zfill(5)[:5] for zip_code in zip_codes]

        temp_display = temp_display_var.get()
        data = []

        for name, zip_code in zip(names, zip_codes):
            weather_data = get_weather_data(zip_code.strip())
            if weather_data:
                highs, lows, dates = extract_high_and_low_temps(weather_data)
                relevant_highs = highs[:7]
                relevant_lows = lows[:7]
                temps = []

                if temp_display == "Summer (High Temps)":
                    # If the user wants only the highs
                    temps = [f"{round(high)}F" if isinstance(high, (int, float)) else "N/A" for high in relevant_highs]
                elif temp_display == "Winter (Low Temps)":
                    # If the user wants only the lows
                    temps = [f"{round(low)}F" if isinstance(low, (int, float)) else "N/A" for low in relevant_lows]
                else:
                    # Season: show LowF - HighF
                    for high, low in zip(relevant_highs, relevant_lows):
                        if isinstance(high, (int, float)) and isinstance(low, (int, float)):
                            temps.append(f"{round(low)}F - {round(high)}F")
                        else:
                            temps.append("N/A")

                data.append([name.strip(), zip_code.strip()] + temps)
            else:
                data.append([name.strip(), zip_code.strip()] + ['N/A'] * 7)

        today = datetime.today()
        day_titles = [(today + timedelta(days=i)).strftime("%A") for i in range(7)]
        columns = ['Name', 'Zip Code'] + day_titles
        results_df = pd.DataFrame(data, columns=columns)

        # Clear existing rows before repopulating
        for item in tree.get_children():
            tree.delete(item)

        tree["columns"] = columns

        for col in columns:
            tree.heading(col, text=col, anchor=tk.CENTER, command=lambda _col=col: sort_column(tree, _col, False))
            tree.column(col, width=100, anchor=tk.CENTER)

        # Insert data into Treeview with highlight logic
        for i, row in results_df.iterrows():
            values = list(row)
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            item_id = tree.insert("", "end", values=values, tags=(tag,))
            
            for j, val in enumerate(values[2:], start=2):
                if "N/A" not in val:
                    if temp_display == "Summer (High Temps)":
                        # Highlight if high is above 98
                        temp = float(val.split("F")[0])
                        if temp > 98:
                            tree.item(item_id, tags=(tag, "highlight_summer"))
                    elif temp_display == "Winter (Low Temps)":
                        # Highlight if low is below 25
                        temp = float(val.split("F")[0])
                        if temp < 25:
                            tree.item(item_id, tags=(tag, "highlight_winter"))
                    elif temp_display == "Season":
                        # Check combined high/low
                        try:
                            low, high = map(lambda x: float(x.split('F')[0]), val.split(' - '))
                            # Highlight if high > 98
                            if high > 98:
                                tree.item(item_id, tags=(tag, "highlight_summer"))
                            # Highlight if low < 25
                            elif low < 25:
                                tree.item(item_id, tags=(tag, "highlight_winter"))
                            # If both conditions meet (low < 25 and high > 98)
                            if low < 25 and high > 98:
                                tree.item(item_id, tags=(tag, "highlight_both"))
                        except ValueError:
                            pass

        result_label.config(text="Weather data has been successfully fetched and displayed.", fg="green")
    except Exception as e:
        result_label.config(text=f"An error occurred: {str(e)}", fg="red")

def remove_selected_rows():
    selected_items = tree.selection()
    for item in selected_items:
        tree.delete(item)

def clear_inputs():
    text_names.delete("1.0", tk.END)
    text_zip_codes.delete("1.0", tk.END)
    result_label.config(text="")
    for item in tree.get_children():
        tree.delete(item)

def sort_column(tree, col, reverse):
    l = [(tree.set(k, col), k) for k in tree.get_children('')]
    l.sort(reverse=reverse)

    for index, (val, k) in enumerate(l):
        tree.move(k, '', index)

    tree.heading(col, command=lambda _col=col: sort_column(tree, _col, not reverse))

root = tk.Tk()
root.title("Jax's Jungle Weather App")
root.configure(bg='#3F5147')

instructions = tk.Label(root, text="Paste Names and ZIP codes in the respective columns:", bg='#3F5147', fg='white', font=('Arial', 12))
instructions.pack(pady=10)

frame = tk.Frame(root, bg='#3F5147')
frame.pack()

bold_font = font.Font(weight="bold")

title_names = tk.Label(frame, text="Names", bg='#3F5147', fg='white', font=bold_font)
title_names.grid(row=0, column=0, padx=5, pady=5)
title_zip_codes = tk.Label(frame, text="ZIP Codes", bg='#3F5147', fg='white', font=bold_font)
title_zip_codes.grid(row=0, column=1, padx=5, pady=5)

text_names = tk.Text(frame, height=15, width=30, borderwidth=2, relief="solid", highlightbackground="black", highlightthickness=1)
text_names.grid(row=1, column=0, padx=5)
text_zip_codes = tk.Text(frame, height=15, width=15, borderwidth=2, relief="solid", highlightbackground="black", highlightthickness=1)
text_zip_codes.grid(row=1, column=1, padx=5)

temp_display_var = tk.StringVar(value=TEMP_DISPLAY_OPTIONS[0])
temp_display_menu = ttk.OptionMenu(frame, temp_display_var, TEMP_DISPLAY_OPTIONS[0], *TEMP_DISPLAY_OPTIONS)
temp_display_menu.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

frame.grid_columnconfigure(0, weight=1)
frame.grid_columnconfigure(1, weight=1)

button_frame = tk.Frame(root, bg='#3F5147')
button_frame.pack(pady=10)

remove_button = tk.Button(button_frame, text="Remove Selected", command=remove_selected_rows, bg='#F1A638', fg='#3F5147', font=('Arial', 12, 'bold'), relief="solid", borderwidth=2)
remove_button.grid(row=0, column=0, padx=10)
remove_button.config(highlightbackground="black", highlightthickness=1)

fetch_button = tk.Button(button_frame, text="Fetch Weather Data", command=fetch_and_display_weather, bg='#F1A638', fg='#3F5147', font=('Arial', 12, 'bold'), relief="solid", borderwidth=2)
fetch_button.grid(row=0, column=1, padx=10)
fetch_button.config(highlightbackground="black", highlightthickness=1)

clear_button = tk.Button(button_frame, text="Clear Inputs", command=clear_inputs, bg='#F1A638', fg='#3F5147', font=('Arial', 12, 'bold'), relief="solid", borderwidth=2)
clear_button.grid(row=0, column=2, padx=10)
clear_button.config(highlightbackground="black", highlightthickness=1)

button_frame.grid_columnconfigure(0, weight=1)
button_frame.grid_columnconfigure(1, weight=1)
button_frame.grid_columnconfigure(2, weight=1)

result_label = tk.Label(root, text="", bg='#3F5147', fg='white', font=('Arial', 12))
result_label.pack(pady=5)

columns = ['Name', 'Zip Code'] + [(datetime.today() + timedelta(days=i)).strftime("%A") for i in range(7)]
tree = ttk.Treeview(root, columns=columns, show='headings', height=20, selectmode="extended")
tree.pack(pady=10)

style = ttk.Style()
style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))

for col in columns:
    tree.heading(col, text=col, command=lambda _col=col: sort_column(tree, _col, False), anchor=tk.CENTER)
    tree.column(col, width=100, anchor=tk.CENTER)

tree.tag_configure("highlight_summer", foreground='#FF0000', font=('Arial', 10, 'bold'))
tree.tag_configure("highlight_winter", foreground='#0492C2', font=('Arial', 10, 'bold'))
tree.tag_configure("highlight_both", foreground='#00A67D', font=('Arial', 10, 'bold'))
tree.tag_configure("evenrow", background='#f0f0f0')
tree.tag_configure("oddrow", background='#ffffff')

root.mainloop()
