"""
Library Management System

A desktop-based library management application built with Python and Tkinter.

Features:
- Book management
- Member management
- Borrow and return system
- Search functionality
- Late fee calculation
- JSON data persistence

Author: Sina
"""

import json
import os
import datetime
import tkinter as tk

from tkinter import ttk, messagebox
from typing import List, Dict, Optional


# Constants
DATA_FILE = "library_data.json"
MAX_BORROW_LIMIT = 5
DEFAULT_BORROW_DAYS = 14
DAILY_LATE_FEE = 500


class Book:
    """
    Represents a library book.
    """

    def __init__(
        self,
        isbn: str,
        title: str,
        author: str,
        year: str,
        copies: int = 1
    ):
        self.isbn = isbn.strip()
        self.title = title.strip()
        self.author = author.strip()
        self.year = year.strip()

        self.total_copies = copies
        self.borrowed_copies = 0

    @property
    def available_copies(self) -> int:
        return self.total_copies - self.borrowed_copies

    def borrow(self) -> None:
        """
        Borrow one copy of the book.
        """

        if self.available_copies <= 0:
            raise ValueError("No available copies.")

        self.borrowed_copies += 1

    def return_copy(self) -> None:
        """
        Return one borrowed copy.
        """

        if self.borrowed_copies <= 0:
            raise ValueError(
                "No borrowed copies exist."
            )

        self.borrowed_copies -= 1

    def add_copy(self) -> None:
        """
        Add a new physical copy.
        """

        self.total_copies += 1

    def to_dict(self) -> Dict:
        return {
            "isbn": self.isbn,
            "title": self.title,
            "author": self.author,
            "year": self.year,
            "copies": self.total_copies,
            "borrowed": self.borrowed_copies
        }


    @classmethod
    def from_dict(cls, data: Dict):
        book = cls(
            data["isbn"],
            data["title"],
            data["author"],
            data["year"],
            data["copies"]
        )

        book.borrowed_copies = data.get(
            "borrowed",
            0
        )

        return book

class Member:
    """
    Represents a library member.
    """

    def __init__(
        self,
        member_id: str,
        name: str,
        phone: str
    ):
        self.member_id = member_id.strip()
        self.name = name.strip()
        self.phone = phone.strip()

        self.borrowed_isbns: List[str] = []

    def borrow_book(
        self,
        isbn: str
    ) -> None:

        if len(self.borrowed_isbns) >= MAX_BORROW_LIMIT:
            raise ValueError(
                "Member reached maximum borrow limit."
            )

        if isbn in self.borrowed_isbns:
            raise ValueError(
                "Book already borrowed by this member."
            )

        self.borrowed_isbns.append(isbn)

    def return_book(
        self,
        isbn: str
    ) -> None:

        if isbn not in self.borrowed_isbns:
            raise ValueError(
                "Book was not borrowed by this member."
            )

        self.borrowed_isbns.remove(isbn)

    def to_dict(self) -> Dict:
        return {
            "member_id": self.member_id,
            "name": self.name,
            "phone": self.phone,
            "borrowed_books": self.borrowed_isbns
        }


    @classmethod
    def from_dict(cls, data: Dict):

        member = cls(
            data["member_id"],
            data["name"],
            data["phone"]
        )

        member.borrowed_isbns = data.get(
            "borrowed_books",
            []
        )
        return member

