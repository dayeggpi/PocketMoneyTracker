"""
Pocket Money Tracker - Desktop Application
A Python app to monitor pocket money saving for kids
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
import customtkinter as ctk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Set appearance mode and color theme
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Color constants matching the web app
COLORS = {
    "primary": "#4f46e5",
    "primary_hover": "#4338ca",
    "success": "#10b981",
    "danger": "#ef4444",
    "warning": "#f59e0b",
    "spent": "#f97316",
    "saved": "#22c55e",
    "given": "#8b5cf6",
    "bg": "#f8fafc",
    "card_bg": "#ffffff",
    "text": "#1e293b",
    "text_muted": "#64748b",
    "border": "#e2e8f0",
}


class DataManager:
    """Handles all data operations with the JSON file."""
    
    def __init__(self, data_file: str = "data/data.json"):
        self.data_file = Path(data_file)
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """Create data directory and file if they don't exist."""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_file.exists():
            initial_data = {
                "kids": [],
                "settings": {"period": "monthly", "currency": "EUR"}
            }
            self._save_data(initial_data)
    
    def _load_data(self) -> dict:
        """Load data from JSON file."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"kids": [], "settings": {"period": "monthly", "currency": "EUR"}}
    
    def _save_data(self, data: dict):
        """Save data to JSON file."""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    def get_settings(self) -> dict:
        """Get application settings."""
        return self._load_data().get("settings", {"period": "monthly", "currency": "EUR"})
    
    def update_settings(self, settings: dict):
        """Update application settings."""
        data = self._load_data()
        data["settings"].update(settings)
        self._save_data(data)
    
    def get_kids(self) -> list:
        """Get all kids with calculated totals."""
        data = self._load_data()
        kids = []
        for kid in data.get("kids", []):
            totals = self._calculate_totals(kid)
            kids.append({
                "id": kid["id"],
                "name": kid["name"],
                "allocation": kid.get("allocation", {"spent": 40, "saved": 40, "given": 20}),
                "interestRate": kid.get("interestRate", 0),
                "totals": totals
            })
        return kids
    
    def get_kid(self, kid_id: str) -> Optional[dict]:
        """Get a specific kid by ID with full details."""
        data = self._load_data()
        for kid in data.get("kids", []):
            if kid["id"] == kid_id:
                totals = self._calculate_totals(kid)
                return {
                    **kid,
                    "totals": totals,
                    "entries": totals.get("entries", [])
                }
        return None
    
    def add_kid(self, name: str) -> dict:
        """Add a new kid."""
        data = self._load_data()
        new_kid = {
            "id": f"kid_{uuid.uuid4().hex[:12]}",
            "name": name,
            "allocation": {"spent": 40, "saved": 40, "given": 20},
            "interestRate": 0,
            "entries": []
        }
        data["kids"].append(new_kid)
        self._save_data(data)
        return new_kid
    
    def update_kid(self, kid_id: str, name: str) -> bool:
        """Update a kid's name."""
        data = self._load_data()
        for kid in data["kids"]:
            if kid["id"] == kid_id:
                kid["name"] = name
                self._save_data(data)
                return True
        return False
    
    def delete_kid(self, kid_id: str) -> bool:
        """Delete a kid."""
        data = self._load_data()
        original_len = len(data["kids"])
        data["kids"] = [k for k in data["kids"] if k["id"] != kid_id]
        if len(data["kids"]) < original_len:
            self._save_data(data)
            return True
        return False
    
    def update_allocation(self, kid_id: str, spent: float, saved: float, 
                          given: float, interest_rate: float) -> bool:
        """Update a kid's allocation settings."""
        data = self._load_data()
        for kid in data["kids"]:
            if kid["id"] == kid_id:
                kid["allocation"] = {"spent": spent, "saved": saved, "given": given}
                kid["interestRate"] = interest_rate
                self._save_data(data)
                return True
        return False
    
    def add_entry(self, kid_id: str, period: str, period_type: str, 
                  amount: float, interest_rate: float,
                  spent_pct: float, saved_pct: float, given_pct: float,
                  used_from_saved: float = 0) -> Optional[dict]:
        """Add a money entry for a kid."""
        data = self._load_data()
        for kid in data["kids"]:
            if kid["id"] == kid_id:
                # Check for duplicate period
                for entry in kid.get("entries", []):
                    if entry["period"] == period:
                        return None  # Duplicate
                
                new_entry = {
                    "id": f"entry_{uuid.uuid4().hex[:12]}",
                    "period": period,
                    "periodType": period_type,
                    "amount": amount,
                    "spentPercent": spent_pct,
                    "savedPercent": saved_pct,
                    "givenPercent": given_pct,
                    "spent": round(amount * spent_pct / 100, 2),
                    "saved": round(amount * saved_pct / 100, 2),
                    "given": round(amount * given_pct / 100, 2),
                    "usedFromSaved": round(used_from_saved, 2),
                    "interestRate": interest_rate,
                    "createdAt": datetime.now().isoformat()
                }
                
                if "entries" not in kid:
                    kid["entries"] = []
                kid["entries"].append(new_entry)
                self._save_data(data)
                return new_entry
        return None
    
    def update_entry(self, kid_id: str, entry_id: str, amount: float,
                     spent_pct: float, saved_pct: float, given_pct: float,
                     interest_rate: float, used_from_saved: float = 0,
                     period: str = None, period_type: str = None) -> bool:
        """Update an existing entry."""
        data = self._load_data()
        for kid in data["kids"]:
            if kid["id"] == kid_id:
                for entry in kid.get("entries", []):
                    if entry["id"] == entry_id:
                        # Check if new period conflicts with existing entries
                        if period and period != entry["period"]:
                            for other_entry in kid.get("entries", []):
                                if other_entry["id"] != entry_id and other_entry["period"] == period:
                                    return False  # Conflict
                            entry["period"] = period
                            if period_type:
                                entry["periodType"] = period_type
                        
                        entry["amount"] = amount
                        entry["spentPercent"] = spent_pct
                        entry["savedPercent"] = saved_pct
                        entry["givenPercent"] = given_pct
                        entry["spent"] = round(amount * spent_pct / 100, 2)
                        entry["saved"] = round(amount * saved_pct / 100, 2)
                        entry["given"] = round(amount * given_pct / 100, 2)
                        entry["usedFromSaved"] = round(used_from_saved, 2)
                        entry["interestRate"] = interest_rate
                        entry["updatedAt"] = datetime.now().isoformat()
                        self._save_data(data)
                        return True
        return False
    
    def delete_entry(self, kid_id: str, entry_id: str) -> bool:
        """Delete an entry."""
        data = self._load_data()
        for kid in data["kids"]:
            if kid["id"] == kid_id:
                original_len = len(kid.get("entries", []))
                kid["entries"] = [e for e in kid.get("entries", []) if e["id"] != entry_id]
                if len(kid["entries"]) < original_len:
                    self._save_data(data)
                    return True
        return False
    
    def _calculate_totals(self, kid: dict) -> dict:
        """Calculate totals with interest for a kid."""
        total_spent = 0
        total_given = 0
        total_interest = 0
        total_used_from_saved = 0
        
        entries = kid.get("entries", [])
        sorted_entries = sorted(entries, key=lambda x: x["period"])
        
        running_saved = 0
        processed_entries = []
        
        for entry in sorted_entries:
            interest_rate = entry.get("interestRate", 0)
            interest_amount = running_saved * (interest_rate / 100)
            total_interest += interest_amount
            running_saved += interest_amount
            
            total_spent += entry["spent"]
            running_saved += entry["saved"]
            total_given += entry["given"]
            
            # Subtract used from saved
            used_from_saved = entry.get("usedFromSaved", 0)
            running_saved -= used_from_saved
            total_used_from_saved += used_from_saved
            
            processed_entry = {
                **entry,
                "interestEarned": round(interest_amount, 2),
                "runningSaved": round(running_saved, 2)
            }
            processed_entries.append(processed_entry)
        
        # Add used from saved to total spent
        total_spent_with_used = total_spent + total_used_from_saved
        
        return {
            "totalSpent": round(total_spent_with_used, 2),
            "totalSaved": round(running_saved, 2),
            "totalGiven": round(total_given, 2),
            "totalInterest": round(total_interest, 2),
            "totalUsedFromSaved": round(total_used_from_saved, 2),
            "grandTotal": round(total_spent_with_used + running_saved + total_given, 2),
            "entries": processed_entries
        }


