import requests

def currency(curr):
    url = "https://api.exchangerate-api.com/v4/latest/"
    response = requests.get(url + f"{curr}")
    res = response.json()
    indian_val = res['rates'].get('INR', None)

    return indian_val

currency_name=str(input("Enter a Currency:"))
amt=currency(currency_name)
print(amt)