#!/usr/bin/env python3
"""
AAR Auto-Update Protocol - Enhanced Dependency Analysis
Task #4 Final Enhancement: Intelligent dependency resolution and blocking detection

This module provides enhanced dependency analysis with cycle detection,
critical path identification, and intelligent task prioritization.
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict, deque
import json
from pathlib import Path

from task_parser import Task, TaskStatus, Priority


@dataclass
class DependencyGraph:
    """Enhanced dependency graph with cycle detection and critical path analysis"""

    nodes: Dict[str, Task]
    edges: Dict[str, List[str]]  # task_id -> [dependent_task_ids]
    reverse_edges: Dict[str, List[str]]  # task_id -> [prerequisite_task_ids]
    cycles: List[List[str]]
    critical_path: List[str]
    blocked_tasks: List[str]
    ready_tasks: List[str]

    @classmethod
    def from_tasks(cls, tasks: List[Task]) -> 'DependencyGraph':
        """Build enhanced dependency graph from task list"""

        nodes = {f"#{task.id.strip('#')}" if task.id.startswith('#') else f"#{task.id}": task for task in tasks}
        edges = defaultdict(list)
        reverse_edges = defaultdict(list)

        # Build dependency relationships
        for task in tasks:
            task_id = f"#{task.id.strip('#')}" if task.id.startswith('#') else f"#{task.id}"

            # Parse dependencies - look for references to other tasks
            for dep in task.dependencies:
                dep_clean = dep.strip().lower()

                # Smart dependency detection
                if "task" in dep_clean:
                    # Extract task numbers: "Task #1", "task 1", etc.
                    import re
                    task_refs = re.findall(r'task\s*#?(\d+)', dep_clean)
                    for ref in task_refs:
                        prereq_id = f"#{ref}"
                        if prereq_id in nodes:
                            edges[prereq_id].append(task_id)
                            reverse_edges[task_id].append(prereq_id)

                # Look for functional dependencies
                elif any(keyword in dep_clean for keyword in ['testing', 'pipeline', 'completion']):
                    # Task depends on Task #1 (Testing Pipeline)
                    if "#1" in nodes and task_id != "#1":
                        edges["#1"].append(task_id)
                        reverse_edges[task_id].append("#1")

                elif any(keyword in dep_clean for keyword in ['aar', 'automation', 'tracking']):
                    # Task depends on Task #4 (AAR Automation)
                    if "#4" in nodes and task_id != "#4":
                        edges["#4"].append(task_id)
                        reverse_edges[task_id].append("#4")

        # Detect cycles
        cycles = cls._detect_cycles(dict(edges))

        # Find critical path (longest path through completed/in-progress tasks)
        critical_path = cls._find_critical_path(nodes, dict(edges))

        # Identify blocked and ready tasks
        blocked_tasks = []
        ready_tasks = []

        for task_id, task in nodes.items():
            if task.status == TaskStatus.COMPLETED:
                continue

            # Check if prerequisites are met
            prereqs = reverse_edges.get(task_id, [])
            if prereqs:
                prereq_completed = all(
                    nodes[prereq].status == TaskStatus.COMPLETED
                    for prereq in prereqs if prereq in nodes
                )
                if not prereq_completed:
                    blocked_tasks.append(task_id)
                else:
                    ready_tasks.append(task_id)
            else:
                ready_tasks.append(task_id)

        return cls(
            nodes=nodes,
            edges=dict(edges),
            reverse_edges=dict(reverse_edges),
            cycles=cycles,
            critical_path=critical_path,
            blocked_tasks=blocked_tasks,
            ready_tasks=ready_tasks
        )

    @staticmethod
    def _detect_cycles(edges: Dict[str, List[str]]) -> List[List[str]]:
        """Detect cycles in dependency graph using DFS"""

        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: List[str]) -> bool:
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return True

            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)

            for neighbor in edges.get(node, []):
                if dfs(neighbor, path + [node]):
                    return True

            rec_stack.remove(node)
            return False

        for node in edges:
            if node not in visited:
                dfs(node, [])

        return cycles

    @staticmethod
    def _find_critical_path(nodes: Dict[str, Task], edges: Dict[str, List[str]]) -> List[str]:
        """Find critical path using topological sort and longest path"""

        # Calculate longest path (critical path)
        in_degree = defaultdict(int)
        for node in edges:
            for neighbor in edges[node]:
                in_degree[neighbor] += 1

        # Initialize queue with nodes having no prerequisites
        queue = deque([node for node in nodes if in_degree[node] == 0])
        longest_path = {}
        critical_path = []

        while queue:
            current = queue.popleft()
            current_distance = longest_path.get(current, 0)

            for neighbor in edges.get(current, []):
                neighbor_distance = longest_path.get(neighbor, 0)
                task_weight = nodes[current].estimated_hours if current in nodes else 1

                if current_distance + task_weight > neighbor_distance:
                    longest_path[neighbor] = current_distance + task_weight

                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Build critical path
        if longest_path:
            # Find the task with maximum distance
            max_node = max(longest_path.items(), key=lambda x: x[1])
            critical_path = [max_node[0]]

            # Trace back the path
            current = max_node[0]
            current_distance = max_node[1]

            while current_distance > 0:
                for node in nodes:
                    if node != current and current in edges.get(node, []):
                        node_distance = longest_path.get(node, 0)
                        node_weight = nodes[node].estimated_hours if node in nodes else 1

                        if abs(node_distance + node_weight - current_distance) < 0.1:
                            critical_path.insert(0, node)
                            current = node
                            current_distance = node_distance
                            break
                else:
                    break

        return critical_path

    def get_analysis_summary(self) -> Dict:
        """Get comprehensive dependency analysis summary"""

        total_tasks = len(self.nodes)
        completed_tasks = sum(1 for task in self.nodes.values() if task.status == TaskStatus.COMPLETED)
        blocked_count = len(self.blocked_tasks)
        ready_count = len(self.ready_tasks)

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "blocked_tasks": blocked_count,
            "ready_tasks": ready_count,
            "cycles_detected": len(self.cycles),
            "critical_path_length": len(self.critical_path),
            "completion_percentage": round((completed_tasks / total_tasks) * 100, 1) if total_tasks > 0 else 0,
            "efficiency_score": round(((ready_count - blocked_count) / total_tasks) * 100, 1) if total_tasks > 0 else 0,
            "critical_path": self.critical_path,
            "next_recommended_tasks": self.ready_tasks[:3],  # Top 3 ready tasks
            "blocking_issues": [
                f"Task {task_id} blocked by incomplete prerequisites"
                for task_id in self.blocked_tasks
            ]
        }


class DependencyAnalyzer:
    """Enhanced dependency analyzer with cycle detection and critical path analysis"""

    def analyze_dependencies(self, tasks: List[Task]) -> DependencyGraph:
        """Perform comprehensive dependency analysis"""
        return DependencyGraph.from_tasks(tasks)

    def find_critical_path(self, dependency_graph: DependencyGraph) -> List[str]:
        """Find the critical path through the dependency graph"""
        return dependency_graph.critical_path

    def get_blocked_tasks(self, dependency_graph: DependencyGraph) -> List[str]:
        """Get tasks that are currently blocked by dependencies"""
        return dependency_graph.blocked_tasks

    def get_ready_tasks(self, dependency_graph: DependencyGraph) -> List[str]:
        """Get tasks that are ready to be worked on"""
        return dependency_graph.ready_tasks


def enhance_task_analysis(tasks: List[Task]) -> Tuple[List[Task], Dict]:
    """Enhanced task analysis with dependency resolution"""

    # Build dependency graph
    dep_graph = DependencyGraph.from_tasks(tasks)

    # Get analysis summary
    analysis = dep_graph.get_analysis_summary()

    # Add enhanced metadata to tasks
    enhanced_tasks = []
    for task in tasks:
        task_id = f"#{task.id.strip('#')}" if task.id.startswith('#') else f"#{task.id}"

        # Add dependency metadata
        task.blocks = dep_graph.edges.get(task_id, [])

        # Add analysis insights
        if task_id in dep_graph.critical_path:
            task.complexity_indicators.append("critical_path")
        if task_id in dep_graph.blocked_tasks:
            task.risk_factors.append("blocked_by_dependencies")
        if task_id in dep_graph.ready_tasks:
            task.success_patterns.append("ready_for_execution")

        enhanced_tasks.append(task)

    return enhanced_tasks, analysis


if __name__ == "__main__":
    # Test the dependency analysis
    from task_parser import TaskParser
    from pathlib import Path

    parser = TaskParser(Path("."))
    tasks = parser.parse_tasks()
    enhanced_tasks, analysis = enhance_task_analysis(tasks)

    print("=== ENHANCED DEPENDENCY ANALYSIS ===")
    print(json.dumps(analysis, indent=2))