class PeriodHelper:
    """Helper class for period calculations."""
    
    @staticmethod
    def get_week_number(date: datetime) -> int:
        """Get ISO week number."""
        return date.isocalendar()[1]
    
    @staticmethod
    def get_max_weeks_in_year(year: int) -> int:
        """Get the maximum number of weeks in a year."""
        dec_28 = datetime(year, 12, 28)
        return dec_28.isocalendar()[1]
    
    @staticmethod
    def get_week_dates(week: int, year: int) -> Tuple[datetime, datetime]:
        """Get start and end dates for a given week number and year."""
        jan_4 = datetime(year, 1, 4)
        start_of_week_1 = jan_4 - timedelta(days=jan_4.weekday())
        start_date = start_of_week_1 + timedelta(weeks=week - 1)
        end_date = start_date + timedelta(days=6)
        return start_date, end_date
    
    @staticmethod
    def get_biweek_dates(biweek: int, year: int) -> Tuple[datetime, datetime]:
        """Get start and end dates for a given bi-weekly period."""
        start_week = (biweek - 1) * 2 + 1
        end_week = start_week + 1
        start_date, _ = PeriodHelper.get_week_dates(start_week, year)
        _, end_date = PeriodHelper.get_week_dates(end_week, year)
        return start_date, end_date
    
    @staticmethod
    def get_quarter_dates(quarter: int, year: int) -> Tuple[datetime, datetime]:
        """Get start and end dates for a given quarter."""
        start_month = (quarter - 1) * 3 + 1
        end_month = start_month + 2
        start_date = datetime(year, start_month, 1)
        if end_month == 12:
            end_date = datetime(year, 12, 31)
        else:
            end_date = datetime(year, end_month + 1, 1) - timedelta(days=1)
        return start_date, end_date
    
    @staticmethod
    def get_month_dates(month: int, year: int) -> Tuple[datetime, datetime]:
        """Get start and end dates for a given month."""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year, 12, 31)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        return start_date, end_date
    
    @staticmethod
    def format_date_range(start: datetime, end: datetime) -> str:
        """Format a date range for display."""
        if start.year == end.year:
            if start.month == end.month:
                return f"{start.day}-{end.day} {start.strftime('%b %Y')}"
            else:
                return f"{start.strftime('%d %b')} - {end.strftime('%d %b %Y')}"
        else:
            return f"{start.strftime('%d %b %Y')} - {end.strftime('%d %b %Y')}"
    
    @staticmethod
    def get_current_period(period_type: str) -> dict:
        """Get current period based on type."""
        now = datetime.now()
        year = now.year
        month = now.month
        
        if period_type == "weekly":
            return {"year": year, "week": PeriodHelper.get_week_number(now), "type": "weekly"}
        elif period_type == "biweekly":
            biweek = (PeriodHelper.get_week_number(now) + 1) // 2
            return {"year": year, "biweek": biweek, "type": "biweekly"}
        elif period_type == "quarterly":
            quarter = (month - 1) // 3 + 1
            return {"year": year, "quarter": quarter, "type": "quarterly"}
        else:  # monthly
            return {"year": year, "month": month, "type": "monthly"}
    
    @staticmethod
    def get_period_key(period: dict) -> str:
        """Get period key string."""
        if period["type"] == "weekly":
            return f"{period['year']}-W{period['week']:02d}"
        elif period["type"] == "biweekly":
            return f"{period['year']}-BW{period['biweek']:02d}"
        elif period["type"] == "quarterly":
            return f"{period['year']}-Q{period['quarter']}"
        else:  # monthly
            return f"{period['year']}-{period['month']:02d}"
    
    @staticmethod
    def parse_period_key(period_key: str) -> dict:
        """Parse a period key back to a period dict."""
        if "-W" in period_key:
            year, week = period_key.split("-W")
            return {"year": int(year), "week": int(week), "type": "weekly"}
        elif "-BW" in period_key:
            year, biweek = period_key.split("-BW")
            return {"year": int(year), "biweek": int(biweek), "type": "biweekly"}
        elif "-Q" in period_key:
            year, quarter = period_key.split("-Q")
            return {"year": int(year), "quarter": int(quarter), "type": "quarterly"}
        else:
            year, month = period_key.split("-")
            return {"year": int(year), "month": int(month), "type": "monthly"}
    
    @staticmethod
    def format_period_display(period: dict, include_dates: bool = True) -> str:
        """Format period for display with optional date range."""
        year = period.get("year", datetime.now().year)
        
        if period["type"] == "weekly":
            week = period["week"]
            base = f"Week {week}, {year}"
            if include_dates:
                start, end = PeriodHelper.get_week_dates(week, year)
                return f"{base}\n({PeriodHelper.format_date_range(start, end)})"
            return base
        elif period["type"] == "biweekly":
            biweek = period["biweek"]
            base = f"Period {biweek}, {year}"
            if include_dates:
                start, end = PeriodHelper.get_biweek_dates(biweek, year)
                return f"{base}\n({PeriodHelper.format_date_range(start, end)})"
            return base
        elif period["type"] == "quarterly":
            quarter = period["quarter"]
            base = f"Q{quarter} {year}"
            if include_dates:
                start, end = PeriodHelper.get_quarter_dates(quarter, year)
                return f"{base}\n({PeriodHelper.format_date_range(start, end)})"
            return base
        else:  # monthly
            month = period["month"]
            month_names = ["January", "February", "March", "April", "May", "June",
                          "July", "August", "September", "October", "November", "December"]
            base = f"{month_names[month - 1]} {year}"
            if include_dates:
                start, end = PeriodHelper.get_month_dates(month, year)
                return f"{base}\n({start.day}-{end.day} {start.strftime('%b')})"
            return base
    
    @staticmethod
    def format_period_label(period_key: str, include_dates: bool = False) -> str:
        """Format period key for display."""
        period = PeriodHelper.parse_period_key(period_key)
        return PeriodHelper.format_period_display(period, include_dates)
    
    @staticmethod
    def format_period_short(period_key: str) -> str:
        """Format period key for short display (table)."""
        period = PeriodHelper.parse_period_key(period_key)
        year = period.get("year", datetime.now().year)
        
        if period["type"] == "weekly":
            start, end = PeriodHelper.get_week_dates(period["week"], year)
            return f"W{period['week']} ({start.strftime('%d/%m')}-{end.strftime('%d/%m')})"
        elif period["type"] == "biweekly":
            start, end = PeriodHelper.get_biweek_dates(period["biweek"], year)
            return f"BW{period['biweek']} ({start.strftime('%d/%m')}-{end.strftime('%d/%m')})"
        elif period["type"] == "quarterly":
            start, end = PeriodHelper.get_quarter_dates(period["quarter"], year)
            return f"Q{period['quarter']} ({start.strftime('%b')}-{end.strftime('%b %Y')})"
        else:
            month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            return f"{month_names[period['month'] - 1]} {year}"
    
    @staticmethod
    def navigate_period(period: dict, direction: int) -> dict:
        """Navigate to next/previous period."""
        new_period = period.copy()
        year = new_period["year"]
        
        if period["type"] == "weekly":
            max_weeks = PeriodHelper.get_max_weeks_in_year(year)
            new_period["week"] += direction
            if new_period["week"] < 1:
                new_period["year"] -= 1
                new_period["week"] = PeriodHelper.get_max_weeks_in_year(new_period["year"])
            elif new_period["week"] > max_weeks:
                new_period["week"] = 1
                new_period["year"] += 1
        elif period["type"] == "biweekly":
            max_biweeks = (PeriodHelper.get_max_weeks_in_year(year) + 1) // 2
            new_period["biweek"] += direction
            if new_period["biweek"] < 1:
                new_period["year"] -= 1
                new_period["biweek"] = (PeriodHelper.get_max_weeks_in_year(new_period["year"]) + 1) // 2
            elif new_period["biweek"] > max_biweeks:
                new_period["biweek"] = 1
                new_period["year"] += 1
        elif period["type"] == "quarterly":
            new_period["quarter"] += direction
            if new_period["quarter"] < 1:
                new_period["quarter"] = 4
                new_period["year"] -= 1
            elif new_period["quarter"] > 4:
                new_period["quarter"] = 1
                new_period["year"] += 1
        else:  # monthly
            new_period["month"] += direction
            if new_period["month"] < 1:
                new_period["month"] = 12
                new_period["year"] -= 1
            elif new_period["month"] > 12:
                new_period["month"] = 1
                new_period["year"] += 1
        
        return new_period