class Library:
    """
    Main library management system.

    Handles:
    - Books
    - Members
    - Borrow transactions
    - Data persistence
    """

    def __init__(self, data_file: str = DATA_FILE):

        self.books: Dict[str, Book] = {}
        self.members: Dict[str, Member] = {}
        self.transactions: List[Dict] = []

        self.data_file = data_file

        self.load_data()

    # -------------------------
    # Book Management
    # -------------------------

    def add_book(
        self,
        isbn: str,
        title: str,
        author: str,
        year: str,
        copies: int = 1
    ) -> None:

        if isbn in self.books:

            self.books[isbn].total_copies += copies

        else:

            self.books[isbn] = Book(
                isbn,
                title,
                author,
                year,
                copies
            )

        self.save_data()

    def remove_book(
        self,
        isbn: str
    ) -> None:

        if isbn not in self.books:
            raise ValueError(
                "Book not found."
            )

        if self.books[isbn].borrowed_copies > 0:
            raise ValueError(
                "Cannot remove borrowed book."
            )

        del self.books[isbn]

        self.save_data()



    def search_books(
        self,
        query: str
    ) -> List[Book]:

        query = query.lower()

        return [
            book
            for book in self.books.values()
            if (
                query in book.title.lower()
                or query in book.author.lower()
                or query in book.isbn.lower()
            )
        ]



    def get_book(
        self,
        isbn: str
    ) -> Optional[Book]:

        return self.books.get(isbn)

    def get_all_books(self) -> List[Book]:

        return list(self.books.values())

    # -------------------------
    # Member Management
    # -------------------------

    def add_member(
        self,
        member_id: str,
        name: str,
        phone: str
    ) -> None:

        if member_id in self.members:
            raise ValueError(
                "Member ID already exists."
            )

        self.members[member_id] = Member(
            member_id,
            name,
            phone
        )

        self.save_data()

    def remove_member(
        self,
        member_id: str
    ) -> None:

        if member_id not in self.members:
            raise ValueError(
                "Member not found."
            )

        member = self.members[member_id]

        if member.borrowed_isbns:
            raise ValueError(
                "Member has borrowed books."
            )

        del self.members[member_id]

        self.save_data()

    def get_member(
        self,
        member_id: str
    ) -> Optional[Member]:

        return self.members.get(member_id)

    def get_all_members(self) -> List[Member]:

        return list(self.members.values())

    # -------------------------
    # Borrow / Return System
    # -------------------------

    def borrow_book(
        self,
        member_id: str,
        isbn: str,
        days: int = DEFAULT_BORROW_DAYS
    ) -> None:

        member = self.get_member(member_id)

        if member is None:
            raise ValueError(
                "Member not found."
            )

        book = self.get_book(isbn)

        if book is None:
            raise ValueError(
                "Book not found."
            )

        book.borrow()

        member.borrow_book(isbn)

        today = datetime.date.today()

        due_date = (
            today +
            datetime.timedelta(days=days)
        )

        self.transactions.append(
            {
                "type": "borrow",
                "member_id": member_id,
                "isbn": isbn,
                "date": str(today),
                "due_date": str(due_date)
            }
        )

        self.save_data()

    def return_book(
        self,
        member_id: str,
        isbn: str
    ) -> int:

        member = self.get_member(member_id)

        if member is None:
            raise ValueError(
                "Member not found."
            )

        book = self.get_book(isbn)

        if book is None:
            raise ValueError(
                "Book not found."
            )

        due_date = None

        for transaction in self.transactions:

            if (
                transaction["type"] == "borrow"
                and transaction["member_id"] == member_id
                and transaction["isbn"] == isbn
            ):

                due_date = datetime.date.fromisoformat(
                    transaction["due_date"]
                )

                break

        if due_date is None:

            raise ValueError(
                "Borrow history not found."
            )

        today = datetime.date.today()

        penalty = 0


        if today > due_date:

            late_days = (
                today - due_date
            ).days

            penalty = late_days * DAILY_LATE_FEE

        book.return_copy()

        member.return_book(isbn)

        self.transactions.append(
            {
                "type": "return",
                "member_id": member_id,
                "isbn": isbn,
                "date": str(today),
                "penalty": penalty
            }
        )

        self.save_data()

        return penalty

    def get_borrowed_books(self) -> List[Dict]:

        result = []


        for member in self.members.values():

            for isbn in member.borrowed_isbns:

                book = self.get_book(isbn)

                if book:

                    result.append(
                        {
                            "member_id": member.member_id,
                            "member_name": member.name,
                            "isbn": isbn,
                            "title": book.title
                        }
                    )


        return result

    # -------------------------
    # Data Storage
    # -------------------------

    def save_data(self) -> None:

        data = {

            "books":
                [
                    book.to_dict()
                    for book in self.books.values()
                ],


            "members":
                [
                    member.to_dict()
                    for member in self.members.values()
                ],


            "transactions":
                self.transactions

        }

        with open(
            self.data_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

    def load_data(self) -> None:

        if not os.path.exists(
            self.data_file
        ):
            return

        try:

            with open(
                self.data_file,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            for book_data in data.get(
                "books",
                []
            ):

                book = Book.from_dict(
                    book_data
                )

                self.books[book.isbn] = book

            for member_data in data.get(
                "members",
                []
            ):

                member = Member.from_dict(
                    member_data
                )

                self.members[member.member_id] = member

            self.transactions = data.get(
                "transactions",
                []
            )

        except Exception:
            self.books = {}
            self.members = {}
            self.transactions = []

class LibraryGUI:
    """
    Tkinter graphical interface for the library system.
    """

    def __init__(self, root: tk.Tk):

        self.root = root

        self.root.title(
            "Library Management System"
        )

        self.root.geometry(
            "950x700"
        )

        self.library = Library()

        self.create_widgets()

        self.refresh_books()

        self.refresh_members()

        self.refresh_borrowed()

    # =========================
    # GUI Creation
    # =========================

    def create_widgets(self):

        self.notebook = ttk.Notebook(
            self.root
        )

        self.notebook.pack(
            fill=tk.BOTH,
            expand=True,
            padx=10,
            pady=10
        )

        self.create_book_tab()

        self.create_member_tab()

        self.create_borrow_tab()

    # =========================
    # Book Tab
    # =========================

    def create_book_tab(self):

        self.book_tab = tk.Frame(
            self.notebook
        )

        self.notebook.add(
            self.book_tab,
            text="Books"
        )

        form = tk.Frame(
            self.book_tab
        )

        form.pack(
            pady=10
        )

        labels = [
            "ISBN",
            "Title",
            "Author",
            "Year",
            "Copies"
        ]

        self.book_entries = {}

        for index, label in enumerate(labels):

            tk.Label(
                form,
                text=label
            ).grid(
                row=index,
                column=0,
                padx=5,
                pady=5
            )

            entry = tk.Entry(
                form
            )

            entry.grid(
                row=index,
                column=1
            )

            self.book_entries[label] = entry

        tk.Button(
            form,
            text="Add Book",
            command=self.add_book
        ).grid(
            row=5,
            column=0,
            columnspan=2,
            pady=10
        )

        self.book_tree = ttk.Treeview(
            self.book_tab,
            columns=(
                "isbn",
                "title",
                "author",
                "available"
            ),
            show="headings"
        )

        for column in self.book_tree["columns"]:

            self.book_tree.heading(
                column,
                text=column.title()
            )

        self.book_tree.pack(
            fill=tk.BOTH,
            expand=True
        )

        tk.Button(
            self.book_tab,
            text="Delete Selected Book",
            command=self.delete_book
        ).pack(
            pady=5
        )

    def add_book(self):

        try:

            data = {
                key:
                value.get()
                for key, value
                in self.book_entries.items()
            }

            self.library.add_book(
                data["ISBN"],
                data["Title"],
                data["Author"],
                data["Year"],
                int(data["Copies"])
            )

            messagebox.showinfo(
                "Success",
                "Book added successfully."
            )

            self.refresh_books()

        except Exception as error:

            messagebox.showerror(
                "Error",
                str(error)
            )

    def refresh_books(self):

        if not hasattr(
            self,
            "book_tree"
        ):
            return

        for item in self.book_tree.get_children():

            self.book_tree.delete(
                item
            )

        for book in self.library.get_all_books():

            self.book_tree.insert(
                "",
                tk.END,
                values=(
                    book.isbn,
                    book.title,
                    book.author,
                    book.available_copies
                )
            )

    def delete_book(self):

        selected = (
            self.book_tree.selection()
        )

        if not selected:
            return

        isbn = self.book_tree.item(
            selected[0]
        )["values"][0]

        try:

            self.library.remove_book(
                isbn
            )

            self.refresh_books()

        except Exception as error:

            messagebox.showerror(
                "Error",
                str(error)
            )

    # =========================
    # Member Tab
    # =========================

    def create_member_tab(self):

        self.member_tab = tk.Frame(
            self.notebook
        )

        self.notebook.add(
            self.member_tab,
            text="Members"
        )

        form = tk.Frame(
            self.member_tab
        )

        form.pack(
            pady=10
        )

        self.member_entries = {}

        for index, label in enumerate(
            [
                "Member ID",
                "Name",
                "Phone"
            ]
        ):

            tk.Label(
                form,
                text=label
            ).grid(
                row=index,
                column=0
            )

            entry = tk.Entry(
                form
            )

            entry.grid(
                row=index,
                column=1
            )
            self.member_entries[label] = entry

        tk.Button(
            form,
            text="Add Member",
            command=self.add_member
        ).grid(
            row=3,
            column=0,
            columnspan=2
        )

        self.member_tree = ttk.Treeview(
            self.member_tab,
            columns=(
                "id",
                "name",
                "phone"
            ),
            show="headings"
        )

        for column in self.member_tree["columns"]:

            self.member_tree.heading(
                column,
                text=column.title()
            )

        self.member_tree.pack(
            fill=tk.BOTH,
            expand=True
        )

    def add_member(self):

        try:

            self.library.add_member(
                self.member_entries["Member ID"].get(),
                self.member_entries["Name"].get(),
                self.member_entries["Phone"].get()
            )

            self.refresh_members()

        except Exception as error:

            messagebox.showerror(
                "Error",
                str(error)
            )

    def refresh_members(self):

        if not hasattr(
            self,
            "member_tree"
        ):
            return

        for item in self.member_tree.get_children():

            self.member_tree.delete(
                item
            )

        for member in self.library.get_all_members():

            self.member_tree.insert(
                "",
                tk.END,
                values=(
                    member.member_id,
                    member.name,
                    member.phone
                )
            )

    # =========================
    # Borrow Tab
    # =========================

    def create_borrow_tab(self):

        self.borrow_tab = tk.Frame(
            self.notebook
        )

        self.notebook.add(
            self.borrow_tab,
            text="Borrow / Return"
        )

        form = tk.Frame(
            self.borrow_tab
        )

        form.pack(
            pady=10
        )

        self.member_id_entry = tk.Entry(
            form
        )

        self.book_isbn_entry = tk.Entry(
            form
        )

        tk.Label(
            form,
            text="Member ID"
        ).grid(
            row=0,
            column=0
        )

        self.member_id_entry.grid(
            row=0,
            column=1
        )

        tk.Label(
            form,
            text="ISBN"
        ).grid(
            row=1,
            column=0
        )

        self.book_isbn_entry.grid(
            row=1,
            column=1
        )

        tk.Button(
            form,
            text="Borrow Book",
            command=self.borrow_book
        ).grid(
            row=2,
            column=0
        )

        tk.Button(
            form,
            text="Return Book",
            command=self.return_book
        ).grid(
            row=2,
            column=1
        )

        self.borrow_tree = ttk.Treeview(
            self.borrow_tab,
            columns=(
                "member",
                "name",
                "isbn",
                "title"
            ),
            show="headings"
        )

        for column in self.borrow_tree["columns"]:

            self.borrow_tree.heading(
                column,
                text=column.title()
            )

        self.borrow_tree.pack(
            fill=tk.BOTH,
            expand=True
        )

    def borrow_book(self):

        try:

            self.library.borrow_book(
                self.member_id_entry.get(),
                self.book_isbn_entry.get()
            )

            self.refresh_borrowed()

        except Exception as error:

            messagebox.showerror(
                "Error",
                str(error)
            )

    def return_book(self):

        try:

            penalty = self.library.return_book(
                self.member_id_entry.get(),
                self.book_isbn_entry.get()
            )

            messagebox.showinfo(
                "Returned",
                f"Penalty: {penalty}"
            )

            self.refresh_borrowed()

        except Exception as error:

            messagebox.showerror(
                "Error",
                str(error)
            )

    def refresh_borrowed(self):

        if not hasattr(
            self,
            "borrow_tree"
        ):
            return

        for item in self.borrow_tree.get_children():

            self.borrow_tree.delete(
                item
            )

        for item in self.library.get_borrowed_books():

            self.borrow_tree.insert(
                "",
                tk.END,
                values=(
                    item["member_id"],
                    item["member_name"],
                    item["isbn"],
                    item["title"]
                )
            )

# =========================
# Application Entry Point
# =========================

if __name__ == "__main__":

    window = tk.Tk()

    app = LibraryGUI(
        window
    )

    window.mainloop()