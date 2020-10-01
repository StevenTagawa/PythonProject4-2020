"""This is the main module for the Store Inventory project."""
from collections import OrderedDict
import csv
import datetime
import os
import re
import sys

from peewee import *

# Global database variable
db = SqliteDatabase("inventory.db")


class Product(Model):
    """Peewee model for the contents of the database file."""
    product_id = PrimaryKeyField()
    product_name = CharField(max_length=255, unique=True)
    product_quantity = IntegerField(default=0)
    product_price = IntegerField(default=0)
    date_updated = DateField(default=datetime.date.today)

    class Meta:
        database = db


class Inventory:
    """The store inventory object."""
    def __init__(self):
        self.menu_options = OrderedDict([
            ("V", self._view_product),
            ("A", self._add_product),
            ("B", self._backup),
            ("Q", self._quit)
        ])
        self.products = []

    def go(self):
        self.clear()
        self._welcome()
        self._init_db()
        self._load_csv()
        self._convert_csv()
        self._save_csv()
        self._main_loop()

    @staticmethod
    def _init_db():
        """Initializes the database file."""
        db.connect()
        db.create_tables([Product], safe=True)
        db.close()

    def _load_csv(self):
        """Loads data from the csv file."""
        print("Working...")
        with open("inventory.csv", newline="") as csvfile:
            self.products = list(csv.DictReader(csvfile))

    def _convert_csv(self):
        """Converts strings from the csv file to appropriate data types."""
        for product in self.products:
            product["product_price"] = (
                int(float(re.search(r"\d+.?\d{0,2}",
                    product["product_price"]).group()) * 100)
            )
            product["product_quantity"] = int(product["product_quantity"])
            product["date_updated"] = (
                datetime.datetime.strptime(
                    product["date_updated"], "%m/%d/%Y").date())

    def _save_csv(self):
        """Saves the data from the csv file to the database file."""
        count = 0
        for product in self.products:
            new = Product()
            new.product_name = product["product_name"]
            new.product_quantity = product["product_quantity"]
            new.product_price = product["product_price"]
            new.date_updated = product["date_updated"]
            try:
                new.save()
                count += 1
            except IntegrityError:
                self._update_latest(new)
        self.products = []
        print(f"Database created.  {count} items added.")
        self._wait()

    def _update_latest(self, new, verbose=False):
        """Compares duplicate records and saves the newer record."""
        if verbose:
            print(f"{new.product_name} already exists.")
        existing = Product.get(Product.product_name == new.product_name)
        if existing.date_updated < new.date_updated:
            existing.product_quantity = new.product_quantity
            existing.product_price = new.product_price
            existing.date_updated = new.date_updated
            existing.save()
            if verbose:
                print(f"{new.product_name} updated.")
        if verbose:
            self._wait()

    def _main_loop(self):
        """The main execution loop.  Runs until the user quits."""
        self.menu = self.Menu(self)
        while True:
            self.menu.go()
            self.menu.action()

    @staticmethod
    def _welcome():
        """Prints a welcome message."""
        print("=" * 40)
        print("Welcome to the Store Inventory Tool")
        print("\nA Treehouse Python Techdegree Project")
        print("\nby Steven Tagawa")
        print("=" * 40)

    @staticmethod
    def clear():
        """Clears the screen (sometimes)."""
        # For terminal emulators that do not recognize the system call, print
        # five blank lines as a cue that the screen should clear.  (On terminals
        # that do recognize "cls" or "clear", this will not be noticeable.)
        print("\n"*5)
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def _goodbye():
        """Prints a goodbye message."""
        print("\n" + "=" * 40)
        print("Thanks for using the Store Inventory Tool!\n"
              "See you again soon!")
        print("=" * 40 + "\n")

    def _view_product(self):
        """Displays a single product, located by ID number."""
        product = None  # Dummy assignment to squash a PyCharm complaint.
        while True:
            response = input(
                "\nPlease enter a product ID, or 'Q' to return to the menu:  ")
            if response == "":
                confirm = input("You didn't enter a product ID.  Do you want "
                                "to return to the main menu? [Y/N]  ")
                if confirm.upper() == "Y":
                    return
                else:
                    continue
            if response.upper() == "Q":
                return
            try:
                response = int(response)
            except ValueError:
                print("\nSorry, the product ID must be a number.  Please try "
                      "again.")
                continue
            try:
                product = Product.get(Product.product_id == response)
                break
            except DoesNotExist:
                print("\nNo product with that ID number was found.  Please try "
                      "again.")
        print(product.product_name)
        print(f"Quantity:  {product.product_quantity}")
        print(f"Price:  ${product.product_price/100}")
        print(f"Updated:  {product.date_updated.strftime('%m/%d/%Y')}\n")
        self._wait()

    def _add_product(self):
        """Adds a product to the database, or updates a product."""
        new = self._get_product_info()
        if new:
            if self._confirm():
                self._save_product(new)

    @staticmethod
    def _get_product_info():
        """Gathers the specifications for a new product."""
        new = Product()
        print("\nPlease enter the product name, quantity and price below.")
        print("Enter 'Q' to return to the menu.\n")
        while True:
            new.product_name = input("Product name:  ")
            if new.product_name.upper() == "Q":
                return None
            elif new.product_name == "":
                confirm = input("You did not enter a product name.  Do you want"
                                " to return to the menu? [Y/N]  ")
                if confirm.upper() == "Y":
                    return
            else:
                break
        while True:
            new.product_quantity = input("Quantity:  ")
            if new.product_quantity.upper() == "Q":
                return None
            try:
                new.product_quantity = int(new.product_quantity)
                break
            except ValueError:
                print("Sorry, the quantity must be a number.  Please try again,"
                      " or enter 'Q' to return to the menu.")
        while True:
            new.product_price = input("Price:  $")
            if new.product_price.upper() == "Q":
                return None
            try:
                new.product_price = int(float(new.product_price) * 100)
                break
            except ValueError:
                print("Sorry, the price must be in dollars and cents.  Please "
                      "try again, or enter 'Q' to return to the main menu.")
        new.date_updated = datetime.datetime.now().date()
        return new

    @staticmethod
    def _confirm():
        """Asks the user for confirmation before saving a new product."""
        while True:
            response = input("\nSave this product? [Y/N]  ")
            if response.upper() == "Y":
                return True
            elif response.upper() == "N":
                return False
            else:
                print("Sorry, you must enter 'Y' or 'N'.  Please try again.")

    def _save_product(self, new):
        """Saves a new product to the database, or updates a product."""
        try:
            new.save()
            print(f"\n{new.product_name} saved to database.  "
                  f"ID: {new.product_id}")
            self._wait()
        except IntegrityError:
            self._update_latest(new, verbose=True)

    def _backup(self):
        """Creates a csv backup file for the database."""
        self._load_db()
        self._convert_db()
        self._save_db()

    def _load_db(self):
        """Loads data from the database file."""
        products = Product.select()
        for product in products:
            self.products.append(
                {"product_name": product.product_name,
                 "product_quantity": product.product_quantity,
                 "product_price": product.product_price,
                 "date_updated": product.date_updated}
            )

    def _convert_db(self):
        """Converts data types from the database to strings."""
        for product in self.products:
            product["product_price"] = f"${product['product_price']/100}"
            product["product_quantity"] = str(product["product_quantity"])
            product["date_updated"] = datetime.datetime.strftime(
                product["date_updated"], "%m/%d/%Y"
            )

    def _save_db(self):
        """Saves the database data to a csv file."""
        with open("backup.csv", "w", newline="") as csvfile:
            fieldnames = [
                "product_name",
                "product_price",
                "product_quantity",
                "date_updated"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for product in self.products:
                writer.writerow(product)
        print("Backup file created.")
        self._wait()

    def _quit(self):
        self._goodbye()
        sys.exit()

    @staticmethod
    def _wait():
        input("Press ENTER to continue...")

    class Menu:
        """The menu object for the Inventory class."""
        def __init__(self, inv):
            self.inv = inv
            self.action = None

        def go(self):
            """Shows the menu and returns an action to do."""
            self.inv.clear()
            while True:
                self._show()
                response = self._get()
                if response:
                    self.action = self.inv.menu_options[response]
                    return
                print("Sorry, that isn't a valid choice.  Please try again.\n")

        @staticmethod
        def _show():
            print("=" * 40)
            print("INVENTORY MENU\n")
            print("V)  View a product by ID number")
            print("A)  Add a new product")
            print("B)  Back up the inventory database")
            print("Q)  Quit\n")

        def _get(self):
            response = input("Please make a selection:  ").upper()
            if self._valid(response):
                return response
            return None

        def _valid(self, response):
            if response in self.inv.menu_options:
                return True
            return False


# EXECUTION BEGINS HERE
if __name__ == "__main__":
    try:
        inventory = Inventory()
        inventory.go()
    except KeyboardInterrupt:
        print("\nScript halted by user.")
# EXECUTION ENDS HERE
