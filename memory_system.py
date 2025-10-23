"""
Advanced Memory and Learning System for Super-Intelligent Agent
"""
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib
import pickle
import os
from collections import defaultdict, deque

@dataclass
class MemoryEntry:
    """Individual memory entry with context and metadata"""
    id: str
    content: str
    context: Dict[str, Any]
    timestamp: datetime
    importance: float
    access_count: int
    last_accessed: datetime
    tags: List[str]
    relationships: List[str]
    confidence: float

@dataclass
class LearningPattern:
    """Learning pattern for adaptive behavior"""
    pattern_id: str
    input_pattern: Dict[str, Any]
    successful_output: Dict[str, Any]
    failure_patterns: List[Dict[str, Any]]
    success_rate: float
    usage_count: int
    last_updated: datetime
    confidence: float

class MemorySystem:
    """
    Advanced memory system with learning capabilities
    """
    
    def __init__(self, memory_file: str = "agent_memory.json"):
        self.logger = logging.getLogger(__name__)
        self.memory_file = memory_file
        self.memories: Dict[str, MemoryEntry] = {}
        self.learning_patterns: Dict[str, LearningPattern] = {}
        self.context_graph: Dict[str, List[str]] = defaultdict(list)
        self.access_patterns: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Load existing memory
        self._load_memory()
    
    def _load_memory(self):
        """Load memory from persistent storage"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Load memories
                for memory_id, memory_data in data.get('memories', {}).items():
                    memory_data['timestamp'] = datetime.fromisoformat(memory_data['timestamp'])
                    memory_data['last_accessed'] = datetime.fromisoformat(memory_data['last_accessed'])
                    self.memories[memory_id] = MemoryEntry(**memory_data)
                
                # Load learning patterns
                for pattern_id, pattern_data in data.get('patterns', {}).items():
                    pattern_data['last_updated'] = datetime.fromisoformat(pattern_data['last_updated'])
                    self.learning_patterns[pattern_id] = LearningPattern(**pattern_data)
                
                self.logger.info(f"Loaded {len(self.memories)} memories and {len(self.learning_patterns)} patterns")
        except Exception as e:
            self.logger.error(f"Error loading memory: {e}")
    
    def _save_memory(self):
        """Save memory to persistent storage"""
        try:
            data = {
                'memories': {},
                'patterns': {},
                'last_saved': datetime.now().isoformat()
            }
            
            # Save memories
            for memory_id, memory in self.memories.items():
                memory_dict = asdict(memory)
                memory_dict['timestamp'] = memory.timestamp.isoformat()
                memory_dict['last_accessed'] = memory.last_accessed.isoformat()
                data['memories'][memory_id] = memory_dict
            
            # Save learning patterns
            for pattern_id, pattern in self.learning_patterns.items():
                pattern_dict = asdict(pattern)
                pattern_dict['last_updated'] = pattern.last_updated.isoformat()
                data['patterns'][pattern_id] = pattern_dict
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error saving memory: {e}")
    
    async def store_memory(self, content: str, context: Dict[str, Any], importance: float = 0.5, tags: Optional[List[str]] = None) -> str:
        """Store a new memory entry"""
        memory_id = self._generate_memory_id(content, context)
        
        memory_entry = MemoryEntry(
            id=memory_id,
            content=content,
            context=context or {},
            timestamp=datetime.now(),
            importance=importance,
            access_count=0,
            last_accessed=datetime.now(),
            tags=tags or [],
            relationships=[],
            confidence=0.8
        )
        
        self.memories[memory_id] = memory_entry
        
        # Update context graph
        for tag in memory_entry.tags:
            self.context_graph[tag].append(memory_id)
        
        # Auto-save important memories
        if importance > 0.7:
            self._save_memory()
        
        self.logger.info(f"Stored memory: {memory_id}")
        return memory_id
    
    async def retrieve_memories(self, query: str, context: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[MemoryEntry]:
        """Retrieve relevant memories based on query and context"""
        query_lower = query.lower()
        relevant_memories = []
        
        for memory in self.memories.values():
            relevance_score = self._calculate_relevance(memory, query_lower, context or {})
            if relevance_score > 0.3:  # Threshold for relevance
                relevant_memories.append((memory, relevance_score))
        
        # Sort by relevance and importance
        relevant_memories.sort(key=lambda x: x[1] * x[0].importance, reverse=True)
        
        # Update access patterns
        for memory, _ in relevant_memories[:limit]:
            memory.access_count += 1
            memory.last_accessed = datetime.now()
            self.access_patterns[memory.id].append(datetime.now())
        
        return [memory for memory, _ in relevant_memories[:limit]]
    
    def _calculate_relevance(self, memory: MemoryEntry, query: str, context: Dict[str, Any]) -> float:
        """Calculate relevance score for memory retrieval"""
        score = 0.0
        
        # Content similarity
        content_words = set(memory.content.lower().split())
        query_words = set(query.split())
        if content_words and query_words:
            content_similarity = len(content_words.intersection(query_words)) / len(query_words)
            score += content_similarity * 0.4
        
        # Tag matching
        for tag in memory.tags:
            if tag.lower() in query:
                score += 0.3
        
        # Context similarity
        if context:
            context_similarity = self._calculate_context_similarity(memory.context, context)
            score += context_similarity * 0.2
        
        # Recency boost
        days_old = (datetime.now() - memory.timestamp).days
        if days_old < 7:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_context_similarity(self, memory_context: Dict[str, Any], query_context: Dict[str, Any]) -> float:
        """Calculate similarity between contexts"""
        if not memory_context or not query_context:
            return 0.0
        
        common_keys = set(memory_context.keys()).intersection(set(query_context.keys()))
        if not common_keys:
            return 0.0
        
        similarities = []
        for key in common_keys:
            if isinstance(memory_context[key], str) and isinstance(query_context[key], str):
                if memory_context[key].lower() == query_context[key].lower():
                    similarities.append(1.0)
                else:
                    similarities.append(0.0)
            elif memory_context[key] == query_context[key]:
                similarities.append(1.0)
            else:
                similarities.append(0.0)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _generate_memory_id(self, content: str, context: Dict[str, Any]) -> str:
        """Generate unique memory ID"""
        combined = f"{content}_{json.dumps(context, sort_keys=True)}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]
    
    async def learn_from_interaction(self, input_data: Dict[str, Any], output_data: Dict[str, Any], success: bool):
        """Learn from user interactions"""
        pattern_id = self._generate_pattern_id(input_data)
        
        if pattern_id in self.learning_patterns:
            pattern = self.learning_patterns[pattern_id]
            
            if success:
                pattern.success_rate = (pattern.success_rate * pattern.usage_count + 1.0) / (pattern.usage_count + 1)
                pattern.successful_output = output_data
            else:
                pattern.failure_patterns.append(output_data)
                pattern.success_rate = (pattern.success_rate * pattern.usage_count) / (pattern.usage_count + 1)
            
            pattern.usage_count += 1
            pattern.last_updated = datetime.now()
        else:
            # Create new pattern
            pattern = LearningPattern(
                pattern_id=pattern_id,
                input_pattern=input_data,
                successful_output=output_data if success else {},
                failure_patterns=[output_data] if not success else [],
                success_rate=1.0 if success else 0.0,
                usage_count=1,
                last_updated=datetime.now(),
                confidence=0.8
            )
            
            self.learning_patterns[pattern_id] = pattern
        
        # Auto-save learning patterns
        if len(self.learning_patterns) % 10 == 0:
            self._save_memory()
    
    def _generate_pattern_id(self, input_data: Dict[str, Any]) -> str:
        """Generate pattern ID from input data"""
        # Normalize input data for pattern matching
        normalized = {}
        for key, value in input_data.items():
            if isinstance(value, str):
                normalized[key] = value.lower()
            else:
                normalized[key] = value
        
        return hashlib.md5(json.dumps(normalized, sort_keys=True).encode()).hexdigest()[:16]
    
    async def get_learned_response(self, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get learned response based on input pattern"""
        pattern_id = self._generate_pattern_id(input_data)
        
        if pattern_id in self.learning_patterns:
            pattern = self.learning_patterns[pattern_id]
            
            # Only return if success rate is high enough
            if pattern.success_rate > 0.7:
                return {
                    "response": pattern.successful_output,
                    "confidence": pattern.success_rate,
                    "pattern_id": pattern_id
                }
        
        return None
    
    async def get_contextual_suggestions(self, current_context: Dict[str, Any]) -> List[str]:
        """Get contextual suggestions based on memory and patterns"""
        suggestions = []
        
        # Find similar contexts in memory
        similar_memories = []
        for memory in self.memories.values():
            similarity = self._calculate_context_similarity(memory.context, current_context)
            if similarity > 0.5:
                similar_memories.append((memory, similarity))
        
        # Sort by similarity and importance
        similar_memories.sort(key=lambda x: x[1] * x[0].importance, reverse=True)
        
        # Generate suggestions from similar memories
        for memory, similarity in similar_memories[:5]:
            if memory.content not in suggestions:
                suggestions.append(memory.content)
        
        # Get suggestions from learning patterns
        for pattern in self.learning_patterns.values():
            if pattern.success_rate > 0.8:
                context_similarity = self._calculate_context_similarity(
                    pattern.input_pattern, current_context
                )
                if context_similarity > 0.6:
                    suggestion = f"Based on previous success: {pattern.successful_output}"
                    if suggestion not in suggestions:
                        suggestions.append(suggestion)
        
        return suggestions[:10]  # Limit to 10 suggestions
    
    async def cleanup_old_memories(self, days_threshold: int = 30):
        """Clean up old, unimportant memories"""
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        
        memories_to_remove = []
        for memory_id, memory in self.memories.items():
            if (memory.timestamp < cutoff_date and 
                memory.importance < 0.3 and 
                memory.access_count < 5):
                memories_to_remove.append(memory_id)
        
        for memory_id in memories_to_remove:
            del self.memories[memory_id]
        
        if memories_to_remove:
            self.logger.info(f"Cleaned up {len(memories_to_remove)} old memories")
            self._save_memory()
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """Get statistics about the memory system"""
        total_memories = len(self.memories)
        total_patterns = len(self.learning_patterns)
        
        if not total_memories:
            return {"total_memories": 0, "total_patterns": 0}
        
        # Calculate average importance
        avg_importance = sum(m.importance for m in self.memories.values()) / total_memories
        
        # Calculate memory age distribution
        now = datetime.now()
        age_distribution = {
            "last_hour": 0,
            "last_day": 0,
            "last_week": 0,
            "last_month": 0,
            "older": 0
        }
        
        for memory in self.memories.values():
            age = now - memory.timestamp
            if age.total_seconds() < 3600:
                age_distribution["last_hour"] += 1
            elif age.days < 1:
                age_distribution["last_day"] += 1
            elif age.days < 7:
                age_distribution["last_week"] += 1
            elif age.days < 30:
                age_distribution["last_month"] += 1
            else:
                age_distribution["older"] += 1
        
        # Calculate pattern success rates
        if total_patterns:
            avg_success_rate = sum(p.success_rate for p in self.learning_patterns.values()) / total_patterns
        else:
            avg_success_rate = 0.0
        
        return {
            "total_memories": total_memories,
            "total_patterns": total_patterns,
            "average_importance": avg_importance,
            "age_distribution": age_distribution,
            "average_success_rate": avg_success_rate,
            "memory_file_size": os.path.getsize(self.memory_file) if os.path.exists(self.memory_file) else 0
        }
    
    async def export_memory(self, filepath: str):
        """Export memory system to file"""
        try:
            data = {
                'memories': {mid: asdict(mem) for mid, mem in self.memories.items()},
                'patterns': {pid: asdict(pat) for pid, pat in self.learning_patterns.items()},
                'export_timestamp': datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Memory exported to {filepath}")
        except Exception as e:
            self.logger.error(f"Error exporting memory: {e}")
    
    async def import_memory(self, filepath: str):
        """Import memory system from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Import memories
            for memory_id, memory_data in data.get('memories', {}).items():
                memory_data['timestamp'] = datetime.fromisoformat(memory_data['timestamp'])
                memory_data['last_accessed'] = datetime.fromisoformat(memory_data['last_accessed'])
                self.memories[memory_id] = MemoryEntry(**memory_data)
            
            # Import patterns
            for pattern_id, pattern_data in data.get('patterns', {}).items():
                pattern_data['last_updated'] = datetime.fromisoformat(pattern_data['last_updated'])
                self.learning_patterns[pattern_id] = LearningPattern(**pattern_data)
            
            self.logger.info(f"Memory imported from {filepath}")
            self._save_memory()
        except Exception as e:
            self.logger.error(f"Error importing memory: {e}")
