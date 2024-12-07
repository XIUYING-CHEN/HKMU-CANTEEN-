import datetime
import qrcode
import urllib.parse
from PIL import Image

class MenuItem:
    def __init__(self, order_packet, name, price, stock, noodle_types=None, noodle_costs=None, drink_options=None, drink_costs=None):
        self.order_packet = order_packet
        self.name = name
        self.price = price
        self.stock = stock
        self.noodle_types = noodle_types.split(';') if noodle_types else []
        self.noodle_costs = [float(cost) for cost in noodle_costs.split(';')] if noodle_costs else []
        self.drink_options = drink_options.split(';') if drink_options else []
        self.drink_costs = [float(cost) for cost in drink_costs.split(';')] if drink_costs else []

    def sell_item(self):
        if self.stock > 0:
            self.stock -= 1
        else:
            raise Exception(f"{self.name} is sold out!")

    def __str__(self):
        return f"{self.name} - ${self.price:.2f} (Stock: {self.stock})"

def load_menu_from_txt(file_path):
    menu = []
    with open(file_path, 'r') as file_variable:
        lines = file_variable.readlines()
    
    headers = lines[0].strip().split(',')
    for line in lines[1:]:  # Skip the header line
        values = line.strip().split(',')
        if len(values) < len(headers):
            # Ensure all headers have corresponding values
            values.extend([''] * (len(headers) - len(values)))
        menu_item_data = dict(zip(headers, values))
    
        # Extracting data from the dictionary
        order_packet = menu_item_data['order packet']
        name = menu_item_data['name']
        price = float(menu_item_data['price']) if menu_item_data['price'] else 0.0  # Default price to 0.0 if empty
        stock = int(menu_item_data['stock']) if menu_item_data['stock'] else 0  # Default stock to 0 if empty
        noodle_types = menu_item_data.get('noodle type', '')
        noodle_costs = menu_item_data.get('noodle cost', '')
        drink_options = menu_item_data.get('drink option', '')
        drink_costs = menu_item_data.get('drink cost', '')
        
        # Creating a MenuItem instance and adding it to the menu list
        menu.append(MenuItem(order_packet, name, price, stock, noodle_types, noodle_costs, drink_options, drink_costs))
    
    return menu

def display_menu(menu):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n--- Menu --- (Current Time: {current_time})")
    for index, item in enumerate(menu):
        stock_status = "Sold Out" if item.stock == 0 else f"In Stock: {item.stock}"
        print(f"{index + 1}. {item.order_packet} - {item.name} - ${item.price:.2f} ({stock_status})")
        if item.noodle_types:
            noodle_details = ", ".join([f"{type_} (${cost:.2f})" for type_, cost in zip(item.noodle_types, item.noodle_costs)])
            print(f"   Noodle Types: {noodle_details}")
        if item.drink_options:
            drink_details = ", ".join([f"{option} (${cost:.2f})" for option, cost in zip(item.drink_options, item.drink_costs)])
            print(f"   Drink Options: {drink_details}")

def display_menu_names(menu):
    print("\n--- Menu ---")
    for index, item in enumerate(menu):
        print(f"{index + 1}. {item.name}")

class Order:
    order_counter = 1

    def __init__(self, discount, takeaway_cost, takeaway_option):
        self.items = []
        self.order_number = Order.order_counter
        Order.order_counter += 1
        self.order_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.discount = discount
        self.takeaway_cost = takeaway_cost
        self.takeaway_option = takeaway_option
        self.payment_option = None

    def add_item(self, item, noodle_choice=None, drink_choice=None):
        item_price = item.price
        if noodle_choice:
            item_price += item.noodle_costs[item.noodle_types.index(noodle_choice)]
        if drink_choice:
            item_price += item.drink_costs[item.drink_options.index(drink_choice)]
        self.items.append((self.order_number, item, noodle_choice, drink_choice, item_price))
        item.sell_item()
        self.order_number += 1

    def get_total(self):
        total = sum(item[4] for item in self.items)
        total = total * self.discount + self.takeaway_cost  # Apply discount and add takeaway cost
        return total

    def display_order(self):
        print(f"\n--- Order Summary --- (Order Time: {self.order_time})")
        for order_number, item, noodle_choice, drink_choice, item_price in self.items:
            print(f"Order No. {order_number}: {item}")
            if noodle_choice:
                print(f"   Noodle Type: {noodle_choice}")
            if drink_choice:
                print(f"   Drink Option: {drink_choice}")
        print(f"Total (after discount and takeaway cost): ${self.get_total():.2f}")

    def display_final_summary(self):
        print("HKMU canteen")
        print("(online order)")
        print(f"Option: {self.takeaway_option}")
        print("When your order is ready to collect, please show out your order no. to the collection centre.")
        print(f"Order Time: {self.order_time}")
        for order_number, item, noodle_choice, drink_choice, item_price in self.items:
            print(f"Order No. {order_number}:")
            print(f"   {item.name} - ${item.price:.2f}")
            if noodle_choice:
                print(f"   Noodle Type: {noodle_choice} - ${item.noodle_costs[item.noodle_types.index(noodle_choice)]:.2f}")
            if drink_choice:
                print(f"   Drink Option: {drink_choice} - ${item.drink_costs[item.drink_options.index(drink_choice)]:.2f}")
        print(f"Discount: {self.discount * 100}%")
        if self.takeaway_cost > 0:
            print(f"Additional cost for takeaway: ${self.takeaway_cost:.2f}")
        print(f"Total cost (after discount and takeaway cost): ${self.get_total():.2f}")
        print(f"Payment option: {self.payment_option}")

    def generate_order_qr_code(self, base_url="http://example.com/order", file_path="order_qrcode.png"):
        query_params = {
            "order_number": self.order_number,
            "time": self.order_time,
            "total": self.get_total(),
            "takeaway_option": self.takeaway_option,
            "payment_option": self.payment_option
        }
        # Add items to query parameters
        for i, (order_number, item, noodle_choice, drink_choice, item_price) in enumerate(self.items):
            query_params[f"item_{i}_name"] = item.name
            query_params[f"item_{i}_price"] = item.price
            if noodle_choice:
                query_params[f"item_{i}_noodle_choice"] = noodle_choice
            if drink_choice:
                query_params[f"item_{i}_drink_choice"] = drink_choice

        # Encode the query parameters
        query_string = urllib.parse.urlencode(query_params)
        order_url = f"{base_url}?{query_string}"

        # Generate the QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(order_url)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        img.save(file_path)
        img.show()