class KidCard(ctk.CTkFrame):
    """Widget for displaying a kid's summary card."""
    
    def __init__(self, parent, kid: dict, on_select, on_edit, on_delete):
        super().__init__(parent, corner_radius=12, fg_color=COLORS["bg"], 
                        border_width=2, border_color=COLORS["bg"])
        
        self.kid = kid
        self.on_select = on_select
        self.on_edit = on_edit
        self.on_delete = on_delete
        
        # Configure hover effect
        self.configure(cursor="hand2")
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        self._create_widgets()
        
        # Bind click to entire card
        self._bind_click_recursive(self)
    
    def _bind_click_recursive(self, widget):
        """Recursively bind click event to widget and all children except buttons."""
        widget_class = widget.winfo_class()
        widget_type = type(widget).__name__
        # Skip buttons
        if widget_type not in ("CTkButton",) and widget_class not in ("Button", "TButton"):
            widget.bind("<Button-1>", lambda e: self._handle_click(e))
            for child in widget.winfo_children():
                self._bind_click_recursive(child)
    
    def _handle_click(self, event):
        """Handle click on the card."""
        self.on_select(self.kid["id"])
    
    def _on_enter(self, event):
        """Handle mouse enter."""
        self.configure(border_color=COLORS["primary"])
    
    def _on_leave(self, event):
        """Handle mouse leave."""
        self.configure(border_color=COLORS["bg"])
        
    def _create_widgets(self):
        # Main content frame
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Header with name and buttons
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        
        name_label = ctk.CTkLabel(
            header, 
            text=f"👦 {self.kid['name']}", 
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text"]
        )
        name_label.pack(side="left")
        
        # Action buttons
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")
        
        edit_btn = ctk.CTkButton(
            btn_frame, text="✏️", width=35, height=35,
            fg_color=COLORS["warning"], hover_color="#d97706",
            command=lambda: self.on_edit(self.kid["id"], self.kid["name"])
        )
        edit_btn.pack(side="left", padx=2)
        
        delete_btn = ctk.CTkButton(
            btn_frame, text="🗑️", width=35, height=35,
            fg_color=COLORS["danger"], hover_color="#dc2626",
            command=lambda: self.on_delete(self.kid["id"], self.kid["name"])
        )
        delete_btn.pack(side="left", padx=2)
        
        # Totals
        totals = self.kid.get("totals", {})
        totals_frame = ctk.CTkFrame(content, fg_color="transparent")
        totals_frame.pack(fill="x")
        
        for col, (label, value, color) in enumerate([
            ("Spent", totals.get("totalSpent", 0), COLORS["spent"]),
            ("Saved", totals.get("totalSaved", 0), COLORS["saved"]),
            ("Given", totals.get("totalGiven", 0), COLORS["given"])
        ]):
            totals_frame.grid_columnconfigure(col, weight=1)
            
            item_frame = ctk.CTkFrame(totals_frame, fg_color=COLORS["card_bg"], corner_radius=8)
            item_frame.grid(row=0, column=col, padx=3, sticky="ew")
            
            ctk.CTkLabel(
                item_frame, text=label, 
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=COLORS["text_muted"]
            ).pack(pady=(8, 2))
            
            ctk.CTkLabel(
                item_frame, text=f"€{value:.2f}",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=color
            ).pack(pady=(0, 8))


