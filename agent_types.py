"""
Core types and data models for super-intelligent human-like agent
"""
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json
import uuid

class AgentMode(Enum):
    RUNNING = "RUNNING"
    NEEDS_INFO = "NEEDS_INFO"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class SlotType(Enum):
    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    ENUM = "enum"
    URL = "url"
    EMAIL = "email"
    CURRENCY = "currency"
    BOOLEAN = "boolean"
    LIST = "list"

@dataclass
class Slot:
    """A slot represents a piece of information the agent needs"""
    id: str
    label: str
    type: SlotType
    required: bool = True
    enum_values: Optional[List[str]] = None
    value: Optional[Any] = None
    reason: Optional[str] = None  # why this slot is needed
    validator: Optional[str] = None  # regex or validation rule
    placeholder: Optional[str] = None
    help_text: Optional[str] = None

@dataclass
class TaskSpec:
    """Complete task specification with slots and plan"""
    id: str
    goal: str  # natural language objective
    slots: List[Slot]  # structured inputs the task needs
    plan_json: Optional[Dict[str, Any]] = None  # compiled plan/graph
    cursor: Optional[str] = None  # where we left off in the plan
    created_at: datetime = None
    updated_at: datetime = None

@dataclass
class NeedInfo:
    """Information needed from user"""
    task_id: str
    question: str  # one crisp question
    slot_id: str  # which slot it will fill
    suggestions: Optional[List[str]] = None  # quick reply options
    details: Optional[str] = None  # helpful context, constraints
    slot: Optional[Slot] = None

@dataclass
class AgentState:
    """Current state of the agent"""
    task: TaskSpec
    mode: AgentMode
    issues: List[str] = None
    last_updated_at: datetime = None
    need_info: Optional[NeedInfo] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.last_updated_at is None:
            self.last_updated_at = datetime.now()

