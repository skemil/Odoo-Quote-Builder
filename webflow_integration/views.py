from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import xmlrpc.client
import os


def show_index(request):
    # This function renders the index.html page
    return render(request, 'index.html')

# Connect to the Odoo server
url = os.getenv('URL')
db = os.getenv('DB')
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

# Get the list of products by ID
producten = models.execute_kw(db, uid, password, 'product.template', 'search', [[]])
producten.sort()

get_product = models.execute_kw(db, uid, password, 'product.template', 'read', [producten], {'fields': ['barcode']})
customers = models.execute_kw(db, uid, password, 'res.partner', 'search_read', [[]], {'fields': ['id', 'email']})

products = {}
customers_dict = {}

for i in get_product:
    # Add the product to the dictionary with the barcode as the key and Id as the value
    products[i['barcode']] = i['id']
print(products)

for i in range(len(customers)):
    buffer = customers[i]
    customers_dict[buffer['email']] = buffer['id']

# Create function to create a new customer if the email is not in the dictionary, name, surname, email and phone number are required and return id of the new customer or the id of the existing customer, make company optional
def create_customer(name, email, phone):
    if email in customers_dict:
        return customers_dict[email]
    else:
        new_customer = models.execute_kw(db, uid, password, 'res.partner', 'create', [{'name': name, 'email': email, 'phone': phone}])
        customers_dict[email] = new_customer
        return new_customer


@csrf_exempt  # Consider CSRF protection for production
def process_form(request):
    if request.method == 'POST':
        # Accessing form data
        voornaam = request.POST.get('voornaam')
        email = request.POST.get('email').lower()  # Adjust the name attribute based on your actual form
        telefoonnummer = request.POST.get('input16')  # Adjust the name attribute based on your actual form
        bedrijf = request.POST.get('naam-2')  # Adjust the name attribute based on your actual form
        
        # Iterate over the keys in the products dictionary and also the product quantities from the form data, create a dictionary with ID as the key and the quantity as the value
        product_quantities = {}
        for barcode, product_id in products.items():
            quantity = request.POST.get(barcode)
            if quantity:
                product_quantities[product_id] = quantity
        
        # If quantinties are not empty, create a new customer and a new sale order
        if product_quantities:
            customer_id = create_customer(voornaam, email, telefoonnummer)
            sale_order = models.execute_kw(db, uid, password, 'sale.order', 'create', [{'partner_id': customer_id}])
            for product_id, quantity in product_quantities.items():
                models.execute_kw(db, uid, password, 'sale.order.line', 'create', [{'order_id': sale_order, 'product_id': product_id, 'product_uom_qty': quantity}])

        
        # After processing the form, redirect to the home page or a 'thank you' page
        return redirect('show_index')  # Assumes you have a URL named 'show_index'
    else:
        # If it's not a POST request, just show the form again
        return render(request, 'index.html')