class PeriodSelectorWidget(ctk.CTkFrame):
    """Reusable period selector widget with detailed date display."""
    
    def __init__(self, parent, period_type: str, initial_period: dict = None,
                 on_change=None, show_type_selector: bool = False, compact: bool = False):
        super().__init__(parent, fg_color="transparent")
        
        self.period_type = period_type
        self.current_period = initial_period or PeriodHelper.get_current_period(period_type)
        self.on_change = on_change
        self.show_type_selector = show_type_selector
        self.compact = compact
        
        self._create_widgets()
    
    def _create_widgets(self):
        # Period type selector (optional)
        if self.show_type_selector:
            type_frame = ctk.CTkFrame(self, fg_color="transparent")
            type_frame.pack(fill="x", pady=(0, 10))
            
            ctk.CTkLabel(type_frame, text="Period Type:").pack(side="left", padx=(0, 10))
            
            self.type_var = ctk.StringVar(value=self.period_type)
            type_menu = ctk.CTkOptionMenu(
                type_frame,
                values=["weekly", "biweekly", "monthly", "quarterly"],
                variable=self.type_var,
                command=self._on_type_change,
                width=120
            )
            type_menu.pack(side="left")
        
        # Navigation frame
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x")
        
        # Previous button
        ctk.CTkButton(
            nav_frame, text="◀", width=35, height=35,
            command=lambda: self._navigate(-1)
        ).pack(side="left", padx=(0, 5))
        
        # Period display
        display_frame = ctk.CTkFrame(nav_frame, fg_color=COLORS["bg"], corner_radius=8)
        display_frame.pack(side="left", fill="x", expand=True, padx=5)
        
        self.period_label = ctk.CTkLabel(
            display_frame,
            text=self._get_display_text(),
            font=ctk.CTkFont(size=12 if self.compact else 13, weight="bold"),
            text_color=COLORS["primary"],
            justify="center"
        )
        self.period_label.pack(padx=15, pady=8 if self.compact else 10)
        
        # Next button
        ctk.CTkButton(
            nav_frame, text="▶", width=35, height=35,
            command=lambda: self._navigate(1)
        ).pack(side="left", padx=(5, 0))
        
        # Year selector for quick navigation
        year_frame = ctk.CTkFrame(self, fg_color="transparent")
        year_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkLabel(year_frame, text="Year:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 5))
        
        current_year = datetime.now().year
        years = [str(y) for y in range(current_year - 5, current_year + 3)]
        
        self.year_var = ctk.StringVar(value=str(self.current_period.get("year", current_year)))
        year_menu = ctk.CTkOptionMenu(
            year_frame,
            values=years,
            variable=self.year_var,
            command=self._on_year_change,
            width=80
        )
        year_menu.pack(side="left")
        
        # Specific period selector
        self._create_period_selector(year_frame)
    
    def _create_period_selector(self, parent):
        """Create period-specific selector."""
        self.period_var = ctk.StringVar()
        
        if self.period_type == "weekly":
            year = self.current_period.get("year", datetime.now().year)
            max_weeks = PeriodHelper.get_max_weeks_in_year(year)
            values = [str(w) for w in range(1, max_weeks + 1)]
            self.period_var.set(str(self.current_period.get("week", 1)))
            label = "Week:"
        elif self.period_type == "biweekly":
            year = self.current_period.get("year", datetime.now().year)
            max_biweeks = (PeriodHelper.get_max_weeks_in_year(year) + 1) // 2
            values = [str(b) for b in range(1, max_biweeks + 1)]
            self.period_var.set(str(self.current_period.get("biweek", 1)))
            label = "Period:"
        elif self.period_type == "quarterly":
            values = ["1", "2", "3", "4"]
            self.period_var.set(str(self.current_period.get("quarter", 1)))
            label = "Quarter:"
        else:  # monthly
            values = [str(m) for m in range(1, 13)]
            self.period_var.set(str(self.current_period.get("month", 1)))
            label = "Month:"
        
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=11)).pack(side="left", padx=(15, 5))
        
        self.period_menu = ctk.CTkOptionMenu(
            parent,
            values=values,
            variable=self.period_var,
            command=self._on_period_select,
            width=70
        )
        self.period_menu.pack(side="left")
    
    def _get_display_text(self) -> str:
        """Get display text for current period."""
        return PeriodHelper.format_period_display(self.current_period, include_dates=True)
    
    def _update_display(self):
        """Update the period display."""
        self.period_label.configure(text=self._get_display_text())
        self.year_var.set(str(self.current_period.get("year", datetime.now().year)))
        
        # Update period selector value
        if self.period_type == "weekly":
            self.period_var.set(str(self.current_period.get("week", 1)))
        elif self.period_type == "biweekly":
            self.period_var.set(str(self.current_period.get("biweek", 1)))
        elif self.period_type == "quarterly":
            self.period_var.set(str(self.current_period.get("quarter", 1)))
        else:
            self.period_var.set(str(self.current_period.get("month", 1)))
        
        if self.on_change:
            self.on_change(self.current_period)
    
    def _navigate(self, direction: int):
        """Navigate to next/previous period."""
        self.current_period = PeriodHelper.navigate_period(self.current_period, direction)
        self._update_display()
    
    def _on_year_change(self, value: str):
        """Handle year change."""
        self.current_period["year"] = int(value)
        
        # Validate period is within range for new year
        if self.period_type == "weekly":
            max_weeks = PeriodHelper.get_max_weeks_in_year(int(value))
            if self.current_period.get("week", 1) > max_weeks:
                self.current_period["week"] = max_weeks
            # Update week selector values
            values = [str(w) for w in range(1, max_weeks + 1)]
            self.period_menu.configure(values=values)
        elif self.period_type == "biweekly":
            max_biweeks = (PeriodHelper.get_max_weeks_in_year(int(value)) + 1) // 2
            if self.current_period.get("biweek", 1) > max_biweeks:
                self.current_period["biweek"] = max_biweeks
            values = [str(b) for b in range(1, max_biweeks + 1)]
            self.period_menu.configure(values=values)
        
        self._update_display()
    
    def _on_period_select(self, value: str):
        """Handle period selection."""
        if self.period_type == "weekly":
            self.current_period["week"] = int(value)
        elif self.period_type == "biweekly":
            self.current_period["biweek"] = int(value)
        elif self.period_type == "quarterly":
            self.current_period["quarter"] = int(value)
        else:
            self.current_period["month"] = int(value)
        
        self._update_display()
    
    def _on_type_change(self, value: str):
        """Handle period type change."""
        self.period_type = value
        self.current_period = PeriodHelper.get_current_period(value)
        
        # Rebuild the selector
        for widget in self.winfo_children():
            widget.destroy()
        self._create_widgets()
        
        if self.on_change:
            self.on_change(self.current_period)
    
    def get_period(self) -> dict:
        """Get current period."""
        return self.current_period
    
    def get_period_key(self) -> str:
        """Get current period key."""
        return PeriodHelper.get_period_key(self.current_period)
    
    def get_period_type(self) -> str:
        """Get current period type."""
        return self.period_type
    
    def set_period(self, period: dict):
        """Set the current period."""
        self.current_period = period
        self.period_type = period["type"]
        self._update_display()