@dataclass
class Checkpoint:
    """Checkpoint for state persistence"""
    id: str
    task_id: str
    snapshot: Dict[str, Any]
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class ExecutionResult:
    """Result of executing a step"""
    step_id: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class TaskTemplate:
    """Template for common task types"""
    
    @staticmethod
    def create_flight_booking_task() -> TaskSpec:
        """Create a flight booking task template"""
        slots = [
            Slot(
                id="trip.origin",
                label="Departure City",
                type=SlotType.STRING,
                required=True,
                reason="Need to know where you're flying from",
                placeholder="e.g., New York, London, Tokyo"
            ),
            Slot(
                id="trip.destination", 
                label="Destination City",
                type=SlotType.STRING,
                required=True,
                reason="Need to know where you're flying to",
                placeholder="e.g., Paris, Sydney, Dubai"
            ),
            Slot(
                id="trip.departure_date",
                label="Departure Date",
                type=SlotType.DATE,
                required=True,
                reason="Need to know when you want to travel",
                placeholder="YYYY-MM-DD format"
            ),
            Slot(
                id="trip.return_date",
                label="Return Date",
                type=SlotType.DATE,
                required=False,
                reason="For round-trip flights",
                placeholder="YYYY-MM-DD format (optional)"
            ),
            Slot(
                id="trip.passengers",
                label="Number of Passengers",
                type=SlotType.NUMBER,
                required=True,
                reason="Need to know how many tickets to book",
                enum_values=["1", "2", "3", "4", "5", "6"]
            ),
            Slot(
                id="trip.cabin_class",
                label="Cabin Class",
                type=SlotType.ENUM,
                required=True,
                reason="Different classes have different prices",
                enum_values=["Economy", "Premium Economy", "Business", "First"]
            ),
            Slot(
                id="trip.budget",
                label="Budget (Optional)",
                type=SlotType.CURRENCY,
                required=False,
                reason="To find flights within your budget",
                placeholder="e.g., 500 USD, 1000 EUR"
            )
        ]
        
        return TaskSpec(
            id=str(uuid.uuid4()),
            goal="Book a flight",
            slots=slots,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    @staticmethod
    def create_research_task() -> TaskSpec:
        """Create a research task template"""
        slots = [
            Slot(
                id="research.topic",
                label="Research Topic",
                type=SlotType.STRING,
                required=True,
                reason="Need to know what to research",
                placeholder="e.g., artificial intelligence trends, renewable energy"
            ),
            Slot(
                id="research.depth",
                label="Research Depth",
                type=SlotType.ENUM,
                required=True,
                reason="Determines how thorough the research should be",
                enum_values=["Brief", "Moderate", "Comprehensive"]
            ),
            Slot(
                id="research.format",
                label="Output Format",
                type=SlotType.ENUM,
                required=True,
                reason="How you want the research presented",
                enum_values=["Summary", "Detailed Report", "Bullet Points", "Presentation"]
            ),
            Slot(
                id="research.deadline",
                label="Deadline (Optional)",
                type=SlotType.DATE,
                required=False,
                reason="When you need the research completed",
                placeholder="YYYY-MM-DD format"
            ),
            Slot(
                id="research.sources",
                label="Preferred Sources",
                type=SlotType.LIST,
                required=False,
                reason="Specific sources or types of sources to focus on",
                placeholder="e.g., academic papers, news articles, industry reports"
            )
        ]
        
        return TaskSpec(
            id=str(uuid.uuid4()),
            goal="Conduct research",
            slots=slots,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    @staticmethod
    def create_web_automation_task() -> TaskSpec:
        """Create a web automation task template"""
        slots = [
            Slot(
                id="automation.url",
                label="Target Website",
                type=SlotType.URL,
                required=True,
                reason="Need to know which website to automate",
                placeholder="https://example.com"
            ),
            Slot(
                id="automation.action",
                label="Action to Perform",
                type=SlotType.ENUM,
                required=True,
                reason="What action should be performed on the website",
                enum_values=["Scrape Data", "Fill Form", "Click Elements", "Monitor Changes", "Download Files"]
            ),
            Slot(
                id="automation.target",
                label="Target Element/Data",
                type=SlotType.STRING,
                required=True,
                reason="What specific element or data to interact with",
                placeholder="e.g., product prices, contact form, download button"
            ),
            Slot(
                id="automation.schedule",
                label="Schedule (Optional)",
                type=SlotType.ENUM,
                required=False,
                reason="How often to run the automation",
                enum_values=["Once", "Daily", "Weekly", "Monthly"]
            ),
            Slot(
                id="automation.notify",
                label="Notification Method",
                type=SlotType.ENUM,
                required=False,
                reason="How to notify you of results",
                enum_values=["Email", "Slack", "None"]
            )
        ]
        
        return TaskSpec(
            id=str(uuid.uuid4()),
            goal="Automate web task",
            slots=slots,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

def create_task_from_goal(goal: str) -> TaskSpec:
    """Create a task specification from a natural language goal"""
    goal_lower = goal.lower()
    
    # Flight booking
    if any(word in goal_lower for word in ["flight", "book flight", "airline", "travel", "trip"]):
        return TaskTemplate.create_flight_booking_task()
    
    # Research
    elif any(word in goal_lower for word in ["research", "study", "investigate", "analyze", "find information"]):
        return TaskTemplate.create_research_task()
    
    # Web automation
    elif any(word in goal_lower for word in ["automate", "scrape", "crawl", "website", "web"]):
        return TaskTemplate.create_web_automation_task()
    
    # Default generic task
    else:
        slots = [
            Slot(
                id="task.details",
                label="Task Details",
                type=SlotType.STRING,
                required=True,
                reason="Need more details to understand what you want to accomplish",
                placeholder="Please provide more specific details about your request"
            ),
            Slot(
                id="task.priority",
                label="Priority Level",
                type=SlotType.ENUM,
                required=False,
                reason="To prioritize your task appropriately",
                enum_values=["Low", "Medium", "High", "Urgent"]
            )
        ]
        
        return TaskSpec(
            id=str(uuid.uuid4()),
            goal=goal,
            slots=slots,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
