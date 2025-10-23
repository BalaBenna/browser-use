"""
Slot-first planning system for intelligent questioning
"""
import re
from typing import Optional, List, Any
from datetime import datetime, date
from agent_types import TaskSpec, Slot, NeedInfo, SlotType

class SlotPlanner:
    """Handles slot-based planning and intelligent questioning"""
    
    def __init__(self):
        self.validation_rules = {
            "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "url": r"^https?://.+\..+",
            "phone": r"^\+?[\d\s\-\(\)]+$",
            "date": r"^\d{4}-\d{2}-\d{2}$"
        }
    
    def find_blocking_slot(self, task: TaskSpec) -> Optional[NeedInfo]:
        """
        Find the next blocking slot that needs information.
        Priority: required & empty → ambiguous → invalid
        """
        # First priority: required slots that are empty
        missing_slot = self._find_missing_required_slot(task)
        if missing_slot:
            return self._create_need_info(task, missing_slot)
        
        # Second priority: slots with ambiguous values
        ambiguous_slot = self._find_ambiguous_slot(task)
        if ambiguous_slot:
            return self._create_need_info(task, ambiguous_slot)
        
        # Third priority: slots with invalid values
        invalid_slot = self._find_invalid_slot(task)
        if invalid_slot:
            return self._create_need_info(task, invalid_slot)
        
        return None
    
    def _find_missing_required_slot(self, task: TaskSpec) -> Optional[Slot]:
        """Find required slots that are missing values"""
        for slot in task.slots:
            if slot.required and self._is_empty_value(slot.value):
                return slot
        return None
    
    def _find_ambiguous_slot(self, task: TaskSpec) -> Optional[Slot]:
        """Find slots with ambiguous values that need clarification"""
        for slot in task.slots:
            if slot.value and self._is_ambiguous_value(slot.value, slot.type):
                return slot
        return None
    
    def _find_invalid_slot(self, task: TaskSpec) -> Optional[Slot]:
        """Find slots with invalid values"""
        for slot in task.slots:
            if slot.value and not self._is_valid_value(slot.value, slot.type, slot.validator):
                return slot
        return None
    
    def _is_empty_value(self, value: Any) -> bool:
        """Check if a value is considered empty"""
        return value is None or value == "" or value == [] or value == {}
    
    def _is_ambiguous_value(self, value: Any, slot_type: SlotType) -> bool:
        """Check if a value is ambiguous and needs clarification"""
        if slot_type == SlotType.DATE:
            # Check if date is in the past
            try:
                if isinstance(value, str):
                    parsed_date = datetime.strptime(value, "%Y-%m-%d").date()
                    return parsed_date < date.today()
            except ValueError:
                return True
        
        elif slot_type == SlotType.NUMBER:
            # Check if number is reasonable
            try:
                num = float(value)
                return num <= 0 or num > 1000000  # Unreasonable range
            except (ValueError, TypeError):
                return True
        
        elif slot_type == SlotType.STRING:
            # Check if string is too short or generic
            if isinstance(value, str):
                return len(value.strip()) < 2 or value.lower() in ["yes", "no", "ok", "sure"]
        
        return False
    
    def _is_valid_value(self, value: Any, slot_type: SlotType, validator: Optional[str] = None) -> bool:
        """Validate a value against its type and custom validator"""
        try:
            if validator and validator in self.validation_rules:
                if not re.match(self.validation_rules[validator], str(value)):
                    return False
            
            if slot_type == SlotType.EMAIL:
                return re.match(self.validation_rules["email"], str(value))
            elif slot_type == SlotType.URL:
                return re.match(self.validation_rules["url"], str(value))
            elif slot_type == SlotType.DATE:
                datetime.strptime(str(value), "%Y-%m-%d")
            elif slot_type == SlotType.NUMBER:
                float(value)
            elif slot_type == SlotType.ENUM and slot.enum_values:
                return str(value) in slot.enum_values
            
            return True
        except (ValueError, TypeError):
            return False
    
    def _create_need_info(self, task: TaskSpec, slot: Slot) -> NeedInfo:
        """Create a NeedInfo object for a slot"""
        return NeedInfo(
            task_id=task.id,
            slot_id=slot.id,
            question=self._make_question(slot),
            suggestions=self._suggest_quick_replies(slot),
            details=self._get_context_details(slot),
            slot=slot
        )
    
    def _make_question(self, slot: Slot) -> str:
        """Generate a human-like question for a slot"""
        base_question = f"What is the {slot.label.lower()}?"
        
        # Add context based on slot type
        if slot.type == SlotType.DATE:
            if "departure" in slot.id.lower():
                base_question = f"When would you like to {slot.label.lower().replace('date', '')}? (YYYY-MM-DD format)"
            elif "return" in slot.id.lower():
                base_question = f"When would you like to {slot.label.lower().replace('date', '')}? (YYYY-MM-DD format, optional)"
            else:
                base_question = f"What is the {slot.label.lower()}? (YYYY-MM-DD format)"
        
        elif slot.type == SlotType.ENUM:
            if slot.enum_values:
                options = ", ".join(slot.enum_values[:4])  # Show first 4 options
                if len(slot.enum_values) > 4:
                    options += f" (or {len(slot.enum_values) - 4} more options)"
                base_question = f"Choose {slot.label.lower()}: {options}"
        
        elif slot.type == SlotType.CURRENCY:
            base_question = f"What is your {slot.label.lower()}? (e.g., 500 USD, 1000 EUR)"
        
        elif slot.type == SlotType.URL:
            base_question = f"Please provide the {slot.label.lower()}. (must start with http:// or https://)"
        
        elif slot.type == SlotType.EMAIL:
            base_question = f"What is your {slot.label.lower()}?"
        
        elif slot.type == SlotType.NUMBER:
            if slot.enum_values:
                base_question = f"How many {slot.label.lower()}? (choose from: {', '.join(slot.enum_values)})"
            else:
                base_question = f"What is the {slot.label.lower()}? (enter a number)"
        
        # Add helpful context
        if slot.reason:
            base_question += f" ({slot.reason})"
        
        return base_question
    
    def _suggest_quick_replies(self, slot: Slot) -> Optional[List[str]]:
        """Generate quick reply suggestions for a slot"""
        if slot.type == SlotType.ENUM and slot.enum_values:
            return slot.enum_values[:4]  # Top 4 options
        
        elif slot.type == SlotType.DATE:
            today = date.today()
            suggestions = []
            for i in range(1, 8):  # Next 7 days
                future_date = today.replace(day=today.day + i)
                suggestions.append(future_date.strftime("%Y-%m-%d"))
            return suggestions[:3]  # Top 3 dates
        
        elif slot.type == SlotType.NUMBER and slot.enum_values:
            return slot.enum_values
        
        # Add smart suggestions based on common patterns
        elif slot.type == SlotType.STRING:
            if "city" in slot.id.lower() or "origin" in slot.id.lower() or "destination" in slot.id.lower():
                return ["New York", "London", "Tokyo", "Paris", "Sydney"]
            elif "topic" in slot.id.lower():
                return ["AI trends", "Climate change", "Market analysis", "Technology news"]
        
        return None
    
    def _get_context_details(self, slot: Slot) -> Optional[str]:
        """Get additional context details for a slot"""
        if slot.help_text:
            return slot.help_text
        
        # Generate context based on slot type and content
        if slot.type == SlotType.DATE:
            if "departure" in slot.id.lower():
                return "Departure date must be today or in the future"
            elif "return" in slot.id.lower():
                return "Return date should be after departure date (optional for one-way trips)"
        
        elif slot.type == SlotType.CURRENCY:
            return "Enter amount followed by currency code (e.g., 500 USD, 1000 EUR)"
        
        elif slot.type == SlotType.URL:
            return "Must be a valid URL starting with http:// or https://"
        
        elif slot.type == SlotType.EMAIL:
            return "Enter a valid email address"
        
        return None
    
    def fill_slot(self, task: TaskSpec, slot_id: str, value: Any) -> bool:
        """Fill a slot with a value and validate it"""
        slot = self._find_slot_by_id(task, slot_id)
        if not slot:
            return False
        
        # Validate the value
        if not self._is_valid_value(value, slot.type, slot.validator):
            return False
        
        # Set the value
        slot.value = value
        task.updated_at = datetime.now()
        
        return True
    
    def _find_slot_by_id(self, task: TaskSpec, slot_id: str) -> Optional[Slot]:
        """Find a slot by its ID"""
        for slot in task.slots:
            if slot.id == slot_id:
                return slot
        return None
    
    def get_filled_slots_summary(self, task: TaskSpec) -> str:
        """Get a summary of filled slots for context"""
        filled_slots = []
        for slot in task.slots:
            if slot.value and not self._is_empty_value(slot.value):
                filled_slots.append(f"{slot.label} = {slot.value}")
        
        if filled_slots:
            return "So far I have: " + ", ".join(filled_slots) + "."
        return ""
    
    def get_progress_summary(self, task: TaskSpec) -> dict:
        """Get progress summary for the task"""
        total_slots = len(task.slots)
        filled_slots = sum(1 for slot in task.slots if slot.value and not self._is_empty_value(slot.value))
        required_slots = sum(1 for slot in task.slots if slot.required)
        filled_required = sum(1 for slot in task.slots if slot.required and slot.value and not self._is_empty_value(slot.value))
        
        return {
            "total_slots": total_slots,
            "filled_slots": filled_slots,
            "required_slots": required_slots,
            "filled_required": filled_required,
            "completion_percentage": (filled_required / required_slots * 100) if required_slots > 0 else 100,
            "all_required_filled": filled_required >= required_slots
        }