class EditEntryDialog(ctk.CTkToplevel):
    """Dialog for editing an entry."""
    
    def __init__(self, parent, entry: dict, on_save, period_type: str = "monthly", 
                 available_saved_before_entry: float = 0):
        super().__init__(parent)
        
        self.entry = entry
        self.on_save = on_save
        self.period_type = entry.get("periodType", period_type)
        # Available saved is what was available BEFORE this entry + what this entry saved - what was used
        self.available_saved = available_saved_before_entry + entry.get("saved", 0)
        
        self.title("Edit Entry")
        self.geometry("500x750")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._center_window()
    
    def _center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 500) // 2
        y = (self.winfo_screenheight() - 750) // 2
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(
            main_frame, text="📝 Edit Entry",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(0, 15))
        
        # Period selector section
        period_section = ctk.CTkFrame(main_frame, fg_color=COLORS["bg"], corner_radius=8)
        period_section.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            period_section, text="📅 Period",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Parse existing period
        existing_period = PeriodHelper.parse_period_key(self.entry["period"])
        
        self.period_selector = PeriodSelectorWidget(
            period_section,
            period_type=existing_period["type"],
            initial_period=existing_period,
            show_type_selector=True,
            compact=True
        )
        self.period_selector.pack(fill="x", padx=15, pady=(0, 15))
        
        # Amount section
        amount_section = ctk.CTkFrame(main_frame, fg_color=COLORS["bg"], corner_radius=8)
        amount_section.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            amount_section, text="💵 Amount (EUR)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.amount_var = ctk.StringVar(value=str(self.entry["amount"]))
        self.amount_entry = ctk.CTkEntry(
            amount_section, textvariable=self.amount_var, 
            height=40, font=ctk.CTkFont(size=16)
        )
        self.amount_entry.pack(fill="x", padx=15, pady=(0, 15))
        self.amount_var.trace_add("write", lambda *args: self._update_summary())
        
        # Used from Saved section
        used_section = ctk.CTkFrame(main_frame, fg_color=COLORS["bg"], corner_radius=8)
        used_section.pack(fill="x", pady=(0, 15))
        
        used_header = ctk.CTkFrame(used_section, fg_color="transparent")
        used_header.pack(fill="x", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            used_header, text="💸 Used from Saved (EUR)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")
        
        ctk.CTkLabel(
            used_header, 
            text=f"(Max: €{self.available_saved:.2f})",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"]
        ).pack(side="right")
        
        self.used_from_saved_var = ctk.StringVar(value=str(self.entry.get("usedFromSaved", 0)))
        self.used_from_saved_entry = ctk.CTkEntry(
            used_section, textvariable=self.used_from_saved_var, 
            height=40, font=ctk.CTkFont(size=16)
        )
        self.used_from_saved_entry.pack(fill="x", padx=15, pady=(0, 15))
        self.used_from_saved_var.trace_add("write", lambda *args: self._update_summary())
        
        # Allocation section
        alloc_section = ctk.CTkFrame(main_frame, fg_color=COLORS["bg"], corner_radius=8)
        alloc_section.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            alloc_section, text="📊 Allocation",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        alloc_frame = ctk.CTkFrame(alloc_section, fg_color="transparent")
        alloc_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.spent_var = ctk.StringVar(value=str(self.entry.get("spentPercent", 40)))
        self.saved_var = ctk.StringVar(value=str(self.entry.get("savedPercent", 40)))
        self.given_var = ctk.StringVar(value=str(self.entry.get("givenPercent", 20)))
        self.interest_var = ctk.StringVar(value=str(self.entry.get("interestRate", 0)))
        
        for i, (label, var, color) in enumerate([
            ("🛒 Spent %", self.spent_var, COLORS["spent"]),
            ("🏦 Saved %", self.saved_var, COLORS["saved"]),
            ("🎁 Given %", self.given_var, COLORS["given"]),
            ("📈 Interest %", self.interest_var, COLORS["primary"])
        ]):
            alloc_frame.grid_columnconfigure(i, weight=1)
            
            item_frame = ctk.CTkFrame(alloc_frame, fg_color="transparent")
            item_frame.grid(row=0, column=i, padx=3)
            
            ctk.CTkLabel(item_frame, text=label, font=ctk.CTkFont(size=10)).pack()
            entry = ctk.CTkEntry(item_frame, textvariable=var, width=55, justify="center")
            entry.pack(pady=5)
            var.trace_add("write", lambda *args: self._update_summary())
        
        # Total indicator
        self.total_label = ctk.CTkLabel(
            alloc_section, text="Total: 100%",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.total_label.pack(pady=(0, 15))
        
        # Summary section
        summary_section = ctk.CTkFrame(main_frame, fg_color=COLORS["bg"], corner_radius=8)
        summary_section.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            summary_section, text="📋 Summary",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        summary_frame = ctk.CTkFrame(summary_section, fg_color="transparent")
        summary_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.summary_labels = {}
        for i, (label, color) in enumerate([
            ("Spent", COLORS["spent"]),
            ("Saved", COLORS["saved"]),
            ("Given", COLORS["given"]),
            ("Used", COLORS["danger"])
        ]):
            summary_frame.grid_columnconfigure(i, weight=1)
            
            item_frame = ctk.CTkFrame(summary_frame, fg_color=COLORS["card_bg"], corner_radius=8)
            item_frame.grid(row=0, column=i, padx=3, sticky="ew")
            
            ctk.CTkLabel(item_frame, text=label, font=ctk.CTkFont(size=10)).pack(pady=(8, 2))
            self.summary_labels[label.lower()] = ctk.CTkLabel(
                item_frame, text="€0.00",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=color
            )
            self.summary_labels[label.lower()].pack(pady=(0, 8))
        
        # Error label for used from saved
        self.used_error_label = ctk.CTkLabel(
            main_frame, text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["danger"]
        )
        self.used_error_label.pack(pady=(0, 5))
        
        # Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkButton(
            btn_frame, text="Cancel", width=100,
            fg_color=COLORS["text_muted"], hover_color="#475569",
            command=self.destroy
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            btn_frame, text="Save Changes", width=120,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=self._save
        ).pack(side="right")
        
        self._update_summary()
    
    def _update_summary(self):
        try:
            amount = float(self.amount_var.get() or 0)
            spent_pct = float(self.spent_var.get() or 0)
            saved_pct = float(self.saved_var.get() or 0)
            given_pct = float(self.given_var.get() or 0)
            used_from_saved = float(self.used_from_saved_var.get() or 0)
            
            total = spent_pct + saved_pct + given_pct
            
            self.total_label.configure(text=f"Total: {total:.1f}%")
            if abs(total - 100) > 0.01:
                self.total_label.configure(text_color=COLORS["danger"])
            else:
                self.total_label.configure(text_color=COLORS["success"])
            
            self.summary_labels["spent"].configure(text=f"€{amount * spent_pct / 100:.2f}")
            self.summary_labels["saved"].configure(text=f"€{amount * saved_pct / 100:.2f}")
            self.summary_labels["given"].configure(text=f"€{amount * given_pct / 100:.2f}")
            self.summary_labels["used"].configure(text=f"-€{used_from_saved:.2f}")
            
            # Validate used from saved
            if used_from_saved > self.available_saved:
                self.used_error_label.configure(
                    text=f"⚠️ Cannot exceed available saved (€{self.available_saved:.2f})"
                )
            elif used_from_saved < 0:
                self.used_error_label.configure(text="⚠️ Cannot be negative")
            else:
                self.used_error_label.configure(text="")
                
        except ValueError:
            pass
    
    def _save(self):
        try:
            amount = float(self.amount_var.get())
            spent_pct = float(self.spent_var.get())
            saved_pct = float(self.saved_var.get())
            given_pct = float(self.given_var.get())
            interest_rate = float(self.interest_var.get())
            used_from_saved = float(self.used_from_saved_var.get() or 0)
            
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be greater than 0")
                return
            
            if abs(spent_pct + saved_pct + given_pct - 100) > 0.01:
                messagebox.showerror("Error", "Allocation must total 100%")
                return
            
            if used_from_saved < 0:
                messagebox.showerror("Error", "Used from Saved cannot be negative")
                return
            
            if used_from_saved > self.available_saved:
                messagebox.showerror("Error", f"Cannot use more than available saved (€{self.available_saved:.2f})")
                return
            
            # Get period info from selector
            period_key = self.period_selector.get_period_key()
            period_type = self.period_selector.get_period_type()
            
            self.on_save(
                self.entry["id"], amount,
                spent_pct, saved_pct, given_pct, interest_rate,
                used_from_saved, period_key, period_type
            )
            self.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")
            
