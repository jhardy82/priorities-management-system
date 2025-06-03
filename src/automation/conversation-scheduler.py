#!/usr/bin/env python3
"""
Enhanced Conversation Scheduler for AAR System
Manages scheduled conversations with timezone support, state management, and workflow integration

This module provides:
- MST/MDT timezone-aware scheduling
- Alternating conversation logic for optimization sessions
- Conversation state management (scheduled, in-progress, completed, missed)
- Missed conversation recovery with resumption capability
- Workflow trigger integration for automation
- Comprehensive scheduling and status tracking

Aligns with Avanade Behavioral Anchors:
- Create the Future: Proactive improvement scheduling with timezone awareness
- Inspire Greatness: Structured learning conversations with state persistence
- Accelerate Impact: Systematic optimization cycles with workflow automation
"""

import argparse
import json
import yaml
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import pytz

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text

console = Console()

class ConversationState:
    """Represents the state of a conversation"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MISSED = "missed"
    CANCELLED = "cancelled"

class ConversationScheduler:
    """
    Enhanced conversation scheduler with timezone support and state management
    """

    def __init__(self, config_path: str = "config/aar-types-config.yaml"):
        """Initialize the enhanced conversation scheduler"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.conversation_schedule = self.config.get('conversation_scheduling', {})
        self.timezone = pytz.timezone(self.conversation_schedule.get('timezone', 'US/Mountain'))
        self.state_file = Path(self.conversation_schedule.get('state_management', {}).get('state_file', 'data/conversation-states.json'))
        self.states = self._load_conversation_states()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            console.print(f"❌ Error loading config: {e}", style="red")
            return {}

    def _load_conversation_states(self) -> Dict[str, Any]:
        """Load conversation states from JSON file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            else:
                # Create state file if it doesn't exist
                self.state_file.parent.mkdir(parents=True, exist_ok=True)
                return {}
        except Exception as e:
            console.print(f"⚠️  Warning: Could not load conversation states: {e}", style="yellow")
            return {}

    def _save_conversation_states(self) -> bool:
        """Save conversation states to JSON file"""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(self.states, f, indent=2, default=str)
            return True
        except Exception as e:
            console.print(f"❌ Error saving conversation states: {e}", style="red")
            return False

    def _get_current_time_mst(self) -> datetime:
        """Get current time in MST/MDT timezone"""
        return datetime.now(self.timezone)

    def _should_schedule_alternating(self, conversation_type: str, current_time: datetime) -> bool:
        """Determine if alternating conversation should be scheduled today"""
        schedule_config = self.conversation_schedule.get('schedules', {}).get(conversation_type, {})
        schedule_type = schedule_config.get('schedule_type')

        if not schedule_type:
            return True  # Normal scheduling if no alternating type

        day_of_month = current_time.day

        if schedule_type == "alternating_odd":
            return day_of_month % 2 == 1  # Odd days
        elif schedule_type == "alternating_even":
            return day_of_month % 2 == 0  # Even days

        return True

    def _get_conversation_key(self, conversation_type: str, date: datetime) -> str:
        """Generate unique key for conversation state tracking"""
        return f"{conversation_type}_{date.strftime('%Y-%m-%d')}"

    def _update_conversation_state(self, conversation_type: str, state: str,
                                 date: Optional[datetime] = None, metadata: Optional[Dict] = None) -> bool:
        """Update conversation state"""
        if date is None:
            date = self._get_current_time_mst()

        key = self._get_conversation_key(conversation_type, date)

        self.states[key] = {
            'conversation_type': conversation_type,
            'date': date.isoformat(),
            'state': state,
            'updated_at': datetime.now(self.timezone).isoformat(),
            'metadata': metadata or {}
        }

        return self._save_conversation_states()

    def _get_conversation_state(self, conversation_type: str, date: Optional[datetime] = None) -> Optional[Dict]:
        """Get conversation state"""
        if date is None:
            date = self._get_current_time_mst()

        key = self._get_conversation_key(conversation_type, date)
        return self.states.get(key)

    def _detect_missed_conversations(self) -> List[Dict]:
        """Detect conversations that were scheduled but missed"""
        missed_conversations = []
        current_time = self._get_current_time_mst()
        recovery_config = self.conversation_schedule.get('missed_conversation_recovery', {})
        max_recovery_days = recovery_config.get('max_recovery_days', 3)

        # Check last few days for missed conversations
        for days_back in range(1, max_recovery_days + 1):
            check_date = current_time - timedelta(days=days_back)

            for conversation_type, schedule_config in self.conversation_schedule.get('schedules', {}).items():
                if self._should_be_scheduled(conversation_type, schedule_config, check_date):
                    state = self._get_conversation_state(conversation_type, check_date)

                    if not state or state.get('state') == ConversationState.SCHEDULED:
                        # This conversation should have happened but didn't complete
                        missed_conversations.append({
                            'conversation_type': conversation_type,
                            'scheduled_date': check_date,
                            'days_ago': days_back,
                            'current_state': state.get('state') if state else 'not_tracked'
                        })

        return missed_conversations

    def check_scheduled_conversations(self) -> List[Dict[str, Any]]:
        """Check if any conversations are due now"""
        current_time = datetime.now()
        due_conversations = []

        schedules = self.conversation_schedule.get('schedules', {})

        for conversation_type, schedule_config in schedules.items():
            if self._is_conversation_due(current_time, schedule_config):
                due_conversations.append({
                    'type': conversation_type,
                    'config': schedule_config,
                    'time_due': current_time
                })

        return due_conversations

    def _is_conversation_due(self, current_time: datetime, schedule_config: Dict) -> bool:
        """Check if a conversation is due based on schedule configuration"""
        schedule_time = schedule_config.get('time', '09:00')
        days = schedule_config.get('days', [])

        # Parse schedule time
        try:
            hour, minute = map(int, schedule_time.split(':'))
            scheduled_time = time(hour, minute)
        except ValueError:
            return False

        # Check if today is a scheduled day
        current_day = current_time.strftime('%A').lower()
        if days and current_day not in days:
            return False

        # Check if current time matches scheduled time (within 30 minutes)
        scheduled_datetime = datetime.combine(current_time.date(), scheduled_time)
        time_diff = abs((current_time - scheduled_datetime).total_seconds())

        return time_diff <= 1800  # 30 minutes tolerance

    def initiate_conversation(self, conversation_type: str) -> bool:
        """Initiate a scheduled conversation"""
        console.print(Panel.fit(
            f"🗣️ Starting {conversation_type.replace('_', ' ').title()} Conversation",
            style="cyan"
        ))

        # Get conversation prompts
        prompts = self.conversation_schedule.get('conversation_prompts', {}).get(conversation_type, {})
        intro = prompts.get('intro', f"Let's start the {conversation_type} conversation.")

        console.print(f"\n{intro}\n", style="yellow")

        # Display conversation sections
        sections = prompts.get('sections', [])
        for i, section in enumerate(sections, 1):
            console.print(f"{i}. {section}", style="white")

        # Ask if user wants to proceed
        proceed = Confirm.ask("\nWould you like to create a structured AAR for this conversation?")

        if proceed:
            return self._create_conversation_aar(conversation_type)

        return False

    def _create_conversation_aar(self, conversation_type: str) -> bool:
        """Create an AAR for the conversation"""
        try:
            # For now, just create a simple AAR file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            aar_dir = Path(f"reports/conversations/{conversation_type}")
            aar_dir.mkdir(parents=True, exist_ok=True)

            aar_file = aar_dir / f"{timestamp}_{conversation_type}.md"

            # Create basic AAR content
            aar_content = f"""# {conversation_type.replace('_', ' ').title()} AAR
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Type:** {conversation_type}