def generate_qr_code(data, file_path="qrcode.png"):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    img.save(file_path)
    img.show()

def main():
    print("Welcome to HKMU canteen.")
    
    # Generate QR code for ordering food
    order_url = "http://example.com/order"
    generate_qr_code(order_url, "order_qrcode.png")

    # Load menu from a text file
    file_path = r"C:\Users\Adeline\Desktop\python individual project\project code\menu.txt"
    menu = load_menu_from_txt(file_path)

    all_orders = []

    while True:
        # Determine discount
        while True:
            user_type = input("Are you a student or school staff? (yes/no): ").strip().lower()
            if user_type == 'yes':
                discount = 0.8  # 20% discount
                break
            elif user_type == 'no':
                discount = 1.0  # No discount
                break
            else:
                print("You entered an invalid type. Please enter 'yes' or 'no'.")

        # Determine takeaway cost
        while True:
            takeaway = input("Is this order for eat in or take away? (eat in/take away+$3): ").strip().lower()
            if takeaway == 'eat in':
                takeaway_cost = 0
                takeaway_option = "Eat in"
                break
            elif takeaway == 'take away':
                takeaway_cost = 3
                takeaway_option = "Take away"
                print("Additional $3 will be added for take away.")
                break
            else:
                print("You entered an invalid type. Please enter 'eat in' or 'take away+$3'.")

        order = Order(discount, takeaway_cost, takeaway_option)

        while True:
            display_menu_names(menu)
            packet_number = input("Enter the number of the order packet to order (or 'q' to finish): ")
            if packet_number.lower() == 'q':
                break
            try:
                packet_index = int(packet_number) - 1
                if 0 <= packet_index < len(menu):
                    item = menu[packet_index]
                    if item.stock == 0:
                        print(f"{item.name} is sold out. Please choose another item.")
                        continue
                    noodle_choice = None
                    drink_choice = None
                    if item.noodle_types:
                        while True:
                            print("Available noodle types:")
                            for i, noodle in enumerate(item.noodle_types):
                                print(f"{i + 1}. {noodle} (${item.noodle_costs[i]:.2f})")
                            noodle_choice_index = input("Choose a noodle type (enter the number between 1 and 4): ")
                            try:
                                noodle_choice_index = int(noodle_choice_index) - 1
                                if 0 <= noodle_choice_index < len(item.noodle_types):
                                    noodle_choice = item.noodle_types[noodle_choice_index]
                                    break
                                else:
                                    print("Invalid choice. Please enter a number between 1 and 4.")
                            except ValueError:
                                print("Invalid input. Please enter a number between 1 and 4.")
                    if item.drink_options:
                        while True:
                            print("Available drink options:")
                            for i, drink in enumerate(item.drink_options):
                                print(f"{i + 1}. {drink} (${item.drink_costs[i]:.2f})")
                            drink_choice_index = input("Choose a drink option (enter the number between 1 and 4): ")
                            try:
                                drink_choice_index = int(drink_choice_index) - 1
                                if 0 <= drink_choice_index < len(item.drink_options):
                                    drink_choice = item.drink_options[drink_choice_index]
                                    break
                                else:
                                    print("Invalid choice. Please enter a number between 1 and 4.")
                            except ValueError:
                                print("Invalid input. Please enter a number between 1 and 4.")
                    try:
                        order.add_item(item, noodle_choice, drink_choice)
                    except Exception as e:
                        print(e)
                else:
                    print("Invalid packet number. Please enter a number between 1 and 5.")
            except ValueError:
                print("Please enter a valid number between 1 and 5.")

        order.display_order()
        all_orders.append(order)

        # Payment options
        while True:
            print("\n--- Payment Options ---")
            print("1. Alipay")
            print("2. WeChat")
            print("3. Octopus")
            payment_option = input("Choose a payment option (enter the number between 1 and 3): ")
            if payment_option == '1':
                order.payment_option = "Alipay"
                print("Payment made using Alipay.")
                break
            elif payment_option == '2':
                order.payment_option = "WeChat"
                print("Payment made using WeChat.")
                break
            elif payment_option == '3':
                order.payment_option = "Octopus"
                print("Payment made using Octopus.")
                break
            else:
                print("Invalid payment option. Please enter a number between 1 and 3.")

        while True:
            another_order = input("Do you want to place another order? (yes/no): ").strip().lower()
            if another_order == 'yes':
                break
            elif another_order == 'no':
                print("\n--- Final Order Summary ---")
                for order in all_orders:
                    order.display_final_summary()
                    order.generate_order_qr_code(f"order_{order.order_number}.png")
                return
            else:
                print("You entered an invalid type. Please enter 'yes' or 'no'.")

if __name__ == "__main__":
    main()