class KidDetailsView(ctk.CTkFrame):
    """View for displaying and managing a kid's details."""
    
    def __init__(self, parent, data_manager: DataManager, kid_id: str, on_back, on_period_type_change=None):
        super().__init__(parent, fg_color="transparent")
        
        self.dm = data_manager
        self.kid_id = kid_id
        self.on_back = on_back
        self.on_period_type_change = on_period_type_change
        self.current_period = None
        self.period_type = "monthly"
        self.chart_canvas = None
        
        self._load_kid()
        self._create_widgets()
    
    def _load_kid(self):
        """Load kid data."""
        self.kid = self.dm.get_kid(self.kid_id)
        settings = self.dm.get_settings()
        self.period_type = settings.get("period", "monthly")
        self.current_period = PeriodHelper.get_current_period(self.period_type)
    
    def _create_widgets(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["card_bg"], corner_radius=12)
        header.pack(fill="x", pady=(0, 15))
        
        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            header_inner,
            text=f"👦 {self.kid['name']}'s Pocket Money",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["primary"]
        ).pack(side="left")
        
        # Period type selector in header
        settings_frame = ctk.CTkFrame(header_inner, fg_color="transparent")
        settings_frame.pack(side="right")
        
        ctk.CTkButton(
            settings_frame, text="← Back", width=80,
            fg_color=COLORS["text_muted"], hover_color="#475569",
            command=self.on_back
        ).pack(side="right", padx=(10, 0))
        
        self.period_type_var = ctk.StringVar(value=self.period_type)
        period_menu = ctk.CTkOptionMenu(
            settings_frame,
            values=["weekly", "biweekly", "monthly", "quarterly"],
            variable=self.period_type_var,
            command=self._on_period_type_change,
            width=110
        )
        period_menu.pack(side="right", padx=5)
        
        ctk.CTkLabel(settings_frame, text="Period:").pack(side="right", padx=(0, 5))
        
        # Create scrollable content
        self.content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True)
        
        self._create_allocation_section()
        self._create_add_entry_section()
        self._create_totals_section()
        self._create_entries_section()
        self._create_chart_section()
    
    def _on_period_type_change(self, value: str):
        """Handle period type change."""
        self.period_type = value
        self.current_period = PeriodHelper.get_current_period(value)
        
        # Update the period selector
        if hasattr(self, 'period_selector'):
            self.period_selector.destroy()
        
        self.period_selector = PeriodSelectorWidget(
            self.period_selector_container,
            period_type=self.period_type,
            initial_period=self.current_period,
            on_change=self._on_period_change
        )
        self.period_selector.pack(fill="x")
        
        # Save settings
        self.dm.update_settings({"period": value})
        
        if self.on_period_type_change:
            self.on_period_type_change(value)
    
    def _on_period_change(self, period: dict):
        """Handle period change from selector."""
        self.current_period = period
    
    def _create_allocation_section(self):
        """Create allocation settings section."""
        section = ctk.CTkFrame(self.content, fg_color=COLORS["card_bg"], corner_radius=12)
        section.pack(fill="x", pady=(0, 15))
        
        inner = ctk.CTkFrame(section, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            inner, text="📊 Default Bucket Allocation",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            inner,
            text="This is the default allocation for new entries.",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", pady=(5, 15))
        
        # Allocation inputs
        alloc_frame = ctk.CTkFrame(inner, fg_color="transparent")
        alloc_frame.pack(fill="x")
        
        allocation = self.kid.get("allocation", {"spent": 40, "saved": 40, "given": 20})
        
        self.alloc_vars = {}
        for i, (key, label, default) in enumerate([
            ("spent", "🛒 Spent %", allocation.get("spent", 40)),
            ("saved", "🏦 Saved %", allocation.get("saved", 40)),
            ("given", "🎁 Given %", allocation.get("given", 20)),
            ("interest", "📈 Interest %", self.kid.get("interestRate", 0))
        ]):
            alloc_frame.grid_columnconfigure(i, weight=1)
            
            item_frame = ctk.CTkFrame(alloc_frame, fg_color="transparent")
            item_frame.grid(row=0, column=i, padx=10)
            
            ctk.CTkLabel(item_frame, text=label).pack()
            
            var = ctk.StringVar(value=str(default))
            self.alloc_vars[key] = var
            
            ctk.CTkEntry(item_frame, textvariable=var, width=80, justify="center").pack(pady=5)
        
        # Error label
        self.alloc_error = ctk.CTkLabel(inner, text="", text_color=COLORS["danger"])
        self.alloc_error.pack(pady=5)
        
        ctk.CTkButton(
            inner, text="Save Default Allocation", width=180,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=self._save_allocation
        ).pack(pady=(5, 0))
    
    def _create_add_entry_section(self):
        """Create add entry section."""
        section = ctk.CTkFrame(self.content, fg_color=COLORS["card_bg"], corner_radius=12)
        section.pack(fill="x", pady=(0, 15))
        
        inner = ctk.CTkFrame(section, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            inner, text="💵 Add Money Entry",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 15))
        
        # Period selector container
        self.period_selector_container = ctk.CTkFrame(inner, fg_color="transparent")
        self.period_selector_container.pack(fill="x", pady=(0, 15))
        
        self.period_selector = PeriodSelectorWidget(
            self.period_selector_container,
            period_type=self.period_type,
            initial_period=self.current_period,
            on_change=self._on_period_change
        )
        self.period_selector.pack(fill="x")
        
        # Amount and Used from Saved row
        entry_frame = ctk.CTkFrame(inner, fg_color="transparent")
        entry_frame.pack(fill="x")
        
        # Amount input
        ctk.CTkLabel(entry_frame, text="Amount (EUR):").pack(side="left", padx=(0, 10))
        
        self.amount_var = ctk.StringVar()
        ctk.CTkEntry(entry_frame, textvariable=self.amount_var, width=100, height=35).pack(side="left")
        
        # Used from Saved input
        ctk.CTkLabel(entry_frame, text="Used from Saved (EUR):").pack(side="left", padx=(20, 10))
        
        self.used_from_saved_var = ctk.StringVar(value="0")
        self.used_from_saved_entry = ctk.CTkEntry(
            entry_frame, textvariable=self.used_from_saved_var, 
            width=100, height=35
        )
        self.used_from_saved_entry.pack(side="left")
        
        # Available saved display
        available_saved = self.kid.get("totals", {}).get("totalSaved", 0)
        self.available_saved_label = ctk.CTkLabel(
            entry_frame, 
            text=f"(Available: €{available_saved:.2f})",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"]
        )
        self.available_saved_label.pack(side="left", padx=(5, 0))
        
        # Add button
        ctk.CTkButton(
            entry_frame, text="Add Entry", width=100, height=35,
            fg_color=COLORS["success"], hover_color="#059669",
            command=self._add_entry
        ).pack(side="left", padx=15)
    
    def _create_totals_section(self):
        """Create totals display section."""
        section = ctk.CTkFrame(self.content, fg_color=COLORS["card_bg"], corner_radius=12)
        section.pack(fill="x", pady=(0, 15))
        
        inner = ctk.CTkFrame(section, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            inner, text="📈 Current Totals",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 15))
        
        totals_frame = ctk.CTkFrame(inner, fg_color="transparent")
        totals_frame.pack(fill="x")
        
        totals = self.kid.get("totals", {})
        
        self.total_labels = {}
        for i, (key, label, icon, color) in enumerate([
            ("totalSpent", "Total Spent", "🛒", COLORS["spent"]),
            ("totalSaved", "Total Saved", "🏦", COLORS["saved"]),
            ("totalGiven", "Total Given", "🎁", COLORS["given"]),
            ("grandTotal", "Grand Total", "💰", COLORS["primary"])
        ]):
            totals_frame.grid_columnconfigure(i, weight=1)
            
            card = ctk.CTkFrame(totals_frame, fg_color=COLORS["bg"], corner_radius=10)
            card.grid(row=0, column=i, padx=5, sticky="ew")
            
            ctk.CTkLabel(
                card, text=f"{icon} {label}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_muted"]
            ).pack(pady=(10, 5))
            
            value = totals.get(key, 0)
            self.total_labels[key] = ctk.CTkLabel(
                card, text=f"€{value:.2f}",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=color
            )
            self.total_labels[key].pack(pady=(0, 10))
    
    def _create_entries_section(self):
        """Create entries history section."""
        section = ctk.CTkFrame(self.content, fg_color=COLORS["card_bg"], corner_radius=12)
        section.pack(fill="x", pady=(0, 15))
        
        inner = ctk.CTkFrame(section, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            inner, text="📜 Transaction History",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 15))
        
        # Entries container
        self.entries_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self.entries_frame.pack(fill="x")
        
        self._render_entries()
    
    def _render_entries(self):
        """Render entries table."""
        # Clear existing
        for widget in self.entries_frame.winfo_children():
            widget.destroy()
        
        entries = self.kid.get("totals", {}).get("entries", [])
        
        if not entries:
            ctk.CTkLabel(
                self.entries_frame,
                text="No entries yet. Add your first entry above!",
                text_color=COLORS["text_muted"]
            ).pack(pady=20)
            return
        
        # Header
        header_frame = ctk.CTkFrame(self.entries_frame, fg_color=COLORS["bg"], corner_radius=8)
        header_frame.pack(fill="x", pady=(0, 5))
        
        headers = ["Period", "Amount", "Spent", "Saved", "Given", "Used", "Interest", "Running", "Actions"]
        widths = [120, 70, 70, 70, 70, 70, 70, 80, 80]
        for i, (h, w) in enumerate(zip(headers, widths)):
            header_frame.grid_columnconfigure(i, weight=1 if i == 0 else 0)
            ctk.CTkLabel(
                header_frame, text=h,
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=COLORS["text_muted"],
                width=w
            ).grid(row=0, column=i, padx=1, pady=8)
        
        # Entries (sorted by period descending)
        sorted_entries = sorted(entries, key=lambda x: x["period"], reverse=True)
        
        for entry in sorted_entries:
            row_frame = ctk.CTkFrame(self.entries_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            
            for i in range(9):
                row_frame.grid_columnconfigure(i, weight=1 if i == 0 else 0)
            
            # Period with dates
            period_text = PeriodHelper.format_period_short(entry["period"])
            ctk.CTkLabel(
                row_frame,
                text=period_text,
                font=ctk.CTkFont(size=9, weight="bold"),
                width=120
            ).grid(row=0, column=0, padx=1, pady=5, sticky="w")
            
            # Amount
            ctk.CTkLabel(
                row_frame, text=f"€{entry['amount']:.2f}",
                font=ctk.CTkFont(size=9, weight="bold"),
                width=70
            ).grid(row=0, column=1, padx=1, pady=5)
            
            # Spent
            ctk.CTkLabel(
                row_frame,
                text=f"{entry.get('spentPercent', 0):.0f}%\n€{entry['spent']:.2f}",
                font=ctk.CTkFont(size=8),
                text_color=COLORS["spent"],
                width=70
            ).grid(row=0, column=2, padx=1, pady=5)
            
            # Saved
            ctk.CTkLabel(
                row_frame,
                text=f"{entry.get('savedPercent', 0):.0f}%\n€{entry['saved']:.2f}",
                font=ctk.CTkFont(size=8),
                text_color=COLORS["saved"],
                width=70
            ).grid(row=0, column=3, padx=1, pady=5)
            
            # Given
            ctk.CTkLabel(
                row_frame,
                text=f"{entry.get('givenPercent', 0):.0f}%\n€{entry['given']:.2f}",
                font=ctk.CTkFont(size=8),
                text_color=COLORS["given"],
                width=70
            ).grid(row=0, column=4, padx=1, pady=5)
            
            # Used from Saved
            used_from_saved = entry.get('usedFromSaved', 0)
            ctk.CTkLabel(
                row_frame,
                text=f"-€{used_from_saved:.2f}" if used_from_saved > 0 else "€0.00",
                font=ctk.CTkFont(size=9, weight="bold" if used_from_saved > 0 else "normal"),
                text_color=COLORS["danger"] if used_from_saved > 0 else COLORS["text_muted"],
                width=70
            ).grid(row=0, column=5, padx=1, pady=5)
            
            # Interest
            ctk.CTkLabel(
                row_frame,
                text=f"{entry.get('interestRate', 0):.1f}%\n+€{entry.get('interestEarned', 0):.2f}",
                font=ctk.CTkFont(size=8),
                text_color=COLORS["success"],
                width=70
            ).grid(row=0, column=6, padx=1, pady=5)
            
            # Running saved
            ctk.CTkLabel(
                row_frame,
                text=f"€{entry.get('runningSaved', 0):.2f}",
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=COLORS["primary"],
                width=80
            ).grid(row=0, column=7, padx=1, pady=5)
            
            # Actions
            actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=80)
            actions_frame.grid(row=0, column=8, padx=1, pady=5)
            
            entry_id = entry["id"]
            ctk.CTkButton(
                actions_frame, text="✏️", width=28, height=24,
                fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                command=lambda eid=entry_id: self._edit_entry(eid)
            ).pack(side="left", padx=1)
            
            ctk.CTkButton(
                actions_frame, text="🗑️", width=28, height=24,
                fg_color=COLORS["danger"], hover_color="#dc2626",
                command=lambda eid=entry_id: self._delete_entry(eid)
            ).pack(side="left", padx=1)
    
    def _create_chart_section(self):
        """Create chart section."""
        section = ctk.CTkFrame(self.content, fg_color=COLORS["card_bg"], corner_radius=12)
        section.pack(fill="x", pady=(0, 15))
        
        inner = ctk.CTkFrame(section, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            inner, text="📊 Savings Evolution",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 15))
        
        self.chart_frame = ctk.CTkFrame(inner, fg_color=COLORS["bg"], corner_radius=8, height=300)
        self.chart_frame.pack(fill="x")
        self.chart_frame.pack_propagate(False)
        
        self._update_chart()
    
    def _update_chart(self):
        """Update the savings chart."""
        # Clear existing chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        entries = self.kid.get("totals", {}).get("entries", [])
        
        if not entries:
            ctk.CTkLabel(
                self.chart_frame,
                text="No data to display",
                text_color=COLORS["text_muted"]
            ).pack(expand=True)
            return
        
        sorted_entries = sorted(entries, key=lambda x: x["period"])
        
        labels = [PeriodHelper.format_period_short(e["period"]) for e in sorted_entries]
        
        cumulative_spent = []
        cumulative_given = []
        saved_data = []
        
        cum_spent = 0
        cum_given = 0
        
        for entry in sorted_entries:
            cum_spent += entry["spent"]
            cum_given += entry["given"]
            cumulative_spent.append(cum_spent)
            cumulative_given.append(cum_given)
            saved_data.append(entry.get("runningSaved", 0))
        
        # Create matplotlib figure
        fig = Figure(figsize=(8, 3), dpi=100)
        fig.patch.set_facecolor(COLORS["bg"])
        
        ax = fig.add_subplot(111)
        ax.set_facecolor(COLORS["bg"])
        
        ax.plot(labels, cumulative_spent, color=COLORS["spent"], 
                label="Cumulative Spent", linewidth=2, marker='o', markersize=4)
        ax.fill_between(labels, cumulative_spent, alpha=0.1, color=COLORS["spent"])
        
        ax.plot(labels, saved_data, color=COLORS["saved"],
                label="Total Saved", linewidth=2, marker='o', markersize=4)
        ax.fill_between(labels, saved_data, alpha=0.1, color=COLORS["saved"])
        
        ax.plot(labels, cumulative_given, color=COLORS["given"],
                label="Cumulative Given", linewidth=2, marker='o', markersize=4)
        ax.fill_between(labels, cumulative_given, alpha=0.1, color=COLORS["given"])
        
        ax.legend(loc='upper left', fontsize=8)
        ax.tick_params(axis='x', rotation=45, labelsize=7)
        ax.tick_params(axis='y', labelsize=8)
        ax.grid(True, alpha=0.3)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def _save_allocation(self):
        """Save allocation settings."""
        try:
            spent = float(self.alloc_vars["spent"].get())
            saved = float(self.alloc_vars["saved"].get())
            given = float(self.alloc_vars["given"].get())
            interest = float(self.alloc_vars["interest"].get())
            
            if abs(spent + saved + given - 100) > 0.01:
                self.alloc_error.configure(
                    text=f"Total must be 100% (currently {spent + saved + given:.1f}%)"
                )
                return
            
            self.alloc_error.configure(text="")
            
            self.dm.update_allocation(self.kid_id, spent, saved, given, interest)
            self.kid["allocation"] = {"spent": spent, "saved": saved, "given": given}
            self.kid["interestRate"] = interest
            
            messagebox.showinfo("Success", "Default allocation saved!")
        except ValueError:
            self.alloc_error.configure(text="Please enter valid numbers")
    
    def _add_entry(self):
        """Add a new entry."""
        try:
            amount = float(self.amount_var.get())
            if amount <= 0:
                messagebox.showerror("Error", "Please enter a valid amount")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
            return
        
        # Validate used from saved
        try:
            used_from_saved = float(self.used_from_saved_var.get() or 0)
            if used_from_saved < 0:
                messagebox.showerror("Error", "Used from Saved cannot be negative")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount for Used from Saved")
            return
        
        # Check available saved
        available_saved = self.kid.get("totals", {}).get("totalSaved", 0)
        if used_from_saved > available_saved:
            messagebox.showerror("Error", f"Cannot use more than available saved amount (€{available_saved:.2f})")
            return
        
        period_key = self.period_selector.get_period_key()
        period_type = self.period_selector.get_period_type()
        allocation = self.kid.get("allocation", {"spent": 40, "saved": 40, "given": 20})
        interest_rate = self.kid.get("interestRate", 0)
        
        result = self.dm.add_entry(
            self.kid_id, period_key, period_type, amount, interest_rate,
            allocation["spent"], allocation["saved"], allocation["given"],
            used_from_saved
        )
        
        if result is None:
            messagebox.showerror("Error", "Entry for this period already exists")
            return
        
        self.amount_var.set("")
        self.used_from_saved_var.set("0")
        self._refresh()
        messagebox.showinfo("Success", "Entry added!")
    
    def _edit_entry(self, entry_id: str):
        """Open edit entry dialog."""
        entries = self.kid.get("totals", {}).get("entries", [])
        
        # Find the entry and calculate available saved at that point
        sorted_entries = sorted(entries, key=lambda x: x["period"])
        available_saved_before = 0
        target_entry = None
        
        for entry in sorted_entries:
            if entry["id"] == entry_id:
                target_entry = entry
                break
            # Calculate running saved up to this point
            available_saved_before = entry.get("runningSaved", 0)
        
        if target_entry:
            EditEntryDialog(
                self, target_entry, self._save_entry_changes, 
                self.period_type, available_saved_before
            )
    
    def _save_entry_changes(self, entry_id: str, amount: float,
                           spent_pct: float, saved_pct: float,
                           given_pct: float, interest_rate: float,
                           used_from_saved: float = 0,
                           period: str = None, period_type: str = None):
        """Save entry changes from dialog."""
        result = self.dm.update_entry(
            self.kid_id, entry_id, amount,
            spent_pct, saved_pct, given_pct, interest_rate,
            used_from_saved, period, period_type
        )
        
        if not result:
            messagebox.showerror("Error", "Failed to update entry. Period may conflict with existing entry.")
            return
        
        self._refresh()
        messagebox.showinfo("Success", "Entry updated!")
    
    def _delete_entry(self, entry_id: str):
        """Delete an entry."""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this entry?"):
            self.dm.delete_entry(self.kid_id, entry_id)
            self._refresh()
            messagebox.showinfo("Success", "Entry deleted!")
    
    def _refresh(self):
        """Refresh the view."""
        self._load_kid()
        self._update_totals()
        self._render_entries()
        self._update_chart()
        
        # Update available saved label
        if hasattr(self, 'available_saved_label'):
            available_saved = self.kid.get("totals", {}).get("totalSaved", 0)
            self.available_saved_label.configure(text=f"(Available: €{available_saved:.2f})")
    
    def _update_totals(self):
        """Update totals display."""
        totals = self.kid.get("totals", {})
        for key, label in self.total_labels.items():
            value = totals.get(key, 0)
            label.configure(text=f"€{value:.2f}")