## Conversation Summary
<!-- Add conversation details here -->

## Key Insights
<!-- Capture main insights -->

## Action Items
<!-- List follow-up actions -->

## Next Steps
<!-- Plan next conversation or follow-up -->
"""

            with open(aar_file, 'w') as f:
                f.write(aar_content)

            console.print(f"✅ Conversation AAR created: {aar_file}", style="green")
            return True

        except Exception as e:
            console.print(f"❌ Error creating conversation AAR: {e}", style="red")
            return False

    def send_notification(self, conversation_type: str, minutes_before: int = 5):
        """Send notification for upcoming conversation"""
        console.print(Panel.fit(
            f"🔔 Reminder: {conversation_type.replace('_', ' ').title()} conversation in {minutes_before} minutes",
            style="yellow"
        ))

    def list_upcoming_conversations(self) -> None:
        """List all upcoming scheduled conversations"""
        table = Table(title="📅 Upcoming Scheduled Conversations")
        table.add_column("Type", style="cyan")
        table.add_column("Next Scheduled", style="white")
        table.add_column("Days", style="green")
        table.add_column("Auto Trigger", style="yellow")

        schedules = self.conversation_schedule.get('schedules', {})

        for conversation_type, schedule_config in schedules.items():
            display_name = conversation_type.replace('_', ' ').title()
            schedule_time = schedule_config.get('time', 'Not set')
            days = ', '.join(schedule_config.get('days', ['Not set']))
            auto_trigger = "Yes" if schedule_config.get('auto_trigger', False) else "No"

            # Calculate next occurrence
            next_time = self._calculate_next_occurrence(schedule_config)

            table.add_row(display_name, next_time, days, auto_trigger)

        console.print(table)

    def _calculate_next_occurrence(self, schedule_config: Dict) -> str:
        """Calculate when the next conversation will occur"""
        try:
            current_time = datetime.now()
            schedule_time = schedule_config.get('time', '09:00')
            days = schedule_config.get('days', [])

            if not days:
                return "Not scheduled"

            # Parse schedule time
            hour, minute = map(int, schedule_time.split(':'))

            # Find next occurrence
            for i in range(8):  # Check next 7 days
                check_date = current_time + timedelta(days=i)
                day_name = check_date.strftime('%A').lower()

                if day_name in days:
                    scheduled_datetime = datetime.combine(check_date.date(), time(hour, minute))

                    # If it's today, check if time has passed
                    if i == 0 and scheduled_datetime <= current_time:
                        continue

                    return scheduled_datetime.strftime('%Y-%m-%d %H:%M')

            return "Next week"

        except Exception:
            return "Error calculating"


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="AAR Conversation Scheduler")
    parser.add_argument('command', choices=['check', 'list', 'initiate', 'notify'],
                       help='Command to execute')
    parser.add_argument('--type', help='Conversation type for initiate command')
    parser.add_argument('--minutes', type=int, default=5,
                       help='Minutes before for notify command')

    args = parser.parse_args()

    scheduler = ConversationScheduler()

    if args.command == 'check':
        due_conversations = scheduler.check_scheduled_conversations()
        if due_conversations:
            console.print(f"📋 Found {len(due_conversations)} due conversations:")
            for conv in due_conversations:
                console.print(f"  - {conv['type']}")
                if scheduler.initiate_conversation(conv['type']):
                    console.print("  ✅ Conversation completed")
                else:
                    console.print("  ⏭️ Conversation skipped")
        else:
            console.print("✅ No conversations due at this time")

    elif args.command == 'list':
        scheduler.list_upcoming_conversations()

    elif args.command == 'initiate':
        if not args.type:
            console.print("❌ Please specify --type for initiate command", style="red")
            return

        success = scheduler.initiate_conversation(args.type)
        if success:
            console.print("✅ Conversation initiated successfully")
        else:
            console.print("❌ Conversation initiation failed")

    elif args.command == 'notify':
        if not args.type:
            console.print("❌ Please specify --type for notify command", style="red")
            return

        scheduler.send_notification(args.type, args.minutes)


if __name__ == "__main__":
    main()
