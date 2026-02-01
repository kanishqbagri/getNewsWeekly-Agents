import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, List

class Storage:
    """File-based storage with versioning"""
    
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create storage directories if they don't exist"""
        (self.base_path / "raw").mkdir(parents=True, exist_ok=True)
        (self.base_path / "processed").mkdir(parents=True, exist_ok=True)
        (self.base_path / "approved").mkdir(parents=True, exist_ok=True)
        (self.base_path / "archives").mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep files
        for dir_path in [self.base_path / "raw", self.base_path / "processed", self.base_path / "approved", self.base_path / "archives"]:
            (dir_path / ".gitkeep").touch(exist_ok=True)
    
    def save_raw(self, data: Any, category: str, date: datetime = None):
        """Save raw scraped data"""
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y-%m-%d")
        path = self.base_path / "raw" / date_str
        path.mkdir(parents=True, exist_ok=True)
        
        filepath = path / f"{category}.json"
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def save_processed(self, data: Any, week_id: str):
        """Save processed weekly data"""
        filepath = self.base_path / "processed" / f"week-{week_id}.json"
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def load_processed(self, week_id: str) -> Dict:
        """Load processed weekly data"""
        filepath = self.base_path / "processed" / f"week-{week_id}.json"
        if not filepath.exists():
            return {}
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def save_approved(self, data: Any, week_id: str, format_type: str, extension: str = "json"):
        """Save approved content in various formats"""
        path = self.base_path / "approved" / f"week-{week_id}"
        path.mkdir(parents=True, exist_ok=True)
        
        filepath = path / f"{format_type}.{extension}"
        
        if extension == "json":
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif extension in ["html", "txt", "md"]:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(data))
        else:
            # Binary file
            with open(filepath, 'wb') as f:
                if isinstance(data, bytes):
                    f.write(data)
                else:
                    f.write(str(data).encode())
    
    def load_raw(self, category: str, date: datetime) -> Dict:
        """Load raw data for a specific date"""
        date_str = date.strftime("%Y-%m-%d")
        filepath = self.base_path / "raw" / date_str / f"{category}.json"
        
        if not filepath.exists():
            return {}
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def load_weekly_raw(self, start_date: datetime, end_date: datetime) -> Dict[str, List]:
        """Load all raw data for a week"""
        data = {}
        current = start_date
        
        while current <= end_date:
            date_str = current.strftime("%Y-%m-%d")
            day_path = self.base_path / "raw" / date_str
            
            if day_path.exists():
                for file in day_path.glob("*.json"):
                    category = file.stem
                    if category not in data:
                        data[category] = []
                    
                    with open(file, 'r') as f:
                        day_data = json.load(f)
                        if isinstance(day_data, list):
                            data[category].extend(day_data)
                        else:
                            data[category].append(day_data)
            
            current = current + timedelta(days=1)
        
        return data
    
    def get_archive_index(self) -> List[Dict]:
        """Get list of all archived weeks"""
        archives = []
        approved_path = self.base_path / "approved"
        
        if approved_path.exists():
            for week_dir in sorted(approved_path.glob("week-*"), reverse=True):
                week_id = week_dir.name.replace("week-", "")
                archives.append({
                    "week_id": week_id,
                    "path": str(week_dir)
                })
        
        return archives
