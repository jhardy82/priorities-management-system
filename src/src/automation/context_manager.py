#!/usr/bin/env python3
"""
Context Manager for AAR Auto-Update Protocol
Implements the SCF Context Object Pattern for Python

This module provides a Python implementation of the Scripted Collaboration Framework (SCF)
Context object pattern, enabling structured state tracking and error handling throughout
the application lifecycle.
"""

import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field


class Phase(str, Enum):
    """SCF execution phases."""

    DEVELOPMENT = "Development"
    TESTING = "Testing"
    PRODUCTION = "Production"


class OperationType(str, Enum):
    """Types of operations that can be performed."""

    ANALYSIS = "Analysis"
    UPDATE = "Update"
    VALIDATION = "Validation"
    REPORTING = "Reporting"


class SCFPhase(str, Enum):
    """The eight phases of the Scripted Collaboration Framework."""

    IDENTIFY_MISSION = "Identify Mission"
    GATHER_CONTEXT = "Gather Context"
    PROPOSE_SOLUTIONS = "Propose Solutions"
    SELECT_PLAN = "Select & Plan"
    EXECUTE_IMPLEMENT = "Execute & Implement"
    VALIDATE_VERIFY = "Validate & Verify"
    REVIEW_DOCUMENT = "Review & Document"
    TEST_REFINE = "Test & Refine"


class Context(BaseModel):
    """
    Context object for tracking state and errors throughout operations.

    This is the Python equivalent of the PowerShell Context object
    used in the Scripted Collaboration Framework.
    """

    timestamp: datetime = Field(default_factory=datetime.now)
    has_error: bool = False
    phase: Phase = Phase.DEVELOPMENT
    operation_type: Optional[OperationType] = None
    scf_phase: Optional[SCFPhase] = None
    error_message: Optional[str] = None
    results: Dict[str, Any] = Field(default_factory=dict)

    def log_checkpoint(self, checkpoint_name: str, message: str) -> None:
        """
        Log a checkpoint in the operation process.

        Args:
            checkpoint_name: Name/identifier for the checkpoint
            message: Description of the checkpoint state
        """
        logging.info(f"CHECKPOINT - {checkpoint_name}: {message}")

        if "checkpoints" not in self.results:
            self.results["checkpoints"] = []

        self.results["checkpoints"].append(
            {
                "name": checkpoint_name,
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "status": "ERROR" if self.has_error else "SUCCESS",
            }
        )

    def set_error(self, error_message: str) -> None:
        """
        Set the context to an error state with the specified message.

        Args:
            error_message: Description of the error
        """
        self.has_error = True
        self.error_message = error_message
        logging.error(f"Operation failed: {error_message}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to a dictionary."""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert context to a JSON string."""
        return self.model_dump_json(indent=2)

    def log_to_file(self, log_path: Union[str, Path]) -> None:
        """
        Log the context to a file in a structured format.

        Args:
            log_path: Path to the log file
        """
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Format for AAR logging
        log_entry = f"""## {datetime.now().strftime('%Y-%m-%d')}: {self.operation_type or 'Operation'} Execution

**SCF Phase**: {self.scf_phase or 'Execute & Implement'}
**Action**: {self.operation_type or 'Operation'} execution
**Outcome**: {"FAILURE" if self.has_error else "SUCCESS"}
**Details**:
- Execution Time: {self.timestamp.isoformat()}
- Phase: {self.phase}
"""

        if self.results.get("checkpoints"):
            log_entry += "- Checkpoints:\n"
            for cp in self.results["checkpoints"]:
                log_entry += f"  - {cp['name']}: {cp['status']}\n"

        if self.has_error:
            log_entry += f"- Error: {self.error_message}\n"

        log_entry += """
**Lessons**:
- Automatically captured execution details
- Structured logging provides clear outcomes

**Opportunities**:
- Enhance checkpoint tracking
- Add more detailed state tracking
"""

        with open(log_path, "a") as f:
            f.write(log_entry + "\n")

    @classmethod
    def load_from_json(cls, json_str: str) -> "Context":
        """
        Create a Context object from a JSON string.

        Args:
            json_str: JSON representation of the context

        Returns:
            Populated Context object
        """
        data = json.loads(json_str)
        # Convert string timestamp to datetime
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(
                data["timestamp"].replace("Z", "+00:00")
            )
        return cls(**data)


def create_context(
    operation_type: Optional[OperationType] = None,
    phase: Phase = Phase.DEVELOPMENT,
    scf_phase: Optional[SCFPhase] = SCFPhase.EXECUTE_IMPLEMENT,
) -> Context:
    """
    Factory function to create a properly initialized Context object.

    Args:
        operation_type: The type of operation being performed
        phase: The execution phase (Development, Testing, Production)
        scf_phase: The current SCF phase

    Returns:
        Initialized Context object
    """
    context = Context(operation_type=operation_type, phase=phase, scf_phase=scf_phase)

    logging.info(
        f"Context initialized: {operation_type or 'Operation'} at {context.timestamp}"
    )
    return context


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Create a context for an analysis operation
    ctx = create_context(operation_type=OperationType.ANALYSIS)

    try:
        # Simulate work with checkpoints
        ctx.log_checkpoint("Initialization", "Setting up analysis parameters")
        # ... work happens here ...
        ctx.log_checkpoint("Data Loading", "Loading historical data")
        # ... more work ...

        # Simulating an error
        # Uncomment to test error handling:
        # raise ValueError("Data validation failed")

        ctx.log_checkpoint("Analysis Complete", "Successfully processed all data")

    except Exception as e:
        ctx.set_error(str(e))

    # Output results
    print(f"Operation completed with status: {'ERROR' if ctx.has_error else 'SUCCESS'}")
    print(f"Checkpoints logged: {len(ctx.results.get('checkpoints', []))}")

    # Example of logging to a file
    log_path = Path(__file__).parent / "aar_actions.log"
    ctx.log_to_file(log_path)
    print(f"Context logged to: {log_path}")