class MainApplication(ctk.CTk):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        self.title("💰 Pocket Money Tracker")
        self.geometry("1100x750")
        self.minsize(900, 650)
        
        self.dm = DataManager()
        self.current_view = None
        
        self._create_widgets()
        self._show_main_view()
    
    def _create_widgets(self):
        # Main container with gradient-like background
        self.main_container = ctk.CTkFrame(self, fg_color="#667eea", corner_radius=0)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Content frame
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True)
    
    def _show_main_view(self):
        """Show the main kids list view."""
        self._clear_content()
        
        # Header
        header = ctk.CTkFrame(self.content_frame, fg_color=COLORS["card_bg"], corner_radius=12)
        header.pack(fill="x", pady=(0, 15))
        
        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            header_inner,
            text="💰 Pocket Money Tracker",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["primary"]
        ).pack(side="left")
        
        # Settings
        settings_frame = ctk.CTkFrame(header_inner, fg_color="transparent")
        settings_frame.pack(side="right")
        
        ctk.CTkLabel(settings_frame, text="Default Period:").pack(side="left", padx=(0, 10))
        
        settings = self.dm.get_settings()
        self.period_var = ctk.StringVar(value=settings.get("period", "monthly"))
        
        period_menu = ctk.CTkOptionMenu(
            settings_frame,
            values=["weekly", "biweekly", "monthly", "quarterly"],
            variable=self.period_var,
            command=self._on_period_change,
            width=120
        )
        period_menu.pack(side="left")
        
        ctk.CTkLabel(
            settings_frame, text="Currency: EUR",
            text_color=COLORS["text_muted"]
        ).pack(side="left", padx=(15, 0))
        
        # Kids management section
        section = ctk.CTkFrame(self.content_frame, fg_color=COLORS["card_bg"], corner_radius=12)
        section.pack(fill="both", expand=True)
        
        section_inner = ctk.CTkFrame(section, fg_color="transparent")
        section_inner.pack(fill="both", expand=True, padx=20, pady=15)
        
        ctk.CTkLabel(
            section_inner,
            text="👨‍👩‍👧‍👦 Manage Kids",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", pady=(0, 15))
        
        # Add kid form
        add_frame = ctk.CTkFrame(section_inner, fg_color="transparent")
        add_frame.pack(fill="x", pady=(0, 20))
        
        self.new_kid_var = ctk.StringVar()
        kid_entry = ctk.CTkEntry(
            add_frame,
            textvariable=self.new_kid_var,
            placeholder_text="Enter kid's name",
            width=300,
            height=40
        )
        kid_entry.pack(side="left", padx=(0, 10))
        kid_entry.bind("<Return>", lambda e: self._add_kid())
        
        ctk.CTkButton(
            add_frame, text="Add Kid", width=100, height=40,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=self._add_kid
        ).pack(side="left")
        
        # Kids list
        self.kids_frame = ctk.CTkScrollableFrame(section_inner, fg_color="transparent")
        self.kids_frame.pack(fill="both", expand=True)
        
        self._render_kids()
        
        # Footer
        footer = ctk.CTkLabel(
            self.content_frame,
            text="Pocket Money Tracker",
            text_color="white",
            font=ctk.CTkFont(size=11)
        )
        footer.pack(pady=10)
    
    def _render_kids(self):
        """Render the kids list."""
        for widget in self.kids_frame.winfo_children():
            widget.destroy()
        
        kids = self.dm.get_kids()
        
        if not kids:
            empty_frame = ctk.CTkFrame(self.kids_frame, fg_color="transparent")
            empty_frame.pack(fill="both", expand=True, pady=50)
            
            ctk.CTkLabel(
                empty_frame, text="👶",
                font=ctk.CTkFont(size=48)
            ).pack()
            
            ctk.CTkLabel(
                empty_frame,
                text="No kids added yet. Add your first kid above!",
                text_color=COLORS["text_muted"]
            ).pack(pady=10)
            return
        
        # Grid of kid cards
        row_frame = None
        for i, kid in enumerate(kids):
            if i % 3 == 0:
                row_frame = ctk.CTkFrame(self.kids_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=5)
                for col in range(3):
                    row_frame.grid_columnconfigure(col, weight=1)
            
            card = KidCard(
                row_frame, kid,
                on_select=self._select_kid,
                on_edit=self._edit_kid,
                on_delete=self._delete_kid
            )
            card.grid(row=0, column=i % 3, padx=5, pady=5, sticky="nsew")
    
    def _clear_content(self):
        """Clear the content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def _on_period_change(self, value: str):
        """Handle period change."""
        self.dm.update_settings({"period": value})
    
    def _add_kid(self):
        """Add a new kid."""
        name = self.new_kid_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a name")
            return
        
        self.dm.add_kid(name)
        self.new_kid_var.set("")
        self._render_kids()
        messagebox.showinfo("Success", f"{name} has been added!")
    
    def _select_kid(self, kid_id: str):
        """Select a kid to view details."""
        self._clear_content()
        
        details_view = KidDetailsView(
            self.content_frame, self.dm, kid_id,
            on_back=self._show_main_view,
            on_period_type_change=lambda v: self.period_var.set(v)
        )
        details_view.pack(fill="both", expand=True)
    
    def _edit_kid(self, kid_id: str, name: str):
        """Edit a kid's name."""
        dialog = ctk.CTkInputDialog(
            text="Enter new name:",
            title="Edit Kid's Name"
        )
        new_name = dialog.get_input()
        
        if new_name and new_name.strip():
            self.dm.update_kid(kid_id, new_name.strip())
            self._render_kids()
            messagebox.showinfo("Success", "Name updated!")
    
    def _delete_kid(self, kid_id: str, name: str):
        """Delete a kid."""
        if messagebox.askyesno(
            "Confirm Delete",
            f'Are you sure you want to delete "{name}"?\nAll their data will be lost.'
        ):
            self.dm.delete_kid(kid_id)
            self._render_kids()
            messagebox.showinfo("Success", "Kid removed successfully")


def main():
    """Main entry point."""
    app = MainApplication()
    app.mainloop()


if __name__ == "__main__":
    main()