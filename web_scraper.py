import requests
from bs4 import BeautifulSoup
import datetime
import re
parent_url = 'https://www.nutritics.com/menu/ma4003'
parent_response = requests.get(parent_url)

def get_most_recent_monday():
    today = datetime.datetime.today()
    # Calculate the most recent Monday
    most_recent_monday = today - datetime.timedelta(days=today.weekday())
    return most_recent_monday
def normalize_whitespace(text):
    return ' '.join(text.split())


most_recent_monday = get_most_recent_monday().strftime("%B %-d")
print(most_recent_monday)

if parent_response.status_code == 200:
    # Get main plate's url tail
    soup1 = BeautifulSoup(parent_response.content, 'html.parser')
    
    prefix = f"Main Plate Lunch & Dinner - {most_recent_monday}"
    normalized_prefix = normalize_whitespace(prefix).lower()
    print(normalized_prefix)
    span = soup1.find("span", class_="title", string=lambda text: text and normalize_whitespace(text).lower().startswith(normalized_prefix))
     
# Extract the parent div and its id from the inner span
    if span:
        parent_div = span.find_parent("div", class_="menu")
        if parent_div:
            div_id = parent_div.get("id")
            print(f"Div ID: {div_id}")
        else:
            print("No parent div with the specified class found.")
    else:
        print("No span with the specified text found.")
else:
    print(f'Failed to retrieve the parent site. Status code: {parent_response.status_code}')
main_menu_id =re.findall("\d+", div_id)[0]
print(main_menu_id) 

# URL of the page to scrape
url = f'https://www.nutritics.com/menu/ma4003/{main_menu_id}'
print(url)
# Get today's date
today = datetime.datetime.now()
# Format the date as DaysofweekMonthDate
formatted_date = today.strftime('%A%B%-d')
print(formatted_date)
#Format the header'date
header_date = today.strftime('%A, %B %d')
# Send a GET request to the URL
response = requests.get(url)


# Check if the request was successful
if response.status_code == 200:
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find and print the title of the page
    title = soup.find('title').get_text()
    lunch_elements = soup.select(
    f'.item.g-{formatted_date}Lunch, '
    f'.item.g-{formatted_date}Brunch, '
    f'.item.g-{formatted_date}Polish'
)
    dinner_elements = soup.select(f'[class^="item g-{formatted_date}Dinner"]')
    print(title)
    base_food_url = "https://www.nutritics.com/images-user/food/168118/430x430x"
    
    def get_food_data(elements):
        food_data = []
        for element in elements:
            data_name = element.get('data-name')
            if "Pizza" in data_name:
                continue 
            data_cals = element.get('data-cals')
            data_carbs = element.get('data-carbs')
            data_proteins = element.get('data-protein')
            data_fat = element.get('data-fat')
            photo_id = element.get('data-fid')
            if data_name:
                photo_url = f"{base_food_url}{photo_id}.jpg"
                food_data.append((data_name, data_cals, data_carbs, data_proteins, data_fat, photo_url))
        return food_data
    
    lunch_data = get_food_data(lunch_elements)
    dinner_data = get_food_data(dinner_elements)

    #Write the scraped data to an html email
    with open('daily_menu.html', 'w') as f:
        f.write(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            @media only screen and (max-width: 600px) {{
                .responsive-img {{
                    width: 100% !important;
                    height: auto !important;
                }}
            }}
        </style>
        
    </head>
    <body>
        <h1 style='background-color: #97002E; padding: 10px; text-align: center; color: #FBAF3F;'>{header_date}</h1>
    """)

        def write_food_data(f, meal_of_day, food_data):
            if food_data:
                f.write(f"<h2>{meal_of_day}</h2>")
                f.write("<table border='1' style='width: 100%;text-align: center; border-collapse: collapse;'>")
                f.write("<tr><th style='width: 30%;'>Name</th><th style='width: 17.5%;'>Image</th><th style='width: 17.5%;'>Carbs (g)</th><th style='width: 17.5%;'>Proteins (g)</th><th style='width: 17.5%;'>Fat (g)</th></tr>")
                for name, cals, carbs, proteins, fat, image_url in food_data:
                    f.write(f"<tr><td><em>{name}</em><br>{cals} calories</td><td><img src='{image_url}' alt='{name}' style='width: 150px; height: 123.5px;' class='responsive-img'></td><td>{carbs}</td><td>{proteins}</td><td>{fat}</td></tr>")
                f.write("</table>")

       
        write_food_data(f, "Lunch", lunch_data)
        write_food_data(f, "Dinner", dinner_data)

        f.write("""<footer style="margin-top: 20px; text-align: center;">
        <table align="center" role="presentation" style="width: 100%; text-align: center;">
            <tr>
                <td>
                    <p style="font-size: 12px; color: #888;">
                        You are receiving this email because you signed up for updates. 
                        <br><a href="{{unsubscribe_url}}" style="color: #888;">Unsubscribe</a> | 
                        <a style="text-decoration: none;" href="https://www.linkedin.com/in/tanphucle/">
                            <img style="width: 12px; height: auto; margin-bottom: -3px;" 
                            src="https://cdn-icons-png.flaticon.com/512/174/174857.png" alt="LinkedIn"> 
                            <span style="color: #888; text-decoration: underline;">Connect with me</span>
                        </a>
                    </p>
                </td>
            </tr>
        </table>
    </footer>""")
        f.write("</body></html>")
else:
    print(f'Failed to retrieve the page. Status code: {response.status_code}')